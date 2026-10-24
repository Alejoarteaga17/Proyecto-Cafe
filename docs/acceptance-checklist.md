# Checklist de aceptación

| Requisito | Estado | Evidencia |
| --- | --- | --- |
| README actualizado | COMPLETE | `README.md`, `batch/README.md` |
| CHANGELOG actualizado | COMPLETE | `CHANGELOG.md` |
| Arquitectura aprobada documentada | COMPLETE | `docs/architecture.md` |
| IaC del flujo aprobado | NOT VERIFIED | Recursos declarados; `serverless print`/AWS no ejecutados en esta auditoría |
| Historical ingestion | COMPLETE local / NOT VERIFIED AWS | Lambda valida exactamente 19 columnas, tipos, fechas, filas, columnas inesperadas y tamaño; pruebas locales; despliegue no verificado |
| IoT ingestion | PARTIAL / NOT VERIFIED AWS | IoT Core/Firehose y contrato/catalogación declarados; publicación AWS no verificada |
| Glue transformations | COMPLETE local / NOT VERIFIED AWS | `batch/glue/`, contrato documentado, transformaciones y pruebas locales; ejecución Glue no verificada |
| Step Functions | COMPLETE in IaC / NOT VERIFIED AWS | Integración `.sync`, secuencia y reintentos en `data-platform/resources.yml` |
| Dos optimizaciones | COMPLETE in code | Particionado S3 por `YEAR/MM`, Parquet Gold y Athena workgroup |
| Data dictionary | COMPLETE | `docs/data-dictionary.md` |
| Data catalog | COMPLETE in IaC / NOT VERIFIED AWS | Tablas IoT Bronze, histórico Bronze/Silver/Gold declaradas |
| Data lineage | COMPLETE | `docs/data-lineage.md` |
| RACI | COMPLETE | `docs/raci.md` |
| Data-quality rules | COMPLETE local | Validadores históricos/IoT y pruebas locales |
| Componentes MongoDB/SQS/DLQ/Secrets/SNS | COMPLETE | Código, stacks, fixtures y dependencias eliminados |
| DataOps | DEFERRED TO FINAL SPRINT | README y changelog |
| Consumption/QuickSight | DEFERRED TO FINAL SPRINT | README y architecture |

Ningún estado de esta tabla implica que exista un recurso desplegado en AWS. La
verificación pendiente requiere credenciales, `serverless print/deploy`, Glue y
consultas Athena en una cuenta autorizada. La suite local ejecutada durante esta
revisión terminó con `11 passed`; no sustituye una prueba de integración AWS.
