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

Por defecto, el simulador solo imprime los eventos. Para publicarlos
automáticamente en AWS IoT Core, usa `--publish`:

```bash
python3 simulator/simulate_coffee_sensors.py \
  --publish --count 3 --seed 7 --interval 2
```

Para dejarlo ejecutándose temporalmente, omite `--count` y detenlo con
`Ctrl+C`:

```bash
python3 simulator/simulate_coffee_sensors.py --publish --interval 5
```

El topic predeterminado usa el sensor seleccionado, por ejemplo:

```text
sensors/coffee/ST-01/data
```

Puedes cambiar el Thing y el topic explícitamente:

```bash
python3 simulator/simulate_coffee_sensors.py \
  --publish \
  --thing-name coffee-cultivation-iot-sensor-simulator \
  --topic 'sensors/coffee/{sensor_id}/data' \
  --count 1
```

El modo `--publish` usa las credenciales AWS del contenedor y descubre
automáticamente el endpoint IoT Data ATS. La identidad IAM usada debe tener
permiso `iot:DescribeEndpoint` y `iot:Publish` para el topic. No es necesario
copiar manualmente el JSON en el MQTT test client.

## Despliegue y validación

El bucket debe existir previamente desde
`/app/batch/infrastructure/serverless/storage`. Después, desde este directorio:

```bash
serverless print --stage dev
serverless deploy --stage dev
```

El despliegue requiere autorización explícita y credenciales AWS configuradas.

El simulador valida cada evento antes de imprimirlo. Cada lectura se publica
en `sensors/coffee/<sensor-id>/data`; el `sensor_id` se obtiene de ese topic
mediante la regla IoT y no se incluye en el payload controlado por el cliente.
El procesamiento IoT se ejecuta manualmente desde su state machine separada:
IoT Glue Job 1 valida, deduplica por `sensor_id + timestamp` y escribe Silver
`YEAR/MM`; IoT Glue Job 2 escribe Gold Parquet agregado.

Para publicar respetando el sensor seleccionado, el simulador usa por defecto
el topic `sensors/coffee/<sensor-id>/data`. Si se usa `--topic`, debe ser una
plantilla que contenga `{sensor_id}`.

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
