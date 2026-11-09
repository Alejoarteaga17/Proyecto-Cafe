# DataOps y CI/CD

## Alcance

El sprint final automatiza validación, publicación de artefactos Glue,
despliegue de infraestructura y reprocesamiento controlado. Se mantienen los
dos workflows independientes:

- Histórico: `bronze/historical/` -> `silver/historical/` -> `gold/historical/`.
- IoT: `bronze/iot/` -> `silver/iot/` -> `gold/iot/`.

No se agregan colas, consumidores Lambda ni bases operativas.

## Scripts

Desde la raíz del repositorio:

```bash
bash scripts/dataops/validate.sh
bash scripts/dataops/publish-glue.sh dev
```

`publish-glue.sh` obtiene el bucket desde SSM y publica los dos jobs de cada
workflow junto con sus paquetes compartidos. Requiere AWS CLI autenticado,
permisos `ssm:GetParameter` y `s3:PutObject`.

Para un reprocesamiento manual:

```bash
export DATA_LAKE_BUCKET=<bucket>
bash scripts/dataops/start-etl.sh historical dev
bash scripts/dataops/start-etl.sh iot dev bronze/iot/YEAR=2026/MONTH=11/
```

El script obtiene el ARN mediante los exports de CloudFormation y arranca solo
la state machine correspondiente. Requiere `states:StartExecution`,
`cloudformation:ListExports` y, si no se define `DATA_LAKE_BUCKET`,
`ssm:GetParameter`.

## GitHub Actions

- `CI`: ejecuta pruebas, compilación Python, validación HTML y YAML en pushes y
  pull requests.
- `CD - AWS deployment`: workflow manual para `dev`, `test` o `prod`.
- `DataOps - publish and reprocess`: workflow manual para publicar Glue o
  relanzar el workflow `historical` o `iot`.

Configurar en cada GitHub environment:

- Secret `AWS_DEPLOY_ROLE_ARN`, confiado mediante GitHub OIDC.
- Secret `SERVERLESS_ACCESS_KEY`, creado en
  <https://app.serverless.com/settings/accessKeys>. Es necesario porque
  Serverless Framework v4 requiere autenticación en ejecuciones no
  interactivas.
- Variables `AWS_ACCOUNT_ID`, `QUICKSIGHT_DASHBOARD_ID` y
  `QUICKSIGHT_USER_ARN` para la configuración de QuickSight.
- Aprobación obligatoria para `prod`.
- Variable opcional `DATA_LAKE_BUCKET`.

El workflow `CD - AWS deployment` valida esas tres variables y despliega el
stack `data-platform` con `QuickSightEnabled=true`, usando
`QUICKSIGHT_USER_ARN` como `QuickSightPrincipalArn`. Esto crea o actualiza la
fuente Athena y los datasets de QuickSight; el dashboard debe existir o
publicarse separadamente con el contrato de
`docs/quicksight-dashboard-definition.json`.

Los cuatro stacks Serverless usan buckets S3 de artefactos por ambiente
(`us-east-1-cfn-storage-*`, `us-east-1-cfn-data-platform-*`,
`us-east-1-cfn-backend-batch-*` y `us-east-1-cfn-iot-*`). El workflow ejecuta
`scripts/dataops/bootstrap-serverless-buckets.sh` antes de desplegar; el paso
es idempotente y crea, versiona, cifra y bloquea para acceso público los
buckets que falten.

La configuración AWS ya está creada en la cuenta de desarrollo:

- Stack: `coffee-cultivation-github-actions-oidc`
- Región: `us-east-1`
- Estado verificado: `CREATE_COMPLETE`
- Rol: `arn:aws:iam::688060219062:role/coffee-cultivation-github-actions`

El template del rol incluye `ssm:PutParameter`, `ssm:DeleteParameter`,
`ssm:AddTagsToResource` y `ssm:RemoveTagsFromResource` para los parámetros bajo
`coffee-cultivation-*`. CloudFormation necesita también administrar las
etiquetas del parámetro. Si el despliegue falla con
`Access denied for operation 'PutParameter'`, el stack del rol está
desactualizado: modificar el archivo no modifica automáticamente la política
ya desplegada. Actualízalo una vez con credenciales administrativas o con un
rol autorizado a administrar IAM:

```bash
aws cloudformation deploy \
  --region us-east-1 \
  --stack-name coffee-cultivation-github-actions-oidc \
  --template-file infrastructure/github-actions-oidc.yml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    GitHubRepository=Alejoarteaga17/Proyecto-Cafe \
    RoleName=coffee-cultivation-github-actions
```

Confirma que el stack termine en `UPDATE_COMPLETE` y vuelve a ejecutar el
workflow `CD - AWS deployment`. No concedas `ssm:PutParameter` sobre `*`: el
permiso ya está limitado a los parámetros del proyecto. El stack OIDC no se
actualiza automáticamente desde el workflow de aplicación para evitar que un
rol de despliegue modifique su propia relación de confianza o sus permisos.

En GitHub todavía debe registrarse ese ARN como `AWS_DEPLOY_ROLE_ARN` en
`dev`, `test` y `prod`. También debe configurarse la aprobación requerida para
`prod`; esto requiere permisos de administración del repositorio y no puede
realizarse desde AWS CLI.

El rol debe limitarse a los recursos del ambiente. Los workflows no contienen
credenciales AWS y no realizan despliegues automáticamente desde un pull
request. La existencia de los archivos no prueba una ejecución AWS; conservar
los logs y el cambio de CloudFormation como evidencia de cada ejecución.
