# Checklist de aceptación

| Requisito | Estado | Evidencia |
| --- | --- | --- |
| README actualizado | COMPLETE | `README.md`, `batch/README.md` |
| CHANGELOG actualizado | COMPLETE | `CHANGELOG.md` |
| Arquitectura aprobada documentada | COMPLETE | `docs/architecture.md` |
| IaC del flujo aprobado | COMPLETE in repository; deployment NOT VERIFIED in this review | Stacks Storage, Data Platform, API/Lambda e IoT están versionados; no se ejecutó despliegue durante esta revisión |
| Historical ingestion | COMPLETE in code; AWS evidence historical | Lambda, API Gateway, validación y escritura a `bronze/historical/` están en el repositorio; la ejecución AWS indicada es evidencia histórica |
| IoT ingestion | COMPLETE in code; AWS delivery and trigger validated | IoT Core mantiene la ruta directa a Firehose/S3 Bronze y la regla inicia `IotEtlStateMachine`; una prueba MQTT creó una ejecución real |
| IoT frontend simulator | COMPLETE in development | `frontend/index.html`, `IotSimulation` Lambda y `POST /coffee-iot/simulate`; endpoint real aceptó 2 eventos y creó ejecuciones IoT |
| Glue transformations | COMPLETE in code; AWS evidence historical | Los cuatro jobs están separados por flujo y tienen pruebas locales; la ejecución AWS indicada es evidencia histórica |
| Step Functions | Historical and IoT automatic triggers COMPLETE in development | `ValidateAndStore` inicia `HistoricalEtlStateMachine`; la regla IoT inicia `IotEtlStateMachine`; ambas máquinas usan `glue:startJobRun.sync` y encadenan Job 1 -> Job 2 |
| Dos optimizaciones | COMPLETE in code; benchmark NOT VERIFIED | Particionado S3 por `YEAR/MM`, Parquet Gold y resumen Gold; consultas comparativas en `batch/benchmarks/` y procedimiento en `docs/optimization-benchmark.md` |
| Data dictionary | COMPLETE | `docs/data-dictionary.md` |
| Data catalog | COMPLETE in IaC; AWS query NOT VERIFIED in this review | Tablas Bronze/Silver/Gold y registro de particiones están definidos en `resources.yml`; Athena query `records = 1` es evidencia histórica |
| QuickSight configuration | COMPLETE; dashboard validated in AWS development account | Fuente `coffee-cultivation-athena-dev`, datasets históricos/IoT y dashboard `coffee-cultivation-dashboard-dev`; contrato en `docs/quicksight-dashboard-definition.json` |
| QuickSight web embedding | COMPLETE in development account | `frontend/index.html` con pestañas CSV/dashboard, Lambda `DashboardEmbed` y `GET /coffee-dashboard/embed-url`; endpoint probado con respuesta `200` y URL temporal |
| Data lineage | COMPLETE | `docs/data-lineage.md` |
| RACI | COMPLETE | `docs/raci.md` |
| Data-quality rules | COMPLETE local | Validadores históricos/IoT y pruebas locales |
| Componentes MongoDB/SQS/DLQ/Secrets/SNS | COMPLETE | Código, stacks, fixtures y dependencias eliminados |
| DataOps | DEFERRED TO FINAL SPRINT | README y changelog |
| Consumption/dashboard validation | COMPLETE in development account; replication pending | Dashboard publicado y validado con dos pestañas; replicación a otra cuenta requiere suscripción, principal y permisos |

La verificación AWS registrada corresponde a una cuenta de desarrollo autorizada
y es evidencia histórica, no una ejecución de esta revisión. La ejecución
end-to-end de Step Functions indicada anteriormente produjo:

- `silver/historical/YEAR=2026/MM=8/...json`
- `gold/historical/YEAR=2026/MM=8/...snappy.parquet`
- Consulta Athena `SELECT count(*) FROM coffee_historical_gold`: `1`

La suite local ejecutada en la revisión anterior terminó con `72 passed`; la
validación del embedding y del frontend unificado se realizó por separado.
La cobertura no se volvió a medir en esta revisión; cualquier porcentaje
anterior debe tratarse como evidencia histórica y no como resultado de esta
validación. La suite local se mantiene como complemento de la prueba de
integración AWS.
