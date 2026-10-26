# README

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

`Cultivo de Café Inteligente` es una plataforma para apoyar la toma de decisiones agronómicas en plantaciones de café. Integra datos históricos del cultivo con telemetría en tiempo real generada por sensores IoT, usando Amazon S3 como data lake medallion para almacenamiento analítico.

El proyecto sigue un enfoque de data engineering aplicado: validación, limpieza, particionado, ingestión en streaming, alertas agronómicas y diseño de pipelines serverless sobre AWS, manteniendo el mismo patrón de desacoplamiento y observabilidad para ambos flujos.

### Pipeline batch: datos históricos del café

El flujo batch recibe un CSV mediante API Gateway y una URL prefirmada. El archivo original se guarda en Bronze; los scripts Glue convierten y validan los datos hacia Silver y generan agregados Gold. La provisión automática de Glue, Step Functions, Data Catalog y Athena es una etapa pendiente de la IaC.



### Pipeline streaming: sensores de cultivo

Los sensores de cultivo publican mediciones de temperatura, humedad, radiación, pH del suelo y nutrientes vía MQTT. Las lecturas se validan contra reglas agronómicas y los mensajes inválidos se envían a una DLQ para revisión operativa.



### Observabilidad

Ambos flujos notifican eventos críticos mediante alarmas de CloudWatch y un topic de SNS. La alarma principal de negocio se activa cuando una DLQ acumula mensajes inválidos o fallidos, y el budget de AWS sirve como red de seguridad para evitar gastos fuera del rango razonable del proyecto.

### Estructura del repositorio

- **`batch/`**: flujo de ingestión histórica y validación de datos por lote.
  - Incluye su `serverless`, `src`, `database`, `tests` e infraestructura propia dentro de `batch/infrastructure`.
- **`batch/src/`**: contiene también los módulos de sensores heredados; su
  separación en un flujo streaming independiente queda pendiente.
- **`frontend/`**: interfaz ligera para pruebas de carga CSV y validación del backend.
- **`docs/`**: documentación y changelog del proyecto.
- **`quality-governance/`**: diccionario, catálogo, reglas de calidad, gobernanza y controles de calidad de código.
- **`.envs/`**: variables de entorno compartidas del proyecto.

La organización por flujo deja cada pipeline con su propio contexto funcional y su infraestructura asociada, sin depender de carpetas legacy del repositorio.

Con esta estructura ya no quedan carpetas duplicadas ni versiones paralelas del mismo proyecto.

Cada subproyecto tiene su propio README con el orden de despliegue y variables de entorno.

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
