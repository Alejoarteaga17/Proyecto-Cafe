# Lineage y catálogo

## Lineage

1. Historical CSV (Kaggle) -> API Gateway -> Lambda: validación de encabezados, formato, tamaño y filas no vacías.
2. Lambda -> S3 Bronze: conserva el archivo crudo bajo `bronze/historical/`.
3. Simulated IoT sensors -> AWS IoT Core -> Amazon Data Firehose -> S3 Bronze: el simulador valida y emite eventos JSON en `sensors/coffee/<sensor-id>/data`; IoT Core deriva `sensor_id` del topic y Firehose entrega bajo `bronze/iot/`.
4. S3 Bronze -> Glue Job 1 -> S3 Silver: validación, normalización,
   deduplicación, particionado y salidas de calidad. Los rechazos, duplicados
   y métricas se conservan bajo `run_id=<JOB_RUN_ID>` para cada ejecución.
   Job 1 registra las particiones `YEAR/MM` de Silver en Glue Data Catalog
   para que Athena pueda aplicar partition pruning.
5. S3 Silver -> Glue Job 2 -> S3 Gold: agregación analítica a Parquet.
6. Step Functions inicia Glue Job 1 y, solo tras éxito, Glue Job 2.
7. S3 Gold -> Glue Data Catalog -> Athena -> QuickSight.
8. S3 Bronze IoT -> IoT Glue Job 1 -> S3 Silver IoT: valida, normaliza
   nutrientes a `n/p/k`, deduplica por `sensor_id + timestamp`, conserva
   rechazos y duplicados, y particiona por `YEAR/MM`.
9. S3 Silver IoT -> IoT Glue Job 2 -> S3 Gold IoT: agrega por sensor,
   ubicación y mes en Parquet.

## Catálogo

| Dataset | Capa | Ubicación | Formato | Catálogo |
| --- | --- | --- | --- | --- |
| historical_raw | Bronze | `s3://<data-lake>/bronze/historical/` | CSV | `coffee_historical_bronze` |
| iot_raw | Bronze | `s3://<data-lake>/bronze/iot/` | JSON.GZIP | `coffee_iot_bronze` |
| historical_silver | Silver | `s3://<data-lake>/silver/historical/` | JSON | `coffee_historical_silver` |
| historical_gold | Gold | `s3://<data-lake>/gold/historical/` | Parquet | `coffee_historical_gold` |
| iot_silver | Silver | `s3://<data-lake>/silver/iot/` | JSON | `coffee_iot_silver` |
| iot_gold | Gold | `s3://<data-lake>/gold/iot/` | Parquet | `coffee_iot_gold` |

Las tablas Bronze, Silver y Gold están declaradas en
`batch/infrastructure/serverless/data-platform/resources.yml`. La tabla Gold
fue verificada en AWS mediante Athena después de que Job 2 registrara la
partición `YEAR=2026/MM=8`; una consulta de conteo devolvió `1` registro.
QuickSight permanece reservado para el sprint final.
