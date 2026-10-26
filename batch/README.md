# README

## Resumen

`batch` contiene el pipeline de ingestión histórica del proyecto de café: carga mediante API, transformación con AWS Glue, particionado y almacenamiento analítico en el data lake S3.

La IaC está separada en stacks bajo `serverless/` e `infrastructure/serverless/`.
Actualmente están implementados el stack de almacenamiento S3 y el servicio de
carga de URL prefirmada. Los scripts Glue existen, pero sus Jobs, catálogo y
orquestación aún deben provisionarse antes de declarar completo el pipeline.

## Arquitectura del pipeline

```text
Cliente -> API Gateway -> Lambda de carga -> URL prefirmada -> S3 Bronze
                                                        |
                                           Step Functions + Glue
                                                        |
                                              S3 Silver -> S3 Gold
                                                        |
                                      Glue Data Catalog -> Athena
```

La API entrega una URL prefirmada de corta duración. La aplicación cliente sube el archivo directamente a S3 usando `PUT`, por lo que el archivo no atraviesa los límites de payload de API Gateway ni la memoria de la Lambda. La URL no restringe el formato por sí misma; el pipeline histórico acepta inicialmente CSV y valida la extensión y el `Content-Type` declarado. JSON, JSONL o Parquet pueden agregarse después mediante lectores específicos en los Glue Jobs.

La estructura propuesta es:

```text
bronze/historical/YYYY/MM/DD/<uuid>.csv
silver/historical/year=YYYY/month=MM/location=<location>/
gold/historical/
```

Silver se particiona por año, mes y ubicación porque son dimensiones de consulta frecuentes y de cardinalidad controlada: Athena puede leer solo los meses y fincas solicitados, reduciendo lecturas y costo. Gold no se particiona inicialmente porque sus agregados serán mucho más pequeños; se revisará con datos reales antes de añadir particiones.

MongoDB no forma parte del pipeline batch nuevo. S3 conserva las capas Bronze, Silver y Gold; el mismo data lake puede recibir posteriormente los eventos del flujo streaming bajo sus propios prefijos.

## Configuración

### Contenedor de desarrollo

1. Instala la extensión `ms-vscode-remote.remote-containers`.
2. Abre la carpeta del repositorio en VS Code y confirma la apertura dentro del contenedor.

### Variables de entorno

Crea los archivos en `.envs` con los valores requeridos por AWS, Serverless y el entorno del proyecto.

### Dependencias

El despliegue requiere AWS CLI, Serverless Framework v4 y un perfil AWS con permisos para CloudFormation, S3, Lambda, API Gateway, Step Functions, Glue, Athena, IAM y CloudWatch Logs. Las credenciales se configuran fuera del repositorio; no deben copiarse al código.

### Despliegue

Se usa Serverless Framework y cada stack vive dentro de `serverless/` y `infrastructure/serverless/` del mismo flujo.

Orden recomendado:

1. `infrastructure/serverless/storage`
2. `serverless`
3. Jobs Glue y sus scripts publicados en S3
4. Step Functions y evento de entrada
5. Glue Data Catalog
6. Athena

Para validar solo lo implementado actualmente, ejecuta los pasos 1 y 2 y
comprueba que el CSV aparezca en `bronze/uploads/`.

### Despliegue en PowerShell

Usa un perfil de AWS IAM Identity Center ya configurado y no guardes
credenciales en el repositorio:

```powershell
$env:AWS_PROFILE = "coffee-dev"
$env:AWS_DEFAULT_REGION = "us-east-1"
$env:DEPLOY_APP = "coffee-cultivation"
$env:DEVELOPER = "alejandra-suarez"

aws sso login --profile coffee-dev
aws sts get-caller-identity --profile coffee-dev
```

Empaqueta y despliega el almacenamiento:

```powershell
cd batch/infrastructure/serverless/storage
npx.cmd serverless package --stage dev --aws-profile coffee-dev
npx.cmd serverless deploy --stage dev --aws-profile coffee-dev
```

Obtén el bucket y despliega la API:

```powershell
$bucket = aws ssm get-parameter `
  --name "/coffee-cultivation-storage/RawReportsBucketName" `
  --query "Parameter.Value" --output text

cd ../../../serverless
npx.cmd serverless package --stage dev --aws-profile coffee-dev
npx.cmd serverless deploy --stage dev --aws-profile coffee-dev
npx.cmd serverless info --stage dev --aws-profile coffee-dev
```

Solicita una URL prefirmada al endpoint mostrado por `serverless info` y sube
el CSV con `PUT` y `Content-Type: text/csv`. Después comprueba Bronze:

```powershell
aws s3 ls "s3://$bucket/bronze/uploads/" --recursive
```

La ejecución completa no puede declararse validada hasta que existan recursos
`AWS::Glue::Job`, `AWS::StepFunctions::StateMachine`,
`AWS::Events::Rule`, `AWS::Glue::Database` y `AWS::Athena::WorkGroup` en la
plantilla empaquetada. Compruébalo antes de desplegar la siguiente fase:

```powershell
Get-Content .serverless/cloudformation-template-update-stack.json |
  Select-String "AWS::Glue|AWS::StepFunctions|AWS::Events|AWS::Athena"
```

### Eliminación

Usa `serverless remove` en el orden inverso al despliegue para evitar dependencias de infraestructura.

---

## Glosario

### AWS environment variables: `../.envs/aws.env`

- `AWS_ACCESS_KEY_ID`: clave de acceso para despliegues AWS.
- `AWS_SECRET_ACCESS_KEY`: clave secreta asociada.
- `AWS_DEFAULT_REGION`: región del despliegue.
- `AWS_DEFAULT_OUTPUT`: formato por defecto del CLI de AWS.

### Serverless Framework environment variables: `../.envs/sls.env`

- `SERVERLESS_ACCESS_KEY`: clave de Serverless Framework para despliegues.

### Service environment variables: `.envs/config.env`

- `DEVELOPER`: identificador del desarrollador para nombres únicos de recursos.

### Variables de despliegue Serverless

- `stage`: entorno de despliegue (`dev`, `test` o `prod`).
