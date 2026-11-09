# Comparativo de optimizaciones en Athena

## Qué está implementado

| Optimización | Evidencia de implementación | Beneficio esperado |
| --- | --- | --- |
| Particionado S3 por `YEAR/MM` | [Job 1](../batch/glue/job_bronze_to_silver.py), [Job 2](../batch/glue/job_silver_to_gold.py) y `PartitionKeys` de `HistoricalGoldTable` en [resources.yml](../batch/infrastructure/serverless/data-platform/resources.yml) | Athena puede aplicar partition pruning cuando el `WHERE` usa ambas claves. |
| Parquet en Gold | `write.parquet(...)` en [Job 2](../batch/glue/job_silver_to_gold.py) y `classification: parquet` en [resources.yml](../batch/infrastructure/serverless/data-platform/resources.yml) | Formato columnar y compresión reducen bytes leídos frente al CSV/JSON crudo. |
| Resumen Gold persistido | `silver_to_gold(...)` en [transformations.py](../batch/src/pipeline/transformations.py) | La consulta de consumo lee agregados en vez de recalcular todo el detalle. |

El `WorkGroup` de Athena con engine 3 y ubicación de resultados está definido
en [resources.yml](../batch/infrastructure/serverless/data-platform/resources.yml).
Eso configura la ejecución, pero no es por sí solo una medición de mejora.

## Comparativo que debe ejecutarse

Las consultas reproducibles están en
[athena_optimization_comparison.sql](../batch/benchmarks/athena_optimization_comparison.sql).
Para un período existente, ejecutar:

1. La consulta 1 contra `coffee_historical_bronze` como línea base.
2. La consulta 2 contra Gold con `WHERE YEAR = ... AND MM = ...` para medir
   particionado y lectura optimizada.
3. La consulta 3 como control: misma tabla Gold, pero sin predicado de
   partición. Su resultado debe ser equivalente al de la consulta 2 y su
   costo normalmente mayor.
4. La consulta 4 para medir el resumen Parquet Gold frente al conteo de la
   línea base. Esta comparación incluye la pre-agregación; no aísla Parquet.

La comparación correcta no es únicamente el tiempo de pared. Athena puede
tener tiempos variables por concurrencia y archivos pequeños. Registrar para
cada `QueryExecutionId`:

| Escenario | `DataScannedInBytes` | `TotalExecutionTimeInMillis` | Resultado |
| --- | ---: | ---: | --- |
| Bronze CSV, filtro de período | pendiente de ejecutar | pendiente de ejecutar | `record_count` |
| Gold Parquet, filtro `YEAR/MM` | pendiente de ejecutar | pendiente de ejecutar | `record_count` |
| Gold Parquet, sin filtro de partición | pendiente de ejecutar | pendiente de ejecutar | `record_count` |

Los valores se obtienen de `GetQueryExecution`:

```bash
aws athena get-query-execution \
  --query-execution-id <QueryExecutionId> \
  --work-group <workgroup> \
  --query 'QueryExecution.{status:Status.State,bytes:Statistics.DataScannedInBytes,time_ms:Statistics.TotalExecutionTimeInMillis}'
```

La mejora porcentual para una métrica se calcula como:

```text
mejora (%) = (baseline - optimizado) / baseline * 100
```

Para bytes se compara `DataScannedInBytes`; para tiempo se compara
`TotalExecutionTimeInMillis`. No se debe completar la tabla con estimaciones:
hasta ejecutar estas consultas en AWS, la mejora está **pendiente de medir**.

## Viabilidad y límites de la comparación

- `transformations.py` prueba la lógica de validación y agregación local, pero
  no puede demostrar bytes escaneados ni el plan de Athena.
- La viabilidad de particionado y Parquet sí queda confirmada por el código de
  Glue y el contrato de Glue Data Catalog/IaC citados arriba.
- Bronze y Gold no tienen exactamente el mismo esquema: Bronze contiene detalle
  CSV y Gold contiene agregados. Por eso la consulta 4 demuestra el beneficio
  del producto Gold (Parquet + pre-agregación), no el de Parquet aislado.
- Para aislar exclusivamente el formato, habría que escribir una copia
  Parquet de detalle con el mismo esquema y ejecutar exactamente la consulta 1
  contra ambas tablas. Esa prueba no está desplegada en este repositorio.
