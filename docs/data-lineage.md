# Lineage y catálogo

## Lineage

1. Historical CSV (Kaggle) -> API Gateway -> Lambda: validación de encabezados, formato, tamaño y filas no vacías.
2. Lambda -> S3 Bronze: conserva el archivo crudo bajo `bronze/historical/`.
3. Simulated IoT sensors -> AWS IoT Core -> Amazon Data Firehose -> S3 Bronze: entrega eventos JSON bajo `bronze/iot/`.
4. S3 Bronze -> Glue Job 1 -> S3 Silver: validación, normalización, deduplicación, particionado y salidas de calidad.
5. S3 Silver -> Glue Job 2 -> S3 Gold: agregación analítica a Parquet.
6. Step Functions inicia Glue Job 1 y, solo tras éxito, Glue Job 2.
7. S3 Gold -> Glue Data Catalog -> Athena -> QuickSight.

## Catálogo

| Dataset | Capa | Ubicación | Formato | Catálogo |
| --- | --- | --- | --- | --- |
| historical_raw | Bronze | `s3://<data-lake>/bronze/historical/` | CSV | pendiente de tabla raw |
| iot_raw | Bronze | `s3://<data-lake>/bronze/iot/` | JSON.GZIP | pendiente de tabla raw |
| historical_silver | Silver | `s3://<data-lake>/silver/historical/` | JSON | pendiente de tabla silver |
| historical_gold | Gold | `s3://<data-lake>/gold/historical/` | Parquet | `coffee_historical_gold` |

El catálogo y la tabla Gold están declarados en `batch/infrastructure/serverless/data-platform/resources.yml`; la existencia y consulta en AWS aún no está verificada.
