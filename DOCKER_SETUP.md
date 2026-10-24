# Desarrollo con Docker

El flujo de desarrollo se ejecuta dentro del contenedor `CoffeeCultivation`.
Esto evita depender de instalaciones locales de Python, Node.js, AWS CLI o
Serverless Framework.

## Requisitos

- Docker Desktop.
- Visual Studio Code con `ms-vscode-remote.remote-containers` (opcional).
- Credenciales AWS autorizadas solo para la cuenta y ambiente objetivo.

## Inicio

Antes de iniciar el contenedor, crea el archivo local de credenciales a partir
del ejemplo:

```bash
cp .envs/aws.env.example .envs/aws.env
cp .envs/sls.env.example .envs/sls.env
```

Edita `.envs/aws.env` y reemplaza los valores de ejemplo por tus credenciales
AWS. Este archivo está excluido de Git y Docker Compose lo inyecta como
variables de entorno; no lo compartas ni lo confirmes en el repositorio.

Edita `.envs/sls.env` y reemplaza su valor de ejemplo si usarás funciones del
Serverless Dashboard. Para validar o desplegar con AWS, `aws.env` es el archivo
importante.

Desde la raíz del repositorio, levanta Docker:

```bash
docker compose -f .docker/docker-compose.yml up -d --build --force-recreate
docker exec -it CoffeeCultivation bash
```

Si el contenedor ya estaba creado, recréalo para cargar cambios:

```bash
docker compose -f .docker/docker-compose.yml up -d --force-recreate
```

Dentro del contenedor, ejecutar las pruebas:

```bash
cd /app/batch
python -m pytest -q
```

Comprueba que AWS CLI recibió las variables sin imprimir secretos:

```bash
aws configure list
```

El campo `access_key` debe indicar `env` y la región debe ser `us-east-1`.

## Validación y despliegue

La arquitectura aprobada usa únicamente estos stacks:

1. `/app/batch/infrastructure/serverless/storage`
2. `/app/batch/infrastructure/serverless/data-platform`
3. `/app/batch/serverless`
4. `/app/streaming/infrastructure/serverless/iot`

Validar cada stack antes de desplegar:

```bash
serverless print --stage dev
```

Publicar los scripts Glue antes del stack `data-platform`:

```powershell
pwsh /app/batch/glue/publish-scripts.ps1 `
  -BucketName <data-lake-bucket> -Region us-east-1
```

El stack IoT se valida desde:

```bash
cd /app/streaming/infrastructure/serverless/iot
serverless print --stage dev
```

El despliegue AWS requiere autorización explícita y credenciales configuradas.
`serverless print` solo valida la resolución local de la configuración; no
demuestra que un recurso esté desplegado.

## Convenciones

- Región por defecto: `us-east-1`.
- Stages permitidos: `dev`, `test`, `prod`.
- No crear ni desplegar MongoDB, SQS, DLQ, SNS, Secrets Manager ni una base
  operativa separada: esos componentes fueron retirados del repositorio y
  están fuera de la arquitectura aprobada.
