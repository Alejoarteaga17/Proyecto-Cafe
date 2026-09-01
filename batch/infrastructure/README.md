# README

## Resumen

`infrastructure` contiene los stacks compartidos de AWS del proyecto de café: almacenamiento S3, colas SQS con DLQ, secretos de MongoDB Atlas, IoT Core y alertas operativas.

La arquitectura actual del proyecto no incluye PostgreSQL/RDS ni ETL hacia un motor relacional; MongoDB Atlas y S3 son la base del diseño activo.

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
