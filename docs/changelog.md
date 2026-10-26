# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Coffee agronomic alert engine with validation for soil pH, humidity, temperature, relative humidity and NPK thresholds
- Historical batch pipeline adapted to the coffee dataset: required 19-column validation, type/date checks and Gold-layer partitioning by YEAR/MM
- IoT sensor contract and simulator aligned to MQTT-to-IoT Core-to-Data Firehose-to-S3 Bronze
- Support for S3 medallion storage with Silver and Gold layers aligned to the coffee data model

### Changed

- Removed MongoDB, SQS, DLQ, SNS and Secrets Manager code, infrastructure,
  fixtures and dependencies from the repository.
- Renamed the active infrastructure resources to a coffee-oriented naming convention and documented the deployment boundary

## [0.0.2] - 29/08/2026

### Added

- Coffee-oriented validation and simulation modules for agronomic monitoring and alerting
- Batch and streaming validation flows aligned to the coffee dataset schema and the IoT Telemery payload structure
- Infrastructure cleanup to remove the previous traffic-course remnants and keep only the active coffee architecture

## [0.0.1] - 29/08/2026

### Added

- Dockerized development environment for the backend and infrastructure subprojects
- Shared AWS infrastructure for S3 storage, IoT routing, Glue, Step Functions, Data Catalog and Athena
- Serverless Lambda code for historical CSV validation and S3 Bronze ingestion
- Architecture diagrams for the active coffee pipelines in the docs folder
