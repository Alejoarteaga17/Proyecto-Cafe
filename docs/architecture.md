# Arquitectura aprobada

## Estado verificado

| Componente | Estado | Evidencia |
| --- | --- | --- |
| Historical CSV -> API Gateway -> Lambda -> S3 Bronze | IMPLEMENTED local / NOT VERIFIED AWS | `batch/serverless/functions.yml`, `batch/src/validate_and_store/handler.py`, `batch/tests/test_upload_handler.py` |
| IoT sensors -> IoT Core -> Data Firehose -> S3 Bronze | IMPLEMENTED local/IaC / NOT VERIFIED AWS | `streaming/infrastructure/serverless/iot/iot.yml`, `streaming/simulator/simulate_coffee_sensors.py`, `streaming/tests/test_sensor_simulator.py` |
| Bronze -> Glue Job 1 -> Silver | IMPLEMENTED local / NOT VERIFIED AWS | `batch/glue/job_bronze_to_silver.py`, `batch/tests/test_transformations.py` |
| Silver -> Glue Job 2 -> Gold | IMPLEMENTED local / NOT VERIFIED AWS | `batch/glue/job_silver_to_gold.py`, `batch/tests/test_transformations.py` |
| Step Functions histórico e IoT | IMPLEMENTADO en IaC, NOT VERIFIED en AWS | `batch/infrastructure/serverless/data-platform/resources.yml` |
| Glue Data Catalog y Athena | IMPLEMENTADO en IaC, NOT VERIFIED en AWS | `batch/infrastructure/serverless/data-platform/resources.yml` |
| QuickSight | DEFERRED TO FINAL SPRINT | No se añade dashboard de consumo en este sprint |

## Flujos

```mermaid
flowchart LR
  CSV[Historical CSV] --> API[API Gateway]
  API --> Lambda[Lambda validation]
  Lambda --> Bronze[(S3 Bronze)]
  Sensors[Simulated IoT sensors] --> IoT[AWS IoT Core]
  IoT --> Firehose[Amazon Data Firehose]
  Firehose --> Bronze
  Bronze --> Job1[AWS Glue Job 1]
  Job1 --> Silver[(S3 Silver)]
  Silver --> Job2[AWS Glue Job 2]
  Job2 --> Gold[(S3 Gold)]
  SF[AWS Step Functions] -. orchestrates .-> Job1
  SF -. orchestrates .-> Job2
  IotJob1[IoT Glue Job 1] --> IotSilver[(S3 Silver IoT)]
  IotSilver --> IotJob2[IoT Glue Job 2]
  IotJob2 --> IotGold[(S3 Gold IoT)]
  IotSF[IoT Step Functions] -. orchestrates .-> IotJob1
  IotSF -. orchestrates .-> IotJob2
  Gold --> Athena[Amazon Athena]
  Catalog[Glue Data Catalog] --> Athena
  Athena --> QS[Amazon QuickSight]
```

## Componentes retirados

Los módulos y stacks de MongoDB, SQS, DLQ, Secrets Manager y SNS fueron
eliminados por pertenecer a la arquitectura anterior. No existen como
dependencias del flujo aprobado.
