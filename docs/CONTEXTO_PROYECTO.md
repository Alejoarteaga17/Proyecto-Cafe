# Contexto completo del proyecto: Cultivo de Café Inteligente

## 1. Visión general

`Cultivo de Café Inteligente` es una plataforma híbrida de data engineering y observabilidad para apoyo a decisiones agronómicas en cultivos de café. El proyecto combina dos tipos de datos:

- datos históricos de producción y clima del cultivo, cargados por lotes
- telemetría en tiempo real generada por sensores IoT conectados a plantaciones

La idea central es unificar ambos flujos en una arquitectura basada en AWS Serverless, almacenamiento de datos con patrón medallón en S3 y MongoDB Atlas como fuente de verdad operativa para la persistencia final.

El enfoque del proyecto se alinea con principios de DataOps, CRISP-DM, DAMA-DMBOK y un diseño orientado a observabilidad, validación y alertas agronómicas.

---

## 2. Objetivos del negocio

El proyecto busca:

- detectar anomalías agronómicas tempranas en cultivos de café
- mantener un historial estructurado para análisis y reportes
- integrar sensores para supervisión continua
- contar con alertas por condiciones críticas de suelo, clima y nutrición
- construir una capa analítica reutilizable para dashboards y modelos de soporte a decisiones

Los cuatro pilares del sistema son:

1. ingestión batch de datos históricos
2. ingestión streaming desde sensores
3. validación y limpieza estructural de datos
4. persistencia operativa en MongoDB Atlas con alertas y DLQ para fallos

---

## 3. Datos que vamos a usar

### 3.1 Dataset batch histórico

Se maneja un dataset agronómico-histórico con estructura tipo CSV, inspirado en fuentes de agricultura y clima. Tiene 19 columnas clave:

- `LON`
- `LAT`
- `YEAR`
- `MM`
- `DD`
- `DOY`
- `Date`
- `Temp_Max`
- `Temp_Min`
- `Humidity`
- `Solar_Radiation`
- `Precipitation_mm`
- `Location`
- `Close_USD_60kg`
- `Is_Weekend`
- `Is_Interpolated`
- `brl`
- `cny`
- `mxn`

Este conjunto representa un registro histórico de condiciones climáticas y métricas económicas relacionadas con la producción de café.

### 3.2 Dataset streaming de sensores

Los sensores simulan métricas agronómicas emitidas por MQTT. La estructura base es la siguiente:

```json
{
  "sensor_id": "ST-01",
  "location": "Lote_Norte_Arabica",
  "timestamp": "2023-10-25T10:00:00Z",
  "Temp_Max": 23.5,
  "Temp_Min": 18.2,
  "Humidity": 68.0,
  "Solar_Radiation": 450.0,
  "Precipitation_mm": 0.0,
  "soil_ph": 5.5,
  "nutrients_mg_kg": {
    "N": 45.0,
    "P": 15.0,
    "K": 120.0
  }
}
```

Este payload incluye:

- identificador del sensor
- ubicación del lote
- timestamp de la lectura
- temperatura máxima y mínima
- humedad relativa
- radiación solar
- precipitación
- pH del suelo
- nutrientes N, P, K

### 3.3 Tipo de señales y dominio agronómico

El proyecto prioriza mediciones relacionadas con salud del cultivo:

- pH del suelo
- humedad del suelo
- temperatura ambiental
- humedad relativa
- radiación solar
- precipitación
- nutrientes del suelo

La validación del negocio usa reglas fisiológicas del café para decidir si una lectura debe considerarse normal o crítica.

---

## 4. Modelo de ingesta

### 4.1 Ingesta batch

Diseño principal:

- un usuario carga un CSV a través de API Gateway
- la Lambda `ValidateAndStore` valida la estructura del archivo
- si la validación falla, el archivo se rechaza con errores definidos
- si la validación pasa, se aplica limpieza básica y imputación de valores faltantes
- los datos se guardan en la capa Silver dentro de S3
- luego se transforma la data, se particiona y se mueve a Gold
- se divide la información y se envía a una cola SQS
- una Lambda de persistencia valida las filas finales y las almacena en MongoDB Atlas

Este flujo es ideal para datos históricos y analíticos de largo plazo.

### 4.2 Ingesta streaming

Diseño principal:

- los sensores publican mensajes vía MQTT a IoT Core
- los mensajes se enrutan a Amazon SQS
- una Lambda `PersistSensorReading` consume la cola
- la lectura se valida con reglas agronómicas
- si es válida, se persiste en MongoDB Atlas
- si falla, el mensaje se envía a una DLQ para observabilidad y alertas

