# README

> **Estado arquitectónico:** la arquitectura aprobada es Historical CSV -> API Gateway -> Lambda -> S3 Bronze; sensores simulados -> IoT Core -> Data Firehose -> S3 Bronze; Bronze -> Glue Job 1 -> Silver -> Glue Job 2 -> Gold -> Athena/QuickSight. Los componentes MongoDB, SQS, DLQ, Secrets Manager y SNS fueron eliminados del repositorio por pertenecer a la arquitectura anterior.

- [README](#readme)
  - [Resumen](#resumen)
    - [Pipeline batch: datos históricos del café](#pipeline-batch-datos-históricos-del-café)
    - [Pipeline streaming: sensores de cultivo](#pipeline-streaming-sensores-de-cultivo)
    - [Observabilidad](#observabilidad)
    - [Estructura del repositorio](#estructura-del-repositorio)
  - [Configuración](#configuración)
    - [Contenedor de desarrollo](#contenedor-de-desarrollo)
    - [Variables de entorno](#variables-de-entorno)
  - [Glosario](#glosario)
    - [Variables AWS: `.envs/aws.env`](#variables-aws-envsawsenv)
    - [Variables de Serverless: `.envs/sls.env`](#variables-de-serverless-envsslsenv)

---

## Resumen

`Cultivo de Café Inteligente` es una plataforma de datos para apoyar la toma de decisiones agronómicas en plantaciones de café. Integra datos históricos y telemetría IoT en un data lake S3 con capas Bronze, Silver y Gold.

El proyecto sigue un enfoque de data engineering aplicado: validación, limpieza, particionado, ingestión en streaming, alertas agronómicas y diseño de pipelines serverless sobre AWS, manteniendo el mismo patrón de desacoplamiento y observabilidad para ambos flujos.

### Pipeline batch: datos históricos del café

El flujo batch ingresa datasets históricos (CSV/Kaggle) mediante API Gateway y Lambda. Lambda valida el formato, columnas, filas y tamaño, y conserva el archivo crudo en S3 Bronze. Glue Job 1 limpia, valida, deduplica y particiona por `YEAR/MM`; Glue Job 2 agrega a Parquet en Gold.



### Pipeline streaming: sensores de cultivo

Los sensores simulados publican eventos vía MQTT a AWS IoT Core. Una regla los entrega directamente a Amazon Data Firehose, que los almacena en S3 Bronze con prefijos temporales y salida de errores configurada.



### Orquestación, consulta y alcance

Step Functions coordina Glue Job 1 y Glue Job 2 con reintentos y transición de
fallo. Athena consulta las tablas del Glue Data Catalog. QuickSight y la
automatización DataOps se mantienen como trabajo del sprint final; la
documentación no implica que exista un dashboard desplegado.

### Estructura del repositorio

- **`batch/`**: ingestión histórica, Glue Job 1/2, Step Functions, catálogo y
  pruebas del pipeline batch.
- **`streaming/`**: simulador IoT, contrato de sensores, pruebas e
  infraestructura IoT Core → Data Firehose → S3 Bronze.
- **`batch/infrastructure/serverless/data-platform/`**: Glue, Step Functions, Glue Data Catalog y Athena.
- **`frontend/`**: interfaz ligera para pruebas de carga CSV y validación del backend.
- **`docs/`**: diagramas de arquitectura generados con `python3 architecture.py`.
- **`docs/`**: arquitectura, contratos, diccionario, catálogo, lineage, RACI y estado de aceptación.
- **`batch/benchmarks/`**: consultas de Athena para comparar bytes escaneados y tiempo antes/después de las optimizaciones.

La carpeta `streaming/` contiene únicamente la implementación aprobada del
flujo IoT; no se recuperaron componentes legacy de diseños anteriores.

La organización por flujo deja cada pipeline con su propio contexto funcional y su infraestructura asociada, sin depender de carpetas legacy del repositorio.

El detalle de las optimizaciones S3/Athena, las consultas comparables y el
procedimiento para obtener `DataScannedInBytes` y
`TotalExecutionTimeInMillis` está en
[`docs/optimization-benchmark.md`](docs/optimization-benchmark.md). La
implementación está verificada en código/IaC; las métricas de rendimiento
requieren ejecutar las consultas en AWS y permanecen pendientes hasta contar
con ese resultado.

Con esta estructura ya no quedan carpetas duplicadas ni versiones paralelas del mismo proyecto.

Cada subproyecto tiene su propio README con el orden de despliegue y variables de entorno.

### Validación local

Desde el contenedor de desarrollo:

```bash
cd /app
python -m pytest -q batch/tests streaming/tests
```

El resultado local no verifica recursos AWS. Para validar plantillas, ejecutar
`serverless print --stage dev` dentro de cada stack aprobado, incluido
`/app/streaming/infrastructure/serverless/iot`, y revisar el plan antes de
desplegar. No se debe ejecutar un despliegue sin autorización explícita.

El estado detallado y la evidencia se mantienen en
[`docs/acceptance-checklist.md`](docs/acceptance-checklist.md). Los stacks
de los componentes excluidos de la arquitectura anterior fueron eliminados y no
deben reintroducirse.

---

## Configuración

### Contenedor de desarrollo

Estos pasos están pensados para trabajar con Visual Studio Code, pero puedes usar otra IDE siempre que mantengas la misma estructura dockerizada.

1. Instala la extensión `ms-vscode-remote.remote-containers`.
2. Abre la carpeta del proyecto en VS Code. La extensión detectará la configuración del contenedor y te pedirá volver a abrir el proyecto dentro del contenedor.

### Variables de entorno

En la carpeta `.envs` debes crear los archivos con las variables descritas en el glosario.

---

## Glosario

### Variables AWS: `.envs/aws.env`

- `AWS_ACCESS_KEY_ID`: clave de acceso para desplegar stacks en AWS.
- `AWS_SECRET_ACCESS_KEY`: clave secreta asociada a la anterior.
- `AWS_DEFAULT_REGION`: región objetivo del despliegue.
- `AWS_DEFAULT_OUTPUT`: formato de salida por defecto del CLI de AWS.

### Variables de Serverless: `.envs/sls.env`

- `SERVERLESS_ACCESS_KEY`: clave de acceso de Serverless Framework necesaria para despliegues y validaciones del CLI.
