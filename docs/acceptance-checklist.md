# Checklist de aceptación

| Requisito | Estado | Evidencia |
| --- | --- | --- |
| README actualizado | COMPLETE | `README.md` |
| CHANGELOG actualizado | COMPLETE | `CHANGELOG.md` |
| Arquitectura aprobada documentada | COMPLETE | `docs/architecture.md` |
| IaC del flujo aprobado | NOT VERIFIED | Templates parseados localmente; Serverless print requiere autenticación/licencia y espacio disponible |
| Historical ingestion | COMPLETE local / NOT VERIFIED AWS | Lambda y 3 pruebas locales; despliegue no verificado |
| IoT ingestion | NOT VERIFIED | IoT Core/Firehose declarados en `iot/iot.yml` |
| Glue transformations | COMPLETE local / NOT VERIFIED AWS | `batch/glue/`, `batch/tests/test_transformations.py`, 7 pruebas totales |
| Step Functions | NOT VERIFIED | `data-platform/resources.yml` |
| Dos optimizaciones | COMPLETE in code | S3 partitioning y Parquet/partition pruning declarados |
| Data dictionary | COMPLETE | `docs/data-dictionary.md` |
| Data catalog | COMPLETE in IaC / NOT VERIFIED AWS | Tablas Bronze, Silver y Gold declaradas |
| Data lineage | COMPLETE | `docs/data-lineage.md` |
| RACI | COMPLETE | `docs/raci.md` |
| Data-quality rules | COMPLETE local | validator y pruebas locales |
| DataOps | DEFERRED TO FINAL SPRINT | README y changelog |
| Consumption/QuickSight | DEFERRED TO FINAL SPRINT | README y architecture |

Ningún estado de esta tabla implica que exista un recurso desplegado en AWS. La verificación pendiente requiere credenciales, `serverless print/deploy`, Glue y consultas Athena en una cuenta autorizada.
