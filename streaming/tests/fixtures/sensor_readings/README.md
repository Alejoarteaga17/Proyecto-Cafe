# Sensor reading fixtures

Payloads de ejemplo para el pipeline de sensores del cultivo. Puedes publicarlos desde la consola de IoT Core o usando el cliente MQTT real con certificado mTLS.

1. **AWS IoT Core console**: usa el cliente MQTT integrado y publica a un tópico como `sensors/coffee/sensor-001/data`.
2. **`../../sensor_readings/send_sensor_reading.sh`**: usa certificado X.509 real del sensor para validar el canal mTLS.

| File | Resultado esperado |
| --- | --- |
| `valid_reading.json` | Se persiste en MongoDB Atlas con la medida del sensor |
| `invalid_location.json` | Se envía a la DLQ por ubicación vacía |
| `invalid_temperature.json` | Se envía a la DLQ por temperatura no numérica |

Tras publicar un mensaje inválido, revisa los logs de `PersistSensorReading` o el conteo de mensajes en la DLQ.

Nota: estos payloads no llevan `sensor_id` intencionalmente; el entorno autorizado del tema establece la identidad del sensor y la Lambda la incorpora de forma segura antes de validar y persistir.
