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

`Cultivo de Café Inteligente` es una plataforma híbrida para apoyar la toma de decisiones agronómicas en plantaciones de café. Integra datos históricos del cultivo con telemetría en tiempo real generada por sensores IoT, usando MongoDB Atlas como fuente de verdad operativa y Amazon S3 con patrón medallón para almacenamiento analítico.

El proyecto sigue un enfoque de data engineering aplicado: validación, limpieza, particionado, ingestión en streaming, alertas agronómicas y diseño de pipelines serverless sobre AWS, manteniendo el mismo patrón de desacoplamiento y observabilidad para ambos flujos.

### Pipeline batch: datos históricos del café

El flujo batch ingresa datasets históricos (CSV/Kaggle) mediante un endpoint REST en API Gateway. La validación inicial exige las 19 columnas del dataset de café, aplica imputación cuando faltan valores como `Solar_Radiation` y guarda el resultado en la capa Silver del data lake. Luego una segunda etapa realiza particionado por `YEAR/MM/Location` y produce la capa Gold para análisis y persistencia.



### Pipeline streaming: sensores de cultivo

Los sensores de cultivo publican mediciones de temperatura, humedad, radiación, pH del suelo y nutrientes vía MQTT. Las lecturas se validan contra reglas agronómicas del café antes de persistirse en MongoDB Atlas. Si un mensaje falla, se envía a una DLQ para revisión operativa y alertas por CloudWatch/SNS.



### Observabilidad

Ambos flujos notifican eventos críticos mediante alarmas de CloudWatch y un topic de SNS. La alarma principal de negocio se activa cuando una DLQ acumula mensajes inválidos o fallidos, y el budget de AWS sirve como red de seguridad para evitar gastos fuera del rango razonable del proyecto.

### Estructura del repositorio

- **`backend/`**: código Python de las Lambdas y stacks Serverless por hilo funcional: `layers`, `batch`, `streaming`.
- **`infrastructure/`**: recursos compartidos de AWS por stack: `storage`, `queue`, `secrets`, `iot`, `alerts`.
- **`docs/`**: diagramas de arquitectura generados con `python3 architecture.py`.

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