Este flujo prioriza latencia baja y tolerancia a picos de tráfico.

### 4.3 Reglas de validación

Se siguen dos niveles de validación:

1. validación estructural de archivos/JSON
2. validación de negocio agronómica

La validación estructural revisa:

- columnas obligatorias
- tipos numéricos
- relaciones lógicas entre campos
- fechas y rangos válidos
- ausencia de campos críticos

La validación agronómica revisa:

- rangos fisiológicos del café
- condiciones de estrés hídrico
- toxicidad por pH
- riesgo de roya por humedad alta
- deficiencias de nutrientes

---

## 5. Arquitectura general

### 5.1 Arquitectura de capa de datos (medallion)

El data lake se estructura con patrón medallón sobre Amazon S3:

- Bronze: datos crudos, sin transformar, provenientes de datasets históricos y logs de MQTT
- Silver: datos limpiados, tipados, normalizados y validados
- Gold: datos curados, particionados y listos para análisis y persistencia final en MongoDB

La arquitectura del proyecto separa claramente:

- ingestión
- validación
- almacenamiento analítico
- persistencia transaccional
- observabilidad

### 5.2 Arquitectura AWS principal

Los servicios clave del stack son:

- API Gateway para ingreso batch
- Lambda para validación y persistencia
- S3 para almacenamiento del data lake
- SQS para desacoplar flujos y tratar picos de carga
- Secrets Manager para credenciales de MongoDB
- IoT Core para sensores MQTT
- CloudWatch para alarmas y métricas
- SNS para notificaciones por email
- MongoDB Atlas como fuente de verdad operativa

### 5.3 Decisiones de arquitectura críticas

El proyecto mantiene estas decisiones:

- todo está dockerizado
- desplegos con Serverless Framework
- región objetivo: `us-east-1`
- runtime base: Python 3.10
- MongoDB Atlas es la única fuente de verdad para ambos flujos
- no se usan AppSync ni DynamoDB en este alcance

---

## 6. Flujos del proyecto

### 6.1 Flujo batch: datos históricos

Secuencia:

1. Usuario sube CSV a API Gateway
2. `ValidateAndStore` valida columnas y filas
3. se aplican imputaciones y limpieza básica
4. resultado se guarda en S3 Silver
5. `TransformAndPartition` procesa datos y genera Gold
6. registros se dividen y se publican a una cola SQS
7. `ValidateAndPersist` valida y escribe a MongoDB Atlas
8. filas inválidas se despachan a DLQ
9. CloudWatch y SNS alertan sobre fallos o acu-mulación

Esto permite un pipeline ordenado, auditable y escalable para datos históricos.

### 6.2 Flujo streaming: sensores IoT

Secuencia:

1. sensores publican métricas por MQTT
2. IoT Core recibe los mensajes
3. el flujo se envía a una cola SQS
4. `PersistSensorReading` procesa cada evento
5. la lectura se valida con reglas del campo agronómico
6. si es válida, se guarda en MongoDB
7. si falla, se envía a DLQ y se activa alarma

Este flujo es crítico para detección de riesgo en tiempo real.

### 6.3 Relación entre ambos flujos

Ambos flujos comparten:

- la misma lógica de persistencia en MongoDB Atlas
- manejo de secretos por AWS Secrets Manager
- observabilidad por CloudWatch y SNS
- política de DLQ para fallos de negocio o infra

Esto garantiza un diseño profundamente consistente y operativamente comparable.

---

## 7. Reglas agronómicas clave

Las alertas del sistema están basadas en límites fisiológicos del café.

### 7.1 pH del suelo

Rango objetivo: `5.0 - 6.0`

- alerta si pH < 4.8
- alerta si pH > 6.5

Riesgos:

- ácido excesivo: toxicidad por aluminio
- alcalinidad excesiva: bloqueo de hierro y zinc

### 7.2 Humedad del suelo

Rango objetivo: `50% - 75%`

- alerta si < 40%
- alerta si > 85%

Riesgos:

- bajo nivel: estrés hídrico
- alto nivel: asfixia radicular y riesgo de hongos

### 7.3 Temperatura

Rango objetivo: `18 °C - 23 °C`

- alerta si temperatura > 30 °C

Riesgos:

- maduración prematura
- daño en taza del grano

### 7.4 Humedad relativa

Rango objetivo: `65% - 85%`

- alerta si > 90%

Riesgos:

- mayor riesgo de roya del café

### 7.5 Nutrientes N, P, K

Se validan niveles mínimos aceptables para nutrientes del suelo:

- N: umbral bajo de 25 mg/kg
- P: umbral bajo de 10 mg/kg
- K: umbral bajo de 80 mg/kg

