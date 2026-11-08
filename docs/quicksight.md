# QuickSight

## Estado

`PARTIAL`: el repositorio contiene una configuración IaC opcional y un
contrato de dashboard, pero no se afirma que exista un recurso desplegado.
La configuración está desactivada por defecto para evitar crear recursos
account-specific sin autorización. En la cuenta de desarrollo autorizada, el
dashboard publicado contiene visuales nativos de QuickSight, no solo tablas.

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
`DIRECT_QUERY`; el dashboard visual requiere una definición account-specific.

## Validación requerida

1. Ejecutar una consulta Athena sobre `coffee_historical_gold`.
2. Activar la configuración con un principal autorizado.
3. Verificar que ambos datasets consultan las tablas Athena y reconocen
   `YEAR` y `MM` como particiones.
4. Crear el dashboard según el contrato y registrar ARN, propietario y fecha
   de validación.

## Validación realizada en la cuenta de desarrollo

Validación ejecutada en `us-east-1`, cuenta `688060219062`, el 2026-11-08:

- Suscripción QuickSight Enterprise y namespace `default`: disponibles.
- Fuente Athena: `coffee-cultivation-athena-dev`, estado
  `CREATION_SUCCESSFUL`.
- Dataset histórico: `coffee-cultivation-historical-gold-dev`,
  `DIRECT_QUERY`, tabla `coffee_historical_gold`.
- Dataset IoT: `coffee-cultivation-iot-gold-dev`, `DIRECT_QUERY`, tabla
  `coffee_iot_gold`.
- Dashboard: `coffee-cultivation-dashboard-dev`, versión 1,
  `CREATION_SUCCESSFUL`.
- Pestañas publicadas: `Histórico mensual` y `Sensores IoT`.
- Versión publicada: `3`, en estado `CREATION_SUCCESSFUL`.
- Visuales históricos: cuatro KPIs, dos líneas, una comparación de barras y
  una tabla de detalle.
- Visuales IoT: cuatro KPIs, una línea, dos comparaciones de barras y una tabla
  de detalle.
- Embedding web: `frontend/index.html` ofrece las pestañas de publicación CSV y
  dashboard en el mismo origen HTTP; obtiene una URL temporal mediante
  `GET /coffee-dashboard/embed-url` y carga el dashboard con el SDK oficial.
  `frontend/dashboard.html` conserva compatibilidad y redirige a la pestaña.

Para permitir que QuickSight ejecute consultas Athena sobre el bucket de
resultados del proyecto se añadió al rol administrado por QuickSight
`aws-quicksight-service-role-v0` una política específica para:

- `coffee-cultivation-coffee-data-lake-dev-aaccode/*`;
- la base Glue `coffee_cultivation` y sus tablas;
- consultas Athena y lectura/escritura de resultados.

La política debe mantenerse controlada por IAM y revisarse antes de replicar
la configuración en otra cuenta. El dashboard se creó mediante AWS CLI porque
la definición visual depende del usuario/namespace de QuickSight; el contrato
reproducible permanece en
[`quicksight-dashboard-definition.json`](quicksight-dashboard-definition.json).

La API de embedding requiere la API Key del stack batch y no expone
credenciales AWS en el navegador. La URL generada expira según
`QUICKSIGHT_SESSION_LIFETIME_MINUTES` y no debe guardarse en código,
documentación ni almacenamiento permanente.