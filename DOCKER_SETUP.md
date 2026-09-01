# Docker Setup Guide - Cultivo de Café Inteligente

Esta guía explica cómo configurar el entorno Dockerizado para trabajar en el proyecto de **Cultivo de Café Inteligente**.

## Requisitos previos

1. **Docker Desktop** instalado y ejecutándose
2. **Visual Studio Code** con la extensión `ms-vscode-remote.remote-containers`
3. **Credenciales de AWS** con permisos para crear recursos en la cuenta destino

## Estructura de contenedores

El proyecto usa un contenedor raíz para la capa de tooling del repositorio y, desde ahí, se ejecutan los comandos de cada flujo (`batch` y `streaming`) dentro del mismo entorno Docker.

| Contenedor                        | Propósito                                             | Directorio                       |
| --------------------------------- | ----------------------------------------------------- | -------------------------------- |
| `CoffeeCultivation`               | Tooling del monorepo y diagramas de arquitectura      | `.docker/`                       |
| `CoffeeCultivationBatch`          | Pipeline batch y su infraestructura asociada           | `/app/batch`                     |
| `CoffeeCultivationStreaming`      | Pipeline streaming y su infraestructura asociada       | `/app/streaming`                 |

## Configuración inicial

### 1. Configurar variables de entorno

#### Paso 1a: AWS credentials (`.envs/aws.env`)

Copia desde el ejemplo y completa:

```bash
cp .envs/aws.env.example .envs/aws.env
```

Edita `.envs/aws.env` con tus credenciales:

```bash
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1
AWS_DEFAULT_OUTPUT=json
```

#### Paso 1b: Serverless Framework (`.envs/sls.env`)

Copia desde el ejemplo:

```bash
cp .envs/sls.env.example .envs/sls.env
```

Si usas Serverless Dashboard, completa la clave:

```bash
SERVERLESS_ACCESS_KEY=your-key-here
```

#### Paso 1c: Batch config (`batch/.envs/config.env`)

Copia desde el ejemplo:

```bash
cp batch/.envs/config.env.example batch/.envs/config.env
```

Completa con tu identificador de desarrollador:

```bash
DEVELOPER=your-name
STAGE=dev
```

#### Paso 1d: Streaming config (`streaming/.envs/config.env`)

Copia desde el ejemplo:

```bash
cp streaming/.envs/config.env.example streaming/.envs/config.env
```

Completa con credenciales de MongoDB Atlas y tu email de alertas:

```bash
DEVELOPER=your-name
STAGE=dev
MONGO_HOST=cluster0.xxxxx.mongodb.net
MONGO_USERNAME=coffee_user
MONGO_PASSWORD=secure-password
MONGO_DBNAME=coffee_cultivation
ALERTS_EMAIL=team@example.com
```

### 2. Abrir en contenedores

#### Opción A: Usar VS Code Remote Containers

1. Abre la carpeta raíz del proyecto en VS Code
2. Presiona `Cmd/Ctrl + Shift + P`
3. Escribe `Remote-Containers: Reopen in Container`
4. El editor se reconectará dentro del contenedor `CoffeeCultivation`

#### Opción B: Abrir específicamente batch o streaming

Para trabajar solo en batch:

```bash
# En VS Code
1. Abre la carpeta batch en el explorador del proyecto
2. Cmd/Ctrl + Shift + P → Remote-Containers: Reopen Folder in Container
```

Para streaming:

```bash
# En VS Code
1. Abre la carpeta streaming en el explorador del proyecto
2. Cmd/Ctrl + Shift + P → Remote-Containers: Reopen Folder in Container
```

### 3. Verificar la conexión

Una vez dentro del contenedor, verifica:

```bash
# Verificar AWS
aws iam list-account-aliases

# Verificar Serverless
serverless --version

# Verificar Python
python3 --version

# Verificar Node.js
node --version
```

## Trabajar con Docker desde la línea de comandos

Si prefieres no usar VS Code Remote Containers, puedes ejecutar comandos directamente en los contenedores:

### Batch

