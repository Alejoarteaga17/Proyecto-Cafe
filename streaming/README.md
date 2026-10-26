# Streaming IoT

El flujo streaming aprobado es:

```text
Simulated sensors -> AWS IoT Core -> Amazon Data Firehose -> S3 Bronze
```

Esta carpeta contiene únicamente los componentes IoT aprobados:

- `simulator/`: genera eventos JSON compatibles con el contrato de sensores.
- `streaming_src/common/coffee_rules.py`: valida eventos y calcula advertencias
  agronómicas provisionales.
- `tests/`: pruebas del contrato y del simulador.
- `infrastructure/serverless/iot/`: Thing, política IoT, regla y Firehose.

El stack `iot` declara un Thing para el simulador, una política de publicación,
una regla IoT y un delivery stream Firehose hacia `bronze/iot/`. La asociación
de un certificado X.509 al Thing requiere una operación de seguridad de la
cuenta AWS y no se afirma como desplegada por la definición IaC.

No se agrega un consumidor Lambda, SQS, DLQ, MongoDB, Kinesis Data Streams ni
otra base operativa.

## Ejecutar el simulador

Desde el contenedor:

```bash
cd /app/streaming
python3 simulator/simulate_coffee_sensors.py \
  --count 3 --seed 7 --interval 0
```

## Despliegue y validación

El bucket debe existir previamente desde
`/app/batch/infrastructure/serverless/storage`. Después, desde este directorio:

```bash
serverless print --stage dev
serverless deploy --stage dev
```

El despliegue requiere autorización explícita y credenciales AWS configuradas.

El simulador valida cada evento antes de imprimirlo. El `sensor_id` se obtiene
del topic MQTT `sensors/coffee/<sensor-id>/data` mediante la regla IoT y no se
incluye en el payload controlado por el cliente.

## Pruebas

```bash
cd /app
python3 -m pytest -q batch/tests streaming/tests
```

La prueba local no confirma recursos desplegados en AWS. Para validar la
infraestructura:

```bash
cd /app/streaming/infrastructure/serverless/iot
serverless print --stage dev
```

El stack necesita que el bucket S3 del stack `storage` exista y que sus nombres
estén disponibles en los parámetros SSM correspondientes.
