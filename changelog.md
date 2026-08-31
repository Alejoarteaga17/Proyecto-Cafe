# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Coffee agronomic alert engine with validation for soil pH, humidity, temperature, relative humidity and NPK thresholds
- Historical batch pipeline adapted to the coffee dataset: required 19-column validation, imputación for missing sensor values and Gold-layer partitioning by YEAR/MM/Location
- Streaming pipeline for coffee sensors with MQTT-to-SQS-to-Lambda validation before MongoDB persistence
- Support for S3 medallion storage with Silver and Gold layers aligned to the coffee data model

### Changed

- Removed the legacy RDS/PostgreSQL path from the active architecture because MongoDB Atlas and S3 are the active sources of truth in this project
- Renamed the active infrastructure resources to a coffee-oriented naming convention and kept the DLQ/SNS/CloudWatch alerting pattern intact

## [0.0.2] - 29/08/2026

### Added

- Coffee-oriented validation and simulation modules for agronomic monitoring and alerting
- Batch and streaming validation flows aligned to the coffee dataset schema and the IoT Telemery payload structure
- Infrastructure cleanup to remove the previous traffic-course remnants and keep only the active coffee architecture

## [0.0.1] - 29/08/2026

### Added

- Dockerized development environment for the backend and infrastructure subprojects
- Shared AWS infrastructure for storage, queues, secrets, IoT routing and CloudWatch/SNS alerts
- Serverless Lambda code for the coffee batch and streaming flows, using MongoDB Atlas as the operational persistence layer
- Architecture diagrams for the active coffee pipelines in the docs folder
