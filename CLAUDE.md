# CLAUDE.md

## Proyecto activo

Este repositorio corresponde al proyecto `Cultivo de Café Inteligente`, una plataforma híbrida de data engineering para cultivo de café. El alcance activo mantiene el enfoque de:

- batch histórico con validación de datasets agrícolas
- streaming IoT con sensores sintéticos de cultivo
- medallion lake en S3 con capas Bronze/Silver/Gold
- MongoDB Atlas como base operativa de verdad
- Lambdas y SQS con alertas por DLQ y SNS

## Reglas de trabajo

- Todo el trabajo operativo, de desarrollo y despliegue debe ejecutarse dentro de contenedores Docker.
- La región AWS objetivo es `us-east-1`.
- El runtime base es Python 3.10.
- Se usa Serverless Framework para todos los despliegues de infraestructura.
- No se ejecutan comandos destructivos ni despliegues directos a producción.
- Se ignoran diseños previos basados en AppSync, DynamoDB o RDS para este alcance activo.

## Estructura

- `backend/`: Lambdas y stacks Serverless por flujo: `layers`, `batch`, `streaming`.
- `infrastructure/`: recursos compartidos: `storage`, `queue`, `secrets`, `iot`, `alerts`.
- `docs/`: diagramas de arquitectura generados con `python3 architecture.py`.

## Flujos activos

### Batch

- El usuario sube un CSV histórico del café a través de API Gateway.
- `ValidateAndStore` valida columnas y aplica imputación básica cuando faltan valores.
- El resultado se guarda en la capa Silver del data lake en S3.
- `SplitAndEnqueue` revalida y divide los registros antes de encolarlos.
- Los registros finales se validan y persisten en MongoDB Atlas.

### Streaming

- Los sensores publican métricas agronómicas por MQTT hacia IoT Core.
- Se enrutizan a SQS y luego se procesan con `PersistSensorReading`.
- La validación de negocio usa reglas agronómicas del café, con alertas de pH, suelo, temperatura, humedad y nutrientes.
- Los mensajes inválidos se envían a la DLQ para observabilidad.

## Reglas agronómicas clave

- pH del suelo: alerta si < 4.8 o > 6.5
- humedad del suelo: alerta si < 40% o > 85%
- temperatura: alerta si > 30 °C
- humedad relativa: alerta si > 90%
- nutrientes N/P/K: alertas cuando caen por debajo de los rangos fisiológicos

## Control de versiones

Los mensajes de commit deben seguir el estilo del proyecto:

- `feat:` para nuevas funcionalidades
- `fix:` para correcciones de lógica o IaC
- `core:` para refactors de arquitectura
- `docs:` para documentación y diagramas

## Verificación

La validación del proyecto debe hacerse con comandos ejecutados dentro del entorno Dockerizado del repositorio, nunca directamente en el host.
