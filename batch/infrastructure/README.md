# README

## Resumen

`infrastructure` contiene los stacks AWS del proyecto de café: almacenamiento S3 medallion, IoT Core, Data Firehose y la plataforma Glue/Step Functions/Data Catalog/Athena.

Los stacks `queue`, `secrets` y `alerts`, además de cualquier referencia MongoDB, son `LEGACY`. No forman parte de la arquitectura aprobada ni deben incluirse en un despliegue nuevo.

La arquitectura aprobada no incluye PostgreSQL/RDS, MongoDB, SQS, DLQ, SNS ni una base operativa separada. S3 es el almacenamiento del data lake y Glue procesa las capas medallion.

## Configuración

### Contenedor de desarrollo

1. Instala la extensión `ms-vscode-remote.remote-containers`.
2. Abre la carpeta del repositorio en VS Code y acepta la vista dentro del contenedor.

### Variables de entorno

Crea los archivos necesarios en `.envs` con las variables de AWS y Serverless antes de desplegar.

### Dependencias

La cuenta de AWS debe tener un usuario con permisos para crear stacks y recursos de infraestructura.

### Despliegue

Cada stack vive dentro de `serverless/<stack>` y se despliega de forma independiente.

Orden recomendado:

1. `serverless/storage`
2. `serverless/queue`
3. `serverless/secrets`
4. `serverless/iot`
5. `serverless/alerts`

### Eliminación

Usa `serverless remove` en orden inverso al despliegue.

---

## Glosario

### AWS environment variables: `../.envs/aws.env`

- `AWS_ACCESS_KEY_ID`: clave de acceso para desplegar recursos AWS.
- `AWS_SECRET_ACCESS_KEY`: clave secreta asociada.
- `AWS_DEFAULT_REGION`: región de despliegue.
- `AWS_DEFAULT_OUTPUT`: formato de salida del CLI de AWS.

### Serverless Framework environment variables: `../.envs/sls.env`

- `SERVERLESS_ACCESS_KEY`: clave de Serverless Framework para desplegar stacks.

### Service environment variables: `.envs/config.env`

- `DEVELOPER`: identificador del desarrollador para nombres únicos de recursos.
- `MONGO_HOST`, `MONGO_USERNAME`, `MONGO_PASSWORD`, `MONGO_DBNAME`: credenciales de MongoDB Atlas para el secret compartido.
- `ALERTS_EMAIL`: correo del equipo para las alertas de SNS.

### Variables de despliegue Serverless

- `stage`: entorno de despliegue (`dev`, `test` o `prod`).
