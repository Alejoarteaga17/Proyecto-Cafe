# Changelog

## Unreleased

### Added

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

- Historical upload Lambda now validates the upload boundary and writes raw files to S3 Bronze.
- Historical uploads now reject invalid values, inconsistent ISO dates and empty rows
  instead of silently imputing them.
- Glue Job 1 is scoped to `bronze/historical/` so IoT JSON is not parsed as CSV.
- Removed the MongoDB, SQS, DLQ, Secrets Manager and SNS components, including
  their source code, infrastructure, fixtures and development dependencies.
- Batch pipeline marked complete for local/IaC scope; AWS execution remains
  explicitly unverified.
- Streaming remains AWS-unverified; certificate provisioning and an authorized
  MQTT integration test are required before claiming end-to-end delivery.

### Pending

- AWS deployment verification and QuickSight consumption remain not verified or
  deferred to the final sprint. DataOps automation remains deferred to the final
  sprint.