```bash
# Instalar dependencias del flujo batch
docker exec -w /app/batch CoffeeCultivation npm install

# Validar sintaxis Python
docker exec -w /app/batch CoffeeCultivation python3 -m compileall src/

# Ejecutar linter del stack batch
docker exec -w /app/batch CoffeeCultivation cfn-lint serverless/serverless.yml

# Verificar Serverless dentro del contenedor
docker exec CoffeeCultivation sh -lc 'serverless --version'

# Ver logs de CloudWatch
docker exec CoffeeCultivation aws logs tail /aws/lambda/coffee-cultivation-batch-ValidateAndStore --follow
```

### Streaming

```bash
# Validar CloudFormation del flujo streaming
docker exec -w /app/streaming CoffeeCultivation cfn-lint serverless/serverless.yml

# Desplegar la infraestructura del flujo streaming
docker exec -w /app/streaming/infrastructure/serverless/storage CoffeeCultivation serverless deploy --stage dev

# Ver parámetros SSM
docker exec CoffeeCultivation aws ssm describe-parameters --filters Key=Name,Values=coffee-cultivation-streaming-queue
```

### Flujo de despliegue recomendado

Los archivos `.env` no se cargan automáticamente por ejecutar `serverless` desde una carpeta. El contenedor raíz inyecta las variables mediante `env_file` al arrancar el entorno. Por eso, ejecuta los comandos con `docker exec` desde la raíz del proyecto o desde la carpeta del flujo correspondiente.

La reactivación del entorno debe hacerse en este orden exacto. No son pasos intercambiables:

```bash
# 0) Iniciar el contenedor raíz
docker compose -f .docker/docker-compose.yml up -d

# 1) Infraestructura base del batch
docker exec -w /app/batch/infrastructure/serverless/storage CoffeeCultivation serverless deploy --stage dev
docker exec -w /app/batch/infrastructure/serverless/queue CoffeeCultivation serverless deploy --stage dev
docker exec -w /app/batch/infrastructure/serverless/secrets CoffeeCultivation serverless deploy --stage dev
docker exec -w /app/batch/infrastructure/serverless/iot CoffeeCultivation serverless deploy --stage dev

# 2) Infraestructura base del streaming
docker exec -w /app/streaming/infrastructure/serverless/storage CoffeeCultivation serverless deploy --stage dev
docker exec -w /app/streaming/infrastructure/serverless/queue CoffeeCultivation serverless deploy --stage dev
docker exec -w /app/streaming/infrastructure/serverless/secrets CoffeeCultivation serverless deploy --stage dev
docker exec -w /app/streaming/infrastructure/serverless/iot CoffeeCultivation serverless deploy --stage dev

# 3) Despliegue del flujo batch
docker exec -w /app/batch/serverless CoffeeCultivation serverless deploy --stage dev

# 4) Despliegue del flujo streaming
docker exec -w /app/streaming/serverless CoffeeCultivation serverless deploy --stage dev
```

Si quieres reactivar solo los pipelines del proyecto, este es el orden correcto y suficiente:

```bash
# Batch
docker exec -w /app/batch/infrastructure/serverless/storage CoffeeCultivation serverless deploy --stage dev
docker exec -w /app/batch/infrastructure/serverless/queue CoffeeCultivation serverless deploy --stage dev
docker exec -w /app/batch/infrastructure/serverless/secrets CoffeeCultivation serverless deploy --stage dev
docker exec -w /app/batch/infrastructure/serverless/iot CoffeeCultivation serverless deploy --stage dev
docker exec -w /app/batch/serverless CoffeeCultivation serverless deploy --stage dev

# Streaming
docker exec -w /app/streaming/infrastructure/serverless/storage CoffeeCultivation serverless deploy --stage dev
docker exec -w /app/streaming/infrastructure/serverless/queue CoffeeCultivation serverless deploy --stage dev
docker exec -w /app/streaming/infrastructure/serverless/secrets CoffeeCultivation serverless deploy --stage dev
docker exec -w /app/streaming/infrastructure/serverless/iot CoffeeCultivation serverless deploy --stage dev
docker exec -w /app/streaming/serverless CoffeeCultivation serverless deploy --stage dev
```

Después de cada despliegue, verifica que terminó con `Service deployed` antes de continuar. Si ejecutas `serverless` directamente dentro de una terminal que no es el contenedor raíz, carga las variables manualmente:

```bash
set -a
. /app/.envs/aws.env
. /app/.envs/sls.env
. /app/batch/.envs/config.env
. /app/streaming/.envs/config.env
set +a
```

