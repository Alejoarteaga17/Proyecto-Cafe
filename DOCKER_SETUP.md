# Docker Setup Guide - Cultivo de Café Inteligente

Esta guía explica cómo configurar el entorno Dockerizado para trabajar en el proyecto de **Cultivo de Café Inteligente**.

## Requisitos previos

1. **Docker Desktop** instalado y ejecutándose
2. **Visual Studio Code** con la extensión `ms-vscode-remote.remote-containers`
3. **Credenciales de AWS** con permisos para crear recursos en la cuenta destino

## Estructura de contenedores

El proyecto contiene 3 contenedores principales:

| Contenedor | Propósito | Directorio |
|---|---|---|
| `CoffeeCultivation` | Monorepo-level tooling (diagramas de arquitectura) | `.docker/` |
| `CoffeeCultivationBackend` | Lambdas y stacks Serverless del backend | `backend/.docker/` |
| `CoffeeCultivationInfrastructure` | Recursos compartidos de AWS | `infrastructure/.docker/` |

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

#### Paso 1c: Backend config (`backend/.envs/config.env`)

Copia desde el ejemplo:

```bash
cp backend/.envs/config.env.example backend/.envs/config.env
```

Completa con tu identificador de desarrollador:

```bash
DEVELOPER=your-name
STAGE=dev
```

#### Paso 1d: Infrastructure config (`infrastructure/.envs/config.env`)

Copia desde el ejemplo:

```bash
cp infrastructure/.envs/config.env.example infrastructure/.envs/config.env
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

#### Opción B: Abrir específicamente backend o infrastructure

Para trabajar solo en backend:

```bash
# En VS Code
1. Abre el archivo backend/.devcontainer.json
2. Cmd/Ctrl + Shift + P → Remote-Containers: Reopen Folder in Container
```

Para infraestructura:

```bash
# En VS Code
1. Abre el archivo infrastructure/.devcontainer.json
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

### Backend

```bash
# Instalar dependencias Lambda Layers
docker exec -w /app/backend CoffeeCultivationBackend npm install

# Validar sintaxis Python
docker exec -w /app/backend CoffeeCultivationBackend python3 -m compileall src/

# Ejecutar linter
docker exec -w /app/backend CoffeeCultivationBackend cfn-lint serverless/batch/serverless.yml

# Desplegar un stack
docker exec -w /app/backend/serverless/layers CoffeeCultivationBackend serverless deploy --stage dev

# Ver logs de CloudWatch
docker exec CoffeeCultivationBackend aws logs tail /aws/lambda/coffee-cultivation-backend-ValidateAndStore --follow
```

### Infrastructure

```bash
# Validar CloudFormation
docker exec -w /app/infrastructure CoffeeCultivationInfrastructure cfn-lint serverless/storage/serverless.yml

# Desplegar storage
docker exec -w /app/infrastructure/serverless/storage CoffeeCultivationInfrastructure serverless deploy --stage dev

# Ver parámetros SSM
docker exec CoffeeCultivationInfrastructure aws ssm describe-parameters --filters Key=Name,Values=coffee-cultivation-queue
```

### Monorepo (diagramas, etc.)

```bash
# Generar diagramas de arquitectura
docker exec -w /app/docs CoffeeCultivation python3 architecture.py
```

## Troubleshooting

### El contenedor no inicia

```bash
# Reconstruir la imagen Docker
docker-compose -f .docker/docker-compose.yml build --no-cache

# Luego reintentar
docker-compose -f .docker/docker-compose.yml up -d
```

### Permisos denegados en .pth

Si ves errores al instalar layers:

```bash
# Ejecuta dentro del contenedor como sudo
docker exec -u root CoffeeCultivationBackend chown -R coffee-cultivation /usr/local/lib/python3.13/site-packages/
```

### Credenciales expiradas

Actualiza `.envs/aws.env` con nuevas credenciales y reinicia el contenedor:

```bash
docker restart CoffeeCultivationBackend
docker restart CoffeeCultivationInfrastructure
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
docker exec -w /app/backend CoffeeCultivationBackend python3 -m compileall src/
docker exec -w /app/infrastructure CoffeeCultivationInfrastructure cfn-lint serverless/**/*.yml
```

### 3. Probar localmente

```bash
# Seed de base de datos (solo dev/test)
docker exec -w /app/backend CoffeeCultivationBackend ./database/seeders/seed.sh --historical-data 100 --sensor-readings 500

# Ver migraciones
docker exec -w /app/backend CoffeeCultivationBackend python3 -m database.demo_indexes
```

### 4. Desplegar

```bash
# Backend layers (primero)
docker exec -w /app/backend/serverless/layers CoffeeCultivationBackend serverless deploy --stage dev

# Batch
docker exec -w /app/backend/serverless/batch CoffeeCultivationBackend serverless deploy --stage dev

# Streaming
docker exec -w /app/backend/serverless/streaming CoffeeCultivationBackend serverless deploy --stage dev

# Infrastructure (en orden)
docker exec -w /app/infrastructure/serverless/storage CoffeeCultivationInfrastructure serverless deploy --stage dev
docker exec -w /app/infrastructure/serverless/queue CoffeeCultivationInfrastructure serverless deploy --stage dev
docker exec -w /app/infrastructure/serverless/secrets CoffeeCultivationInfrastructure serverless deploy --stage dev
docker exec -w /app/infrastructure/serverless/iot CoffeeCultivationInfrastructure serverless deploy --stage dev
docker exec -w /app/infrastructure/serverless/alerts CoffeeCultivationInfrastructure serverless deploy --stage dev
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

| Variable | Ubicación | Propósito |
|---|---|---|
| `AWS_ACCESS_KEY_ID` | `.envs/aws.env` | Autenticación AWS |
| `DEVELOPER` | `backend/.envs/config.env`, `infrastructure/.envs/config.env` | Namespacing de recursos |
| `DEPLOY_APP` | Establecida automáticamente por docker-compose | Nombre de la aplicación en recursos AWS (`coffee-cultivation`) |
| `MONGO_CREDENTIALS_SECRET_NAME` | Establecida por Lambda handlers | Ruta SSM de MongoDB credentials |

---

**Última actualización**: 2026-08-30  
**Proyecto**: Cultivo de Café Inteligente  
**Arquitectura**: Serverless + MongoDB Atlas + S3 Medallion Lake