Si están por debajo, se emite alerta por deficiencia nutricional.

---

## 8. Validación en código

El repositorio ya contiene reglas para validar tanto datos históricos como lecturas streaming.

### 8.1 Batch validation

Archivo: `backend/src/common/coffee_batch_validator.py`

Revisa:

- columnas faltantes
- tipos numéricos
- valores fuera de rango
- fechas inconsistentes
- relaciones entre `Temp_Min` y `Temp_Max`
- valores negativos no esperados
- ubicación vacía

También aplica un máximo de filas (`MAX_ROWS = 300`) para controlar volumen de entrada.

### 8.2 Reglas de alertas de cultivo

Archivo: `backend/src/common/coffee_rules.py`

Define:

- campos obligatorios del payload del sensor
- rangos objetivo por variable
- lógica de evaluación de alertas
- validación de estructura del objeto `nutrients_mg_kg`
- resumen final con estado `ok` o `alert`

---

## 9. Principios de persistencia y almacenamiento

### 9.1 MongoDB Atlas

MongoDB Atlas actúa como base operativa de verdad para:

- registros históricos validados
- lecturas streaming de sensores
- alertas agronómicas analíticas y de operación

La idea es que las Lambdas escriban primero en esta capa de verdad y que luego el análisis se desprenda de allí para dashboards y reportes.

### 9.2 Data lake en S3

El data lake está pensado para:

- guardar datos originales sin perder trazabilidad
- crear una capa limpia para análisis
- particionar por fecha y ubicación
- reutilizar datos para validación, transformaciones y curación

Esto permite separar claramente almacenamiento bruto y análisis listo para consumo.

---

## 10. Estructura del repositorio

El repositorio se organiza así:

- `backend/`: Lambdas y stacks Serverless por flujo
  - `layers/`: dependencias compartidas
  - `batch/`: validación y ETL batch
  - `streaming/`: ingestión en tiempo real
  - `src/`: lógica común, validadores y reglas agronómicas
- `infrastructure/`: recursos compartidos de AWS
  - `storage/`: S3
  - `queue/`: SQS y DLQ
  - `secrets/`: Secrets Manager
  - `iot/`: IoT Core
  - `alerts/`: CloudWatch, SNS y budgets
- `docs/`: diagramas y documentación arquitectónica
- `database/`: migraciones, seeders e índices de MongoDB

---

## 11. Reglas operativas del proyecto

### 11.1 Dockerización

Todo el trabajo debe ejecutarse dentro de contenedores Docker. Esto incluye:

- instalación de dependencias
- ejecución de Python
- despliegue de infra con Serverless Framework
- validación y testing del proyecto

### 11.2 AWS y despliegue

- región objetivo: `us-east-1`
- el runtime base es Python 3.10
- se usa Serverless Framework para IaC
- no se ejecutan despliegues destructivos ni cambios directos a producción

### 11.3 Control de versiones

Los mensajes de commit deben seguir el estilo del proyecto:

- `feat:` para nuevas funcionalidades
- `fix:` para correcciones
- `core:` para refactors de arquitectura
- `docs:` para documentación y diagramas

---

## 12. Resumen ejecutivo

El proyecto `Cultivo de Café Inteligente` busca crear una plataforma integrada para monitoreo, validación y análisis de cultivos de café usando:

- batch processing para datos históricos
- streaming IoT para lectura continua de sensores
- S3 medallion para almacenamiento analítico
- MongoDB Atlas como sistema operativo de verdad
- AWS Lambda, SQS, API Gateway, Secrets Manager, IoT Core, CloudWatch y SNS para el backend operable

La lógica de negocio y la infraestructura están construidas para que el sistema no solo recolecte datos, sino que también los valide, los interprete y alerte cuando una condición agronómica se vuelve crítica.

---

## 13. Referencias internas del proyecto

- README principal: `README.md`
- context de proyecto: `CLAUDE.md`
- diagramas de arquitectura: `docs/architecture.py`
- validación batch: `backend/src/common/coffee_batch_validator.py`
- reglas agronómicas: `backend/src/common/coffee_rules.py`
- backend de Serverless: `backend/serverless/`
- infraestructura AWS: `infrastructure/serverless/`

---

## 14. Conclusión

Este proyecto es una solución completa de data engineering aplicada al sector agroindustrial, orientada a producción de café. Su fuerza radica en combinar:

- datos históricos y streaming
- validación de negocio real
- integración de sensores IoT
- observabilidad operativa
- arquitectura serverless escalable
- almacenamiento analítico en capas

Todo esto permite generar una base sólida para dashboards, analítica agronómica y alertas de operación que apoyen decisiones concretas en el campo.