Puedes comprobar la dependencia principal del flujo batch antes de desplegar alertas:

```bash
docker exec CoffeeCultivation \
 aws ssm get-parameter \
 --name "/coffee-cultivation-batch/SplitAndEnqueueLambdaName" \
 --query "Parameter.Value" --output text
```

El comando debe devolver el nombre de la Lambda. Si aparece `ParameterNotFound`, repite el despliegue del flujo batch.

### Monorepo (diagramas, etc.)

```bash
# Generar diagramas de arquitectura
docker exec -w /app/docs CoffeeCultivation python3 architecture.py
```

## Iniciar y probar los flujos

Estos pasos se ejecutan después de completar el despliegue recomendado. Usa la
misma región, `stage` y `DEVELOPER` definidos en los archivos `.env`.

### Flujo batch: prueba de aceptación en Postman

El batch inicia con el endpoint privado `POST /coffee-historical-data`. La
petición debe contener un CSV codificado en Base64 dentro de la propiedad
`file`; no se envía como `multipart/form-data`.

1. Obtén la URL del endpoint y la API key desde el contenedor del flujo batch:

```bash
docker exec -w /app/batch/serverless \
 CoffeeCultivation serverless info --stage dev --verbose
```

En la salida, usa el endpoint de `POST /coffee-historical-data` y el valor
de `api keys` como API key. La URL normalmente tiene esta forma:
`https://<api-id>.execute-api.us-east-1.amazonaws.com/dev/coffee-historical-data`.

1. En Postman crea una petición `POST` con esa URL y configura:

- Header `Content-Type`: `application/json`
- Header `x-api-key`: la API key obtenida en el paso anterior
- Authorization: `AWS Signature`
- AWS Region: `us-east-1`
- Service Name: `execute-api`
- AccessKey y SecretKey: las credenciales AWS del archivo `.envs/aws.env`

La firma AWS es necesaria porque la API es privada. Si el stage usa una
API key gestionada en API Gateway, también puedes consultar su valor con:

```bash
docker exec CoffeeCultivation aws apigateway get-api-keys \
 --include-values --query 'items[?contains(name, `batch`)]' \
 --output table
```

1. En `Body > raw > JSON`, envía un objeto como este. El valor de `file` debe
   ser el Base64 de un CSV, no el contenido del CSV directamente:

```json
{
  "file": "<BASE64_DEL_CSV>"
}
```

Para generar el valor sin saltos de línea, crea un CSV con al menos estas
columnas y una fila válida:

```csv
LON,LAT,YEAR,MM,DD,DOY,Date,Temp_Max,Temp_Min,Humidity,Solar_Radiation,Precipitation_mm,Location,Close_USD_60kg,Is_Weekend,Is_Interpolated,brl,cny,mxn
-75.68,4.53,2026,8,22,234,2026-08-22,25,17,70,500,2,Armenia,180,false,false,5,7,18
```

Guarda el contenido como `accepted.csv` y ejecuta:

```bash
base64 -w 0 accepted.csv
```

Pega la salida entre las comillas de `file` en Postman. El CSV debe tener
como máximo 300 filas y todas las columnas requeridas.

1. Envía la petición. Una aceptación correcta devuelve HTTP `202` y un cuerpo
   similar a:

```json
{
  "message": "Coffee historical dataset accepted",
  "s3_key": "silver/uploads/<uuid>.csv",
  "rows_accepted": 1
}
```

Ese resultado confirma la primera etapa. El evento de S3 dispara
`SplitAndEnqueue`, que publica cada fila en SQS, y luego
`ValidateAndPersist` la almacena en MongoDB. Para revisar el procesamiento:

```bash
docker exec CoffeeCultivation aws logs tail \
 /aws/lambda/${DEPLOY_APP}-batch-ValidateAndPersist --follow
```

El script `batch/tests/batch/send_invalid_row_to_queue.sh` sirve para la
prueba negativa de DLQ; no debe usarse para validar una aceptación.

Si el endpoint devuelve `202` pero `SplitAndEnqueue` no se ejecuta, vuelve a
desplegar el stack batch para actualizar el filtro del evento S3 y después
envía un archivo nuevo desde Postman:

```bash
docker exec -w /app/batch/serverless \
 CoffeeCultivation serverless deploy --stage dev
```

