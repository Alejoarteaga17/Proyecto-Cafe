# README

## Resumen

`infrastructure` contiene stacks compartidos de AWS del proyecto de café:
data lake S3, colas SQS con DLQ, secretos, IoT Core y alertas operativas.
Los stacks SQS, secretos e IoT pertenecen a flujos existentes y no deben
confundirse con el nuevo batch medallion.

El bucket compartido de S3 funciona como data lake para los flujos históricos y streaming. Sus zonas lógicas son:

```text
bronze/  # datos recibidos, sin transformación
silver/  # datos validados, limpios y particionados
gold/    # datos agregados para analítica
```

Las zonas son prefijos dentro del mismo bucket para conservar un único punto de administración, cifrado, versionado y control de acceso. El stack no crea tres buckets distintos porque la separación lógica permite compartir políticas y facilita el gobierno del lago sin duplicar infraestructura.

El batch nuevo no utiliza MongoDB. Los componentes de MongoDB que aún aparecen
en otros módulos pertenecen al flujo legado o streaming y se retirarán cuando
ese flujo tenga su propia persistencia en S3.

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
2. El stack batch (`../../serverless`)
3. `serverless/queue`, `serverless/secrets` e `serverless/iot` solo si el flujo
   legado/streaming los requiere
4. `serverless/alerts`

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
