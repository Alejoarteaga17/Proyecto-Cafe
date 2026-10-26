# Diccionario de datos

## Dataset histórico batch

Fuente: CSV histórico de café. La validación actual exige estas 19 columnas en
`batch/src/common/coffee_batch_validator.py`.

| Campo | Tipo Silver | Unidad/formato | Descripción |
|---|---|---|---|
| `LON` | double | grados decimales | Longitud geográfica |
| `LAT` | double | grados decimales | Latitud geográfica |
| `YEAR` | int | año | Año de la observación |
| `MM` | int | 1-12 | Mes de la observación |
| `DD` | int | 1-31 | Día del mes |
| `DOY` | int | 1-366 | Día del año |
| `Date` | date | ISO-8601 | Fecha de la observación |
| `Temp_Max` | double | °C | Temperatura máxima |
| `Temp_Min` | double | °C | Temperatura mínima |
| `Humidity` | double | porcentaje | Humedad relativa |
| `Solar_Radiation` | double | unidad del dataset | Radiación solar |
| `Precipitation_mm` | double | mm | Precipitación |
| `Location` | string | identificador | Ubicación de la observación |
| `Close_USD_60kg` | double | USD/60 kg | Precio de cierre |
| `Is_Weekend` | boolean | true/false | Indica si la fecha cae en fin de semana |
| `Is_Interpolated` | boolean | true/false | Indica si el valor fue interpolado |
| `brl` | double | moneda del dataset | Tasa o valor BRL |
| `cny` | double | moneda del dataset | Tasa o valor CNY |
| `mxn` | double | moneda del dataset | Tasa o valor MXN |

Metadatos añadidos por el pipeline:

| Campo | Tipo | Capa | Descripción |
|---|---|---|---|
| `dataset_id` | string | Silver/Gold | Identificador de la carga |
| `ingested_at` | timestamp | Silver | Momento de ingestión |
| `generated_at` | timestamp | Gold | Momento de generación del agregado |
| `validation_error` | string | Quarantine | Motivo de rechazo |

## Dataset streaming de sensores

El payload de sensores se valida en
`batch/src/common/coffee_rules.py` y contiene:

| Campo | Tipo | Unidad/formato | Obligatorio |
|---|---|---|---|
| `sensor_id` | string | identificador | Sí |
| `location` | string | identificador | Sí |
| `timestamp` | string | ISO-8601 | Sí |
| `Temp_Max` | number | °C | Sí |
| `Temp_Min` | number | °C | Sí |
| `Humidity` | number | porcentaje | Sí |
| `Solar_Radiation` | number | unidad del sensor | Sí |
| `Precipitation_mm` | number | mm | Sí |
| `soil_ph` | number | pH | Sí |
| `nutrients_mg_kg` | object | N, P y K en mg/kg | Sí |
| `soil_moisture` o `soil_moisture_pct` | number | porcentaje | Opcional |

Los campos `N`, `P` y `K` son propiedades del objeto
`nutrients_mg_kg`.