El filtro correcto es `silver/uploads/`, que coincide con la ruta donde
`ValidateAndStore` guarda los archivos. La alerta
`coffee-cultivation-alerts-coffee-batch-dlq-messages-dev` se activa cuando hay
mensajes rechazados en la DLQ; el mensaje enviado por
`send_invalid_row_to_queue.sh` contiene `invalid_field` intencionalmente y
activa esa alarma como prueba negativa. Después de revisarlo, elimina ese
mensaje desde la consola SQS o espera su retención antes de repetir una
prueba limpia.

### Flujo streaming: iniciar una lectura de sensor

El streaming no usa HTTP. Un sensor publica por MQTT sobre TLS mutuo en el
tópico `sensors/coffee/<sensor-id>/data`; IoT Core redirige la lectura a SQS y
`PersistSensorReading` la valida y la guarda en MongoDB.

1. Verifica que los stacks `iot` y `streaming/serverless` terminaron con
   `Service deployed`.
2. En el contenedor del flujo streaming, provisiona un sensor de prueba. Esto crea el
   Thing, el certificado y sus claves locales:

```bash
docker exec -w /app/streaming/tests/sensor_readings \
 CoffeeCultivation ./provision_sensor.sh sensor-001
```

1. Publica una lectura válida usando el certificado mTLS:

```bash
docker exec -w /app/streaming/tests/sensor_readings \
 CoffeeCultivation ./send_sensor_reading.sh sensor-001
```

El payload por defecto es
`streaming/tests/fixtures/sensor_readings/valid_reading.json`. Para probar
una lectura concreta, pasa su archivo como segundo argumento:

```bash
docker exec -w /app/streaming/tests/sensor_readings \
 CoffeeCultivation ./send_sensor_reading.sh sensor-001 \
 ../fixtures/sensor_readings/valid_reading.json
```

1. Revisa los logs de la Lambda para confirmar la persistencia:

```bash
docker exec CoffeeCultivation aws logs tail \
 /aws/lambda/${DEPLOY_APP}-streaming-PersistSensorReading --follow
```

Para una prueba negativa, usa `invalid_location.json` o
`invalid_temperature.json`; la lectura debe terminar en la DLQ de
`SensorReadings` y no en la colección principal.

## Troubleshooting

### El contenedor no inicia

```bash
# Reconstruir la imagen Docker
docker-compose -f .docker/docker-compose.yml build --no-cache

# Luego reintentar
docker-compose -f .docker/docker-compose.yml up -d
```

### Permisos denegados en Serverless o nodemodules

Si `serverless deploy` falla con un error como `EACCES: permission denied, mkdir '/usr/local/lib/node_modules/serverless/node_modules/.bin'`, corrige el propietario del directorio dentro del contenedor:

```bash
# Ejecuta esto desde la máquina host
# (no dentro del contenedor, porque no tiene acceso a 'docker' como comando)
docker exec -u root CoffeeCultivation sh -lc 'chown -R aaccode:aaccode /usr/local/lib/node_modules && chmod -R u+rwX /usr/local/lib/node_modules/serverless'

# Verifica que ya funciona
docker exec CoffeeCultivation sh -lc 'serverless --version'
```

Si ves errores al instalar layers:

```bash
# Ejecuta dentro del contenedor como sudo
docker exec -u root CoffeeCultivation chown -R coffee-cultivation /usr/local/lib/python3.13/site-packages/
```

### Error de SSM no resuelto en `custom.sqs.*`

Si aparece un mensaje como:

```text
Cannot resolve '${ssm:/coffee-cultivation-queue/CoffeeBatchQueueUrl}' variable at 'custom.sqs.coffeeBatch.url'
```

significa que la infraestructura aún no fue desplegada. Revisa primero los stacks de `infrastructure/serverless` y luego vuelve a ejecutar el deploy del `batch`.

```bash
docker exec CoffeeCultivation aws ssm get-parameter --name "/coffee-cultivation-queue/CoffeeBatchQueueUrl" --query "Parameter.Value" --output text
```

Si el comando devuelve una URL, entonces el parámetro SSM ya existe y el deploy del batch puede continuar.

### Credenciales ausentes o expiradas

