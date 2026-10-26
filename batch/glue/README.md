# Glue batch pipeline

## Contrato de entrada y salida

| Job | Entrada | Salidas | Formato |
| --- | --- | --- | --- |
| `job_bronze_to_silver.py` | `s3://<bucket>/bronze/historical/` | `silver/historical/`, `silver/rejected/`, `silver/duplicates/`, `silver/quality/` | JSON |
| `job_silver_to_gold.py` | `s3://<bucket>/silver/historical/` | `gold/historical/` | Parquet |

Job 1 valida y normaliza las 19 columnas históricas, elimina duplicados
exactos y conserva diagnósticos. Silver usa una partición estable por `YEAR` y
`MM`; no cambia la estructura según el número de años de cada archivo. Job 2
agrupa por `Location`, `YEAR` y `MM` para producir los indicadores
documentados en `docs/data-dictionary.md`.

Job 1 usa `spark.sql.sources.partitionOverwriteMode=dynamic` junto con
`mode('overwrite')`. Una ejecución reemplaza únicamente las particiones
`YEAR/MM` que recibió y conserva las demás particiones históricas. Esto
permite reprocesar un mes sin borrar otros años. La reejecución debe leer el
mismo alcance de Bronze para que la deduplicación y la validación sean
deterministas.

Job 1 registra o actualiza en Glue Data Catalog cada partición
`YEAR/MM` escrita en Silver. La tabla `coffee_historical_silver` puede
consultarse desde Athena con filtros sobre ambas claves, por ejemplo
`WHERE YEAR = 2024 AND MM = 1`. Las particiones se registran con valores
string, que es el formato requerido por la API de Glue aunque las claves del
catálogo sean de tipo `int`.

Las salidas de rechazos y duplicados se escriben bajo
`run_id=<JOB_RUN_ID>` para conservar el diagnóstico de cada ejecución. El
resumen de calidad en `silver/quality/run_id=<JOB_RUN_ID>/` incluye conteos de
entrada, válidos, rechazados y duplicados, número de particiones afectadas y
el rango de fechas válido. Actualmente es evidencia operacional; los
umbrales que deban detener el pipeline deben definirse con datos reales.

La granularidad recomendada es:

- `YEAR/MM` para el histórico actual: permite consultar un año completo o un
  mes con partition pruning sin crear demasiadas particiones.
- `YEAR/MM/DD` únicamente si el volumen crece lo suficiente para que cada mes
  produzca archivos grandes y las consultas operativas filtren por día.
- No se recomienda alternar entre solo `MM`, solo `YEAR` o `YEAR/MM` según si
  un archivo contiene uno o varios años. Una tabla debe conservar las mismas
  claves de partición para que Glue Data Catalog, Athena y los reintentos sean
  compatibles. Con `YEAR/MM`, un dataset de un solo año simplemente crea las
  particiones de ese año; al llegar otro año se agregan sin migrar las
  anteriores.

Los jobs se ejecutan mediante Step Functions con la integración
`glue:startJobRun.sync`. No deben ejecutarse directamente en producción sin
publicar primero los scripts y revisar la configuración resuelta.

## Publicación

El publicador debe ejecutarse en un entorno con PowerShell y AWS CLI
configurados. Desde PowerShell:

```powershell
./publish-scripts.ps1 -BucketName <data-lake-bucket> -Region us-east-1
```

El publicador genera los dos scripts y `coffee-pipeline.zip`, que contiene el
código compartido de `src/common` y `src/pipeline`.

Después de cambiar un script Glue, es necesario volver a ejecutar el
publicador. El job ejecuta la copia indicada por `ScriptLocation` en S3, no el
archivo local del repositorio. Antes de reintentar una ejecución, verifica que
el script publicado contenga el registro de particiones con valores string y
una ruta sin doble barra.

Si solo cambió un Job o el código compartido, vuelve a ejecutar este comando
para actualizar los objetos bajo `s3://<data-lake-bucket>/glue/`; no es
necesario redesplegar todos los stacks. Después inicia una nueva ejecución de
Step Functions. Si cambió la definición de Glue, Step Functions, Data Catalog
o Athena, publica primero los scripts y luego redespliega el stack
`batch/infrastructure/serverless/data-platform`.

El flujo histórico y el flujo IoT tienen state machines separadas. Publica
también los scripts IoT desde `streaming/glue/publish-scripts.ps1` antes de
ejecutar la state machine IoT. No se agrega un disparador automático en esta
etapa: ambas ejecuciones se inician manualmente y de forma independiente.