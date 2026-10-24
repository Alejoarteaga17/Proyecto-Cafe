# Desarrollo con Docker

El flujo de desarrollo se ejecuta dentro del contenedor `CoffeeCultivation`.
Esto evita depender de instalaciones locales de Python, Node.js, AWS CLI o
Serverless Framework.

## Requisitos

- Docker Desktop.
- Visual Studio Code con `ms-vscode-remote.remote-containers` (opcional).
- Credenciales AWS autorizadas solo para la cuenta y ambiente objetivo.

## Inicio

Desde la raíz del repositorio:

```bash
docker compose -f .docker/docker-compose.yml build
docker compose -f .docker/docker-compose.yml up -d
docker exec -it CoffeeCultivation bash
```

Antes de iniciar el contenedor, crea el archivo local de credenciales a partir
del ejemplo:

```bash
cp .envs/aws.env.example .envs/aws.env
cp .envs/sls.env.example .envs/sls.env
```

Edita `.envs/aws.env` y reemplaza los valores de ejemplo por tus credenciales
AWS. Este archivo está excluido de Git y Docker Compose lo inyecta como
variables de entorno; no lo compartas ni lo confirmes en el repositorio.

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
2. `/app/batch/infrastructure/serverless/iot`
3. `/app/batch/infrastructure/serverless/data-platform`
4. `/app/batch/serverless`

Validar cada stack antes de desplegar:

```bash
serverless print --stage dev
```

Publicar los scripts Glue antes del stack `data-platform`:

```powershell
pwsh /app/batch/glue/publish-scripts.ps1 `
  -BucketName <data-lake-bucket> -Region us-east-1
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
