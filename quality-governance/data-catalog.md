# Catálogo de datos

Este catálogo es el inventario lógico del data lake. Los prefijos son rutas
S3; no son carpetas físicas independientes.

| Activo | Capa | Formato | Ubicación lógica | Productor | Consumidor | Estado |
|---|---|---|---|---|---|---|
| Carga histórica original | Bronze | CSV | `bronze/uploads/<dataset_id>/` | API Gateway + Lambda | Glue BronzeToSilver | Implementado |
| Histórico validado | Silver | Parquet | `silver/historical/year=YYYY/month=MM/Location=.../` | Glue BronzeToSilver | Glue SilverToGold/Athena | Script implementado; Job pendiente |
| Registros rechazados | Quarantine | JSON | `silver/quarantine/<dataset_id>/` | Glue BronzeToSilver | Operación/calidad | Script implementado; Job pendiente |
| Resumen histórico | Gold | Parquet | `gold/historical/` | Glue SilverToGold | Athena/QuickSight futuro | Script implementado; Job pendiente |
| Lecturas de sensores | Streaming | JSON/evento | Prefijo streaming por definir | IoT Core/Firehose | Glue/Athena futuro | Fuera del despliegue batch actual |

## Retención y sensibilidad

- **Bronze:** fuente original; conservar para reprocesamiento y auditoría.
- **Silver:** datos tipados y validados; conservar mientras existan
  consumidores analíticos.
- **Quarantine:** conservar durante el periodo operativo definido por el
  equipo para corregir y reprocesar errores.
- **Gold:** conservar según la necesidad analítica y los costos de consulta.
- No almacenar credenciales, tokens ni secretos dentro de ninguna capa.

El Glue Data Catalog y las tablas Athena deben reflejar este inventario cuando
se agreguen esos recursos a la infraestructura.
