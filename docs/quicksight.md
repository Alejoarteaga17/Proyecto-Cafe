# QuickSight

## Estado

`PARTIAL`: el repositorio contiene una configuración IaC opcional y un
contrato de dashboard, pero no se afirma que exista un recurso desplegado.
La configuración está desactivada por defecto para evitar crear recursos
account-specific sin autorización.

## Configuración objetivo

- Fuente: Amazon Athena.
- Workgroup: `${service}-gold-${stage}`.
- Database: `coffee_cultivation` (parametrizable por `GLUE_DATABASE_NAME`).
- Tables: `coffee_historical_gold` y `coffee_iot_gold`.
- S3 result location: `s3://<data-lake>/athena-results/`.
- Permisos mínimos: QuickSight debe consultar Athena, Glue Data Catalog y la ubicación Gold/resultados S3 mediante un rol administrado en la cuenta.
- IaC: [`batch/infrastructure/serverless/data-platform/quicksight.yml`](../batch/infrastructure/serverless/data-platform/quicksight.yml).
- Contrato de dashboard: [`quicksight-dashboard-definition.json`](quicksight-dashboard-definition.json).

## Activación controlada

El stack `data-platform` recibe `QuickSightEnabled=false` por defecto. Para
activarlo se necesita un `QuickSightPrincipalArn` válido y una revisión de
costos/permisos. La activación crea una fuente Athena y dos datasets en modo
`DIRECT_QUERY`; no crea automáticamente un dashboard visual completo.

## Validación requerida

1. Ejecutar una consulta Athena sobre `coffee_historical_gold`.
2. Activar la configuración con un principal autorizado.
3. Verificar que ambos datasets consultan las tablas Athena y reconocen
   `YEAR` y `MM` como particiones.
4. Crear el dashboard según el contrato y registrar ARN, propietario y fecha
   de validación.