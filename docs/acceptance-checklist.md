# Checklist de aceptación

| Requisito | Estado | Evidencia |
| --- | --- | --- |
| README actualizado | COMPLETE | `README.md`, `batch/README.md` |
| CHANGELOG actualizado | COMPLETE | `CHANGELOG.md` |
| Arquitectura aprobada documentada | COMPLETE | `docs/architecture.md` |
| IaC del flujo aprobado | COMPLETE in repository; deployment NOT VERIFIED in this review | Stacks Storage, Data Platform, API/Lambda e IoT están versionados; no se ejecutó despliegue durante esta revisión |
| Historical ingestion | COMPLETE in code; AWS evidence historical | Lambda, API Gateway, validación y escritura a `bronze/historical/` están en el repositorio; la ejecución AWS indicada es evidencia histórica |
| IoT ingestion | COMPLETE in code; AWS evidence historical | IoT Core, Firehose y prefijo `bronze/iot/` están en IaC; la entrega MQTT indicada es evidencia histórica |
| Glue transformations | COMPLETE in code; AWS evidence historical | Los cuatro jobs están separados por flujo y tienen pruebas locales; la ejecución AWS indicada es evidencia histórica |
| Step Functions | COMPLETE in IaC; AWS execution NOT VERIFIED in this review | `HistoricalEtlStateMachine` e `IotEtlStateMachine` usan `glue:startJobRun.sync` y encadenan Job 1 -> Job 2 |
| Dos optimizaciones | COMPLETE in code; benchmark NOT VERIFIED | Particionado S3 por `YEAR/MM`, Parquet Gold y resumen Gold; consultas comparativas en `batch/benchmarks/` y procedimiento en `docs/optimization-benchmark.md` |
| Data dictionary | COMPLETE | `docs/data-dictionary.md` |
| Data catalog | COMPLETE in IaC; AWS query NOT VERIFIED in this review | Tablas Bronze/Silver/Gold y registro de particiones están definidos en `resources.yml`; Athena query `records = 1` es evidencia histórica |
| QuickSight configuration | COMPLETE in IaC; dashboard NOT VERIFIED | `quicksight.yml` opcional define fuente Athena y datasets históricos/IoT; el contrato está en `docs/quicksight-dashboard-definition.json` |
| Data lineage | COMPLETE | `docs/data-lineage.md` |
| RACI | COMPLETE | `docs/raci.md` |
| Data-quality rules | COMPLETE local | Validadores históricos/IoT y pruebas locales |
| Componentes MongoDB/SQS/DLQ/Secrets/SNS | COMPLETE | Código, stacks, fixtures y dependencias eliminados |
| DataOps | DEFERRED TO FINAL SPRINT | README y changelog |
| Consumption/dashboard validation | PARTIAL | Configuración y contrato están listos; requiere suscripción, principal, permisos y validación account-specific |

La verificación AWS registrada corresponde a una cuenta de desarrollo autorizada
y es evidencia histórica, no una ejecución de esta revisión. La ejecución
end-to-end de Step Functions indicada anteriormente produjo:

- `silver/historical/YEAR=2026/MM=8/...json`
- `gold/historical/YEAR=2026/MM=8/...snappy.parquet`
- Consulta Athena `SELECT count(*) FROM coffee_historical_gold`: `1`

La suite local ejecutada en la revisión actual terminó con `72 passed`.
La cobertura no se volvió a medir en esta revisión; cualquier porcentaje
anterior debe tratarse como evidencia histórica y no como resultado de esta
validación. La suite local se mantiene como complemento de la prueba de
integración AWS.
