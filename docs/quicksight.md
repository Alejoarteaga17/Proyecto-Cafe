# QuickSight

## Estado

`DEFERRED TO FINAL SPRINT`: la arquitectura reserva QuickSight para consumo analítico, pero este checkout no contiene un AWS account ID, namespace, user ARN ni dashboard desplegado. No se afirma que exista un dashboard.

## Configuración objetivo

- Fuente: Amazon Athena.
- Workgroup: `${service}-gold-${stage}`.
- Database: `coffee_cultivation` (parametrizable por `GLUE_DATABASE_NAME`).
- Table: `coffee_historical_gold`.
- S3 result location: `s3://<data-lake>/athena-results/`.
- Permisos mínimos: QuickSight debe consultar Athena, Glue Data Catalog y la ubicación Gold/resultados S3 mediante un rol administrado en la cuenta.

## Validación requerida

1. Ejecutar una consulta Athena sobre `coffee_historical_gold`.
2. Crear el data source Athena en el namespace autorizado.
3. Crear el dataset y verificar que `YEAR` y `MM` se reconocen como particiones.
4. Crear el dashboard y registrar ARN, propietario y fecha de validación.