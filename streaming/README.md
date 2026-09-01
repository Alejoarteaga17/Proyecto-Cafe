# README

## Resumen

`streaming` contiene el pipeline de sensores del proyecto de café: validación agronómica, persistencia en MongoDB y orquestación del flujo en tiempo real.

El pipeline está desplegado como varios stacks independientes bajo `serverless/` y usa su infraestructura propia dentro de `streaming/infrastructure`.

## Configuración

### Contenedor de desarrollo

1. Instala la extensión `ms-vscode-remote.remote-containers`.
2. Abre la carpeta del repositorio en VS Code y confirma la apertura dentro del contenedor.

### Variables de entorno

Crea los archivos en `.envs` con los valores requeridos por AWS, Serverless y el entorno del proyecto.

### Dependencias

El usuario de Serverless debe tener permisos IAM adecuados en la cuenta de AWS y sus credenciales deben configurarse desde `.envs/aws.env`.

### Migraciones de base de datos

Para aplicar migraciones, usa `database/migrations/migrate.sh`.

Si necesitas revertir, añade `--downgrade`.

### Sembrado de datos

Para poblar MongoDB Atlas con datos sintéticos realistas, usa `database/seeders/seed.sh`.

Solo se permite en `dev` y `test`, verificando la etiqueta `STAGE` del secreto `MongoCredentials`.

### Despliegue

Se usa Serverless Framework y cada stack vive dentro de `serverless/` y `infrastructure/serverless/` del mismo flujo.

Orden recomendado:

1. `infrastructure/serverless/storage`
2. `infrastructure/serverless/queue`
3. `infrastructure/serverless/secrets`
4. `infrastructure/serverless/iot`
5. `serverless`
6. Migraciones
7. Seeders opcionales

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
