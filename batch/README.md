# README

## Resumen

`batch` contiene el pipeline histórico completo del data lake. La ruta
aprobada es API Gateway -> Lambda -> S3 Bronze -> Glue Job 1 -> Silver ->
Glue Job 2 -> Gold.

El pipeline se despliega como varios stacks independientes bajo `serverless/` y
usa su infraestructura propia dentro de `batch/infrastructure`.

## Configuración

### Contenedor de desarrollo

1. Instala la extensión `ms-vscode-remote.remote-containers`.
2. Abre la carpeta del repositorio en VS Code y confirma la apertura dentro del contenedor.

### Variables de entorno

Crea los archivos en `.envs` con los valores requeridos por AWS, Serverless y el entorno del proyecto.

### Dependencias

El usuario de Serverless debe tener permisos IAM adecuados en la cuenta de AWS y sus credenciales deben configurarse desde `.envs/aws.env`.

### Despliegue

Se usa Serverless Framework y cada stack vive dentro de `serverless/` y `infrastructure/serverless/` del mismo flujo.

Orden recomendado:

1. `infrastructure/serverless/storage`
2. Publica los scripts Glue con `glue/publish-scripts.ps1 -BucketName <bucket>`.
3. `infrastructure/serverless/data-platform`
4. `serverless`

Valida primero con `serverless print --stage dev` y despliega solo con autorización explícita.

Los componentes excluidos de la arquitectura anterior fueron eliminados y no
deben reintroducirse.

### Eliminación

Usa `serverless remove` en el orden inverso al despliegue para evitar dependencias de infraestructura.

---

## Contrato operativo

- La API recibe JSON con `file`, cuyo valor es el CSV codificado en Base64.
- El archivo debe ser UTF-8, contener exactamente las 19 columnas requeridas y
  no superar 5 MiB ni 300 filas.
- El límite de 5 MiB es intencional: el archivo viaja completo dentro de una
  invocación síncrona de API Gateway/Lambda, con expansión adicional por
  Base64. No se debe elevar sin cambiar el contrato de transporte.
- Lambda valida estructura, tipos, fechas, rangos y consistencia antes de
  escribir en `bronze/historical/`.
- Glue Job 1 conserva filas rechazadas y duplicadas en `silver/rejected/` y
  `silver/duplicates/`, separadas por `run_id`, y escribe filas válidas
  particionadas por `YEAR/MM`. También publica métricas de calidad por
  ejecución en `silver/quality/`.
- Glue Job 2 lee Silver JSON y escribe Gold Parquet particionado por `YEAR/MM`.
- Step Functions ejecuta Job 2 únicamente después del éxito de Job 1.

## Validación local del batch

```bash
cd batch
python3 -m pytest -q
python3 -m compileall -q src glue tests
```

La validación local no confirma recursos desplegados en AWS. La validación de
infraestructura requiere `serverless print --stage dev` y `cfn-lint` dentro del
contenedor.

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
