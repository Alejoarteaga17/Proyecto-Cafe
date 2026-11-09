# Changelog

## Unreleased

### Added

- Documented recovery for stale GitHub OIDC role policies when CloudFormation
  cannot create the storage stack's SSM parameters.
- Added the SSM tag permissions required by CloudFormation when creating or
  deleting the storage output parameters.
- Added the S3 resource-tag listing permission required by CloudFormation when
  updating tagged buckets.
- Configured all Serverless stacks to use their precreated, environment-scoped
  deployment buckets instead of the global Serverless Framework SSM parameter.
- Aligned the Data Platform stack names with the existing CloudFormation
  stacks and IoT state-machine exports.
- Aligned QuickSight dataset columns with the lowercase Glue Catalog schema.
- Fixed the IoT Step Functions rule to pass ETL context through IoT SQL fields,
  because the CloudFormation Step Functions action does not support `Input`.
- Fixed AWS CLI resource lookups in the deployment workflow to use the singular
  `--logical-resource-id` option.
- Optional QuickSight Athena data source and historical/IoT Gold datasets,
  disabled by default, plus a dashboard contract for account-specific setup.
- QuickSight Athena source, DIRECT_QUERY datasets and the development dashboard
  were created and validated in `us-east-1`.
- Added a unified `frontend/index.html` with CSV publication and QuickSight
  dashboard tabs served from the same HTTP origin; `dashboard.html` remains a
  compatibility redirect. The protected Lambda endpoint embeds the published
  dashboard without exposing AWS credentials.
- Published QuickSight dashboard version 3 with KPI cards, historical and IoT
  trend charts, agronomic comparison charts, and detail tables.
- Historical CSV uploads now start `HistoricalEtlStateMachine` automatically
  after Bronze validation and storage, returning the execution ARN.
- IoT Core rules now start `IotEtlStateMachine` directly while preserving the
  IoT Core -> Firehose -> S3 Bronze delivery path.
- Added the protected `POST /coffee-iot/simulate` endpoint and a frontend
  **Simulación IoT** tab with count, interval, and optional seed controls.
- Contract tests covering the separation of historical and IoT Step Functions.
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
- IoT simulator topics now use the selected sensor identifier, and generated
  readings include mandatory soil moisture.
- Added separated IoT Glue Bronze-to-Silver and Silver-to-Gold jobs, catalog
  tables, and Step Functions state machine with `YEAR/MM` partitions.
- IoT transformations normalize nutrient keys to `n/p/k`, retain the first
  reading per `sensor_id + timestamp`, and preserve invalid and duplicate
  diagnostics.

### Changed

- El despliegue CI/CD ahora separa los stacks por stage, propaga el ARN de
  `HistoricalEtlStateMachine`, autoriza el dominio CloudFront para QuickSight y
  genera la configuración de endpoints del frontend antes de publicarlo.
- El gate de validación verifica JavaScript inline, referencias ARIA y sintaxis
  de los scripts de publicación.
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

- QuickSight replication to another account requires a subscription, authorized
  principal and AWS permissions.
- DataOps automation remains deferred to the final sprint.
## Unreleased

- Added GitHub Actions CI checks for Python, tests, frontend HTML and YAML.
- Added manual OIDC-protected CD deployment for the Storage, Data Platform,
  Batch API and IoT stacks.
- Added DataOps scripts and workflow for Glue publication and independent
  historical/IoT ETL reprocessing.
