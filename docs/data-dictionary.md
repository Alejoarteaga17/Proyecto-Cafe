# Diccionario de datos

## Histórico CSV

| Campo | Tipo normalizado | Unidad | Regla |
| --- | --- | --- | --- |
| `LON`, `LAT` | double | grados | numérico; longitud entre -180 y 180, latitud entre -90 y 90 |
| `YEAR`, `MM`, `DD`, `DOY` | integer | calendario | rangos 1900-2100, 1-12, 1-31, 1-366 |
| `Date` | string ISO date | fecha | requerido; consistente con `YEAR`, `MM`, `DD` y `DOY` |
| `Temp_Max`, `Temp_Min` | double | grados Celsius | `Temp_Min <= Temp_Max` |
| `Humidity` | double | porcentaje | 0-100 |
| `Solar_Radiation` | double | dataset original | finito y no negativo |
| `Precipitation_mm` | double | mm | no negativo |
| `Location` | string | ubicación | no vacío |
| `Close_USD_60kg`, `brl`, `cny`, `mxn` | double | moneda del campo | no negativo |
| `Is_Weekend`, `Is_Interpolated` | string/bool | indicador | normalizado por consumidor |

Todos los campos numéricos deben ser finitos; valores `NaN` o infinitos se
rechazan antes de escribir en Silver. Job 1 conserva los registros rechazados
y duplicados por `JOB_RUN_ID`, y publica un resumen de calidad por ejecución.

## Contratos de capas

- Bronze: CSV histórico crudo en `bronze/historical/` y eventos JSON comprimidos de IoT en `bronze/iot/`.
- Silver: JSON validado, deduplicado y particionado de forma estable por
  `YEAR` y `MM`; rechazos y duplicados conservados en prefijos separados. La
  estructura no cambia si una carga contiene un año o varios. Job 1 usa
  sobrescritura dinámica de particiones, por lo que reprocesar un `YEAR/MM`
  reemplaza ese período sin eliminar los demás.
- Gold: Parquet agregado por `Location`, `YEAR` y `MM`, con métricas de temperatura, humedad, precipitación, radiación y precio.

## IoT Bronze

| Campo | Tipo | Unidad | Regla |
| --- | --- | --- | --- |
| `sensor_id` | string | identificador | lo añade IoT Core desde el topic autorizado |
| `location` | string | lote | requerido |
| `timestamp` | string ISO-8601 | UTC | requerido y parseable |
| `Temp_Max`, `Temp_Min` | double | °C | numérico; mínimo no mayor que máximo |
| `Humidity` | double | porcentaje | 0-100 |
| `Solar_Radiation` | double | según sensor | no negativo |
| `Precipitation_mm` | double | mm | no negativo |
| `soil_ph` | double | pH | numérico |
| `soil_moisture` | double | porcentaje | 0-100 cuando se envía |
| `nutrients_mg_kg` | object | mg/kg | contiene `N`, `P` y `K` numéricos |

La validación estructural del evento se realiza en el simulador antes de
publicar. IoT Core deriva `sensor_id` de `sensors/coffee/<sensor-id>/data`
mediante la regla; Firehose solo entrega el evento y no realiza análisis
agronómico.

Los campos IoT (`sensor_id`, `location`, `timestamp`, `Temp_Max`, `Temp_Min`, `Humidity`, `Solar_Radiation`, `Precipitation_mm`, `soil_ph`, `soil_moisture`, `nutrients_mg_kg`) provienen del contrato existente en `streaming/streaming_src/common/coffee_rules.py`; sus umbrales agronómicos siguen siendo provisionales hasta ser confirmados por el requisito del proyecto.
