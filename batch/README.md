# README

## Resumen

`batch` contiene el pipeline de ingestión histórica del proyecto de café: carga mediante API, transformación con AWS Glue, particionado y almacenamiento analítico en el data lake S3.

El pipeline está desplegado como varios stacks independientes bajo `serverless/` y usa su infraestructura propia dentro de `batch/infrastructure`.

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
4. `serverless`
5. Consultas de Athena de validación

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
