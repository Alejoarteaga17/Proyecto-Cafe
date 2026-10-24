# Glue batch pipeline

## Contrato de entrada y salida

| Job | Entrada | Salidas | Formato |
| --- | --- | --- | --- |
| `job_bronze_to_silver.py` | `s3://<bucket>/bronze/historical/` | `silver/historical/`, `silver/rejected/`, `silver/duplicates/` | JSON |
| `job_silver_to_gold.py` | `s3://<bucket>/silver/historical/` | `gold/historical/` | Parquet |

Job 1 valida y normaliza las 19 columnas históricas, elimina duplicados
exactos y conserva diagnósticos. Job 2 agrupa por `Location`, `YEAR` y `MM`
para producir los indicadores documentados en `docs/data-dictionary.md`.

Los jobs se ejecutan mediante Step Functions con la integración
`glue:startJobRun.sync`. No deben ejecutarse directamente en producción sin
publicar primero los scripts y revisar la configuración resuelta.

## Publicación

Desde PowerShell:

```powershell
./publish-scripts.ps1 -BucketName <data-lake-bucket> -Region us-east-1
```

El publicador genera los dos scripts y `coffee-pipeline.zip`, que contiene el
código compartido de `src/common` y `src/pipeline`.