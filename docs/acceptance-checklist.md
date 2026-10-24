# Checklist de aceptación

| Requisito | Estado | Evidencia |
| --- | --- | --- |
| README actualizado | COMPLETE | `README.md`, `batch/README.md` |
| CHANGELOG actualizado | COMPLETE | `CHANGELOG.md` |
| Arquitectura aprobada documentada | COMPLETE | `docs/architecture.md` |
| IaC del flujo aprobado | COMPLETE | Stacks Storage, Data Platform, API/Lambda e IoT desplegados y actualizados en `us-east-1`; no equivale a una autorización de despliegue futura |
| Historical ingestion | COMPLETE | Lambda validó y almacenó un CSV real en `bronze/historical/` mediante API Gateway |
| IoT ingestion | COMPLETE | Evento MQTT real entregado por IoT Core/Firehose en `bronze/iot/` como objeto GZIP |
| Glue transformations | COMPLETE | Ejecución AWS verificada: Job 1 escribió Silver particionado y Job 2 escribió Gold Parquet |
| Step Functions | COMPLETE | Ejecución real terminó `SUCCEEDED` usando `glue:startJobRun.sync` para ambos jobs |
| Dos optimizaciones | COMPLETE in code | Particionado S3 por `YEAR/MM`, Parquet Gold y Athena workgroup |
| Data dictionary | COMPLETE | `docs/data-dictionary.md` |
| Data catalog | COMPLETE | Job 2 registra las particiones Gold en Glue Data Catalog; Athena devolvió `records = 1`; QuickSight sigue fuera del sprint |
| Data lineage | COMPLETE | `docs/data-lineage.md` |
| RACI | COMPLETE | `docs/raci.md` |
| Data-quality rules | COMPLETE local | Validadores históricos/IoT y pruebas locales |
| Componentes MongoDB/SQS/DLQ/Secrets/SNS | COMPLETE | Código, stacks, fixtures y dependencias eliminados |
| DataOps | DEFERRED TO FINAL SPRINT | README y changelog |
| Consumption/QuickSight | DEFERRED TO FINAL SPRINT | README y architecture |

La verificación AWS registrada corresponde a la cuenta de desarrollo autorizada,
región `us-east-1`, y no implica que QuickSight esté configurado. La ejecución
end-to-end de Step Functions terminó correctamente y produjo:

- `silver/historical/YEAR=2026/MM=8/...json`
- `gold/historical/YEAR=2026/MM=8/...snappy.parquet`
- Consulta Athena `SELECT count(*) FROM coffee_historical_gold`: `1`

La suite local ejecutada durante esta revisión terminó con `13 passed`; se
mantiene como complemento de la prueba de integración AWS.
