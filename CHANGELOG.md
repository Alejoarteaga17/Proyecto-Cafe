# Changelog

## Unreleased

### Added

- Approved medallion pipeline artifacts for Bronze, Silver and Gold.
- Local validation, deduplication and aggregation transformations with tests.
- Glue Job 1, Glue Job 2 and Step Functions definitions.
- IoT Core to Data Firehose to S3 Bronze infrastructure path.
- Data dictionary, catalog, lineage, RACI and architecture status documents.

### Changed

- Historical upload Lambda now validates the upload boundary and writes raw files to S3 Bronze.
- Existing MongoDB, SQS, DLQ and SNS resources are documented as legacy rather than treated as target architecture.

### Pending

- AWS deployment verification, QuickSight consumption, raw/Silver catalog tables and DataOps automation remain deferred or not verified.
