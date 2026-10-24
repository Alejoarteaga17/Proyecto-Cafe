# README

## Resumen

`batch` contiene la ingestión histórica y los jobs del data lake del proyecto de café. La ruta aprobada es API Gateway -> Lambda -> S3 Bronze -> Glue -> Silver/Gold.

El pipeline está desplegado como varios stacks independientes bajo `serverless/` y usa su infraestructura propia dentro de `batch/infrastructure`.

## Configuración

### Contenedor de desarrollo

1. Instala la extensión `ms-vscode-remote.remote-containers`.
2. Abre la carpeta del repositorio en VS Code y confirma la apertura dentro del contenedor.

### Variables de entorno

Crea los archivos en `.envs` con los valores requeridos por AWS, Serverless y el entorno del proyecto.

### Dependencias

El usuario de Serverless debe tener permisos IAM adecuados en la cuenta de AWS y sus credenciales deben configurarse desde `.envs/aws.env`.

### Código legacy

`database/`, `src/validate_and_persist`, `src/persist_sensor_reading` y los stacks SQS/MongoDB son `LEGACY`. No son necesarios para el flujo aprobado y no deben desplegarse como parte de una nueva instalación.

### Despliegue

Se usa Serverless Framework y cada stack vive dentro de `serverless/` y `infrastructure/serverless/` del mismo flujo.

Orden recomendado:

1. `infrastructure/serverless/storage`
2. `infrastructure/serverless/iot`
3. Publica los scripts Glue con `glue/publish-scripts.ps1 -BucketName <bucket>`.
4. `infrastructure/serverless/data-platform`
5. `serverless`

Valida primero con `serverless print --stage dev` y despliega solo con autorización explícita.

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