Actualiza `.envs/aws.env` y recrea los contenedores. `docker restart` no vuelve
a leer los archivos `env_file`, por lo que no corrige variables añadidas o
modificadas después de crear el contenedor:

```bash
# Ejecuta desde la raíz del repositorio, fuera del contenedor
docker compose -f infrastructure/.docker/docker-compose.yml up -d --force-recreate
docker compose -f backend/.docker/docker-compose.yml up -d --force-recreate
```

Comprueba que las credenciales quedaron disponibles sin imprimir sus valores:

```bash
docker exec CoffeeCultivation aws sts get-caller-identity
```

Si devuelve la identidad de la cuenta AWS, repite el despliegue del batch:

```bash
docker exec -w /app/batch/serverless \
 CoffeeCultivation serverless deploy --stage dev
```

### MongoDB Atlas no disponible

Verifica que:

1. El cluster MongoDB Atlas esté ejecutándose
2. Tu IP esté en la lista blanca (Network Access)
3. Las credenciales en `infrastructure/.envs/config.env` sean correctas

## Ciclo de desarrollo típico

### 1. Escribir código

Edita archivos normalmente en tu IDE local; los cambios se reflejan en el contenedor automáticamente.

### 2. Validar

```bash
docker exec -w /app/batch CoffeeCultivation python3 -m compileall src/
docker exec -w /app/streaming CoffeeCultivation cfn-lint serverless/**/*.yml
```

### 3. Probar localmente

```bash
# Seed de base de datos (solo dev/test)
docker exec -w /app/batch CoffeeCultivation ./database/seeders/seed.sh --historical-data 100 --sensor-readings 500

# Ver migraciones
docker exec -w /app/streaming CoffeeCultivation python3 -m database.demo_indexes
```

### 4. Desplegar

```bash
# Infrastructure base (primero, porque batch y streaming dependen de estos parámetros SSM)
docker exec -w /app/infrastructure/serverless/storage CoffeeCultivationInfrastructure serverless deploy --stage dev
docker exec -w /app/infrastructure/serverless/queue CoffeeCultivationInfrastructure serverless deploy --stage dev
docker exec -w /app/infrastructure/serverless/secrets CoffeeCultivationInfrastructure serverless deploy --stage dev
docker exec -w /app/infrastructure/serverless/iot CoffeeCultivationInfrastructure serverless deploy --stage dev

# Backend layers (después)
docker exec -w /app/backend/serverless/layers CoffeeCultivationBackend serverless deploy --stage dev

# Batch
docker exec -w /app/backend/serverless/batch CoffeeCultivationBackend serverless deploy --stage dev

# Alerts (después de batch, porque consume sus parámetros SSM)
docker exec -w /app/infrastructure/serverless/alerts CoffeeCultivationInfrastructure serverless deploy --stage dev

# Streaming
docker exec -w /app/backend/serverless/streaming CoffeeCultivationBackend serverless deploy --stage dev
```

## Limpieza

Para eliminar contenedores sin perder cambios de código:

```bash
# Detener contenedores
docker-compose -f .docker/docker-compose.yml down

# Eliminar volúmenes de historial (opcional)
docker volume rm coffee-cultivation-bashhistory
docker volume rm coffee-cultivation-backend-bashhistory
docker volume rm coffee-cultivation-infrastructure-bashhistory
```

Para limpiar completamente:

```bash
docker system prune --volumes
```

## Variables de referencia rápida

| Variable                        | Ubicación                                                     | Propósito                                                      |
| ------------------------------- | ------------------------------------------------------------- | -------------------------------------------------------------- |
| `AWS_ACCESS_KEY_ID`             | `.envs/aws.env`                                               | Autenticación AWS                                              |
| `DEVELOPER`                     | `backend/.envs/config.env`, `infrastructure/.envs/config.env` | Namespacing de recursos                                        |
| `DEPLOY_APP`                    | Establecida automáticamente por docker-compose                | Nombre de la aplicación en recursos AWS (`coffee-cultivation`) |
| `MONGO_CREDENTIALS_SECRET_NAME` | Establecida por Lambda handlers                               | Ruta SSM de MongoDB credentials                                |

---

**Última actualización**: 2026-08-30  
**Proyecto**: Cultivo de Café Inteligente  
**Arquitectura**: Serverless + MongoDB Atlas + S3 Medallion Lake
