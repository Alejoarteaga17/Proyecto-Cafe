# Diccionario de datos

## Histórico CSV

| Campo | Tipo normalizado | Unidad | Regla |
| --- | --- | --- | --- |
| `LON`, `LAT` | double | grados | numérico |
| `YEAR`, `MM`, `DD`, `DOY` | integer | calendario | rangos 1900-2100, 1-12, 1-31, 1-366 |
| `Date` | string ISO date | fecha | requerido |
| `Temp_Max`, `Temp_Min` | double | grados Celsius | `Temp_Min <= Temp_Max` |
| `Humidity` | double | porcentaje | 0-100 |
| `Solar_Radiation` | double | dataset original | no negativo |
| `Precipitation_mm` | double | mm | no negativo |
| `Location` | string | ubicación | no vacío |
| `Close_USD_60kg`, `brl`, `cny`, `mxn` | double | moneda del campo | no negativo |
| `Is_Weekend`, `Is_Interpolated` | string/bool | indicador | normalizado por consumidor |

## Contratos de capas

- Bronze: CSV histórico crudo en `bronze/historical/` y eventos JSON comprimidos de IoT en `bronze/iot/`.
- Silver: JSON validado, deduplicado y particionado por `YEAR` y `MM`; rechazos y duplicados conservados en prefijos separados.
- Gold: Parquet agregado por `Location`, `YEAR` y `MM`, con métricas de temperatura, humedad, precipitación, radiación y precio.

Los campos IoT (`sensor_id`, `location`, `timestamp`, `Temp_Max`, `Temp_Min`, `Humidity`, `Solar_Radiation`, `Precipitation_mm`, `soil_ph`, `soil_moisture`, `nutrients_mg_kg`) provienen del contrato existente en `batch/src/common/coffee_rules.py`; sus umbrales agronómicos siguen siendo provisionales hasta ser confirmados por el requisito del proyecto.
