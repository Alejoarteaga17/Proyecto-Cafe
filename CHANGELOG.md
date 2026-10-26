# Changelog

## Unreleased

### Added

- Athena optimization benchmark queries and documentation for comparing
  partition pruning, Parquet Gold and the unoptimized Bronze baseline.
- Expanded local test coverage for batch validation, CSV upload edge cases,
  CORS, IoT agronomic rules, simulator arguments and Glue job orchestration
  helpers.
- Approved medallion pipeline artifacts for Bronze, Silver and Gold.
- Local validation, deduplication and aggregation transformations with tests.
- Glue Job 1, Glue Job 2 and Step Functions definitions.
- IoT Core to Data Firehose to S3 Bronze infrastructure path.
- Data dictionary, catalog, lineage, RACI and architecture status documents.
- Reproducible PowerShell publisher for Glue scripts and shared pipeline code.
- IoT Bronze catalog contract and simulator payloads containing `sensor_id`.
- Batch upload contract now rejects duplicate and unexpected CSV columns.
- Streaming simulator now supports finite seeded runs and validates every event
  against the IoT contract before emitting it.
- IoT infrastructure now declares the simulator Thing and its SSM name
  parameter while preserving the direct IoT Core to Firehose to S3 path.

### Changed

- Job 1 ahora registra y actualiza las particiones `YEAR/MM` de Silver en Glue
  Data Catalog, habilitando consultas de Athena sobre el histórico validado.
- Job 1 ahora valida que `DOY` corresponda a `Date`, controla años no
  bisiestos, rangos de latitud/longitud y valores numéricos no finitos.
  Rechazos y duplicados quedan separados por `JOB_RUN_ID`, con métricas de
  calidad por ejecución. Se eliminó `collect()` del recorrido normal de filas.
- Job 2 registra particiones Gold con valores string compatibles con Glue y
  normaliza la ruta S3 para evitar dobles barras.
- Silver ahora conserva una estrategia estable `YEAR/MM` y usa sobrescritura
  dinámica de particiones en Glue Job 1, evitando borrar años o meses que no
  forman parte de una nueva carga.
- Corregida la lectura de particiones `YEAR/MM` en Glue Job 2 y agregada la
  autorización `s3:DeleteObject` requerida para reintentos controlados de Job 1.
- Job 2 ahora registra las particiones Gold en Glue Data Catalog para que Athena
  pueda consultar automáticamente los resultados de cada ejecución.
- Verificado end-to-end en AWS el flujo Step Functions → Glue Job 1 → Glue Job 2,
  con resultados en Silver y Gold.
- Historical upload Lambda now validates the upload boundary and writes raw files to S3 Bronze.
- Historical uploads now reject invalid values, inconsistent ISO dates and empty rows
  instead of silently imputing them.
- Glue Job 1 is scoped to `bronze/historical/` so IoT JSON is not parsed as CSV.
- Removed the MongoDB, SQS, DLQ, Secrets Manager and SNS components, including
  their source code, infrastructure, fixtures and development dependencies.
- Batch pipeline verified locally and end-to-end in AWS, including Step
  Functions, Glue, Data Catalog and an Athena query.
- Streaming ingestion verified in AWS with an authorized MQTT event delivered
  by IoT Core and Firehose to S3 Bronze.

### Pending

- QuickSight consumption remains deferred to the final sprint. DataOps
  automation remains deferred to the final sprint.
