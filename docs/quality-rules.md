# Reglas de calidad

## Reglas batch implementadas

Ubicación: `batch/src/common/coffee_batch_validator.py`.

1. El archivo debe tener una fila de encabezados.
2. Deben existir las 19 columnas requeridas.
3. El archivo debe contener al menos una fila.
4. El batch no puede superar 300 filas en el validador Lambda legado.
5. `YEAR` debe estar entre 1900 y 2100.
6. `MM` debe estar entre 1 y 12.
7. `DD` debe estar entre 1 y 31.
8. `DOY` debe estar entre 1 y 366.
9. `Temp_Min` no puede superar `Temp_Max`.
10. `Humidity` debe estar entre 0 y 100.
11. `Solar_Radiation` y `Precipitation_mm` no pueden ser negativos.
12. `Location` no puede estar vacío.
13. `Close_USD_60kg`, `brl`, `cny` y `mxn` no pueden ser negativos.
14. Los campos numéricos deben convertirse correctamente a número.
15. Los campos enteros deben conservar valores enteros.

La API de URL prefirmada acepta únicamente nombres `.csv` y los tipos MIME
`text/csv`, `application/csv` y `application/vnd.ms-excel`.

## Reglas streaming implementadas

Ubicación: `batch/src/common/coffee_rules.py`.

1. `sensor_id`, `location` y `timestamp` son obligatorios.
2. `timestamp` debe ser ISO-8601 válido.
3. Las variables climáticas y `soil_ph` deben ser numéricas.
4. `nutrients_mg_kg` debe ser un objeto con `N`, `P` y `K` numéricos.
5. La humedad del suelo, si se envía, debe ser numérica.
6. pH inferior a 4.8 o superior a 6.5 genera alerta crítica.
7. Humedad del suelo inferior a 40% o superior a 85% genera alerta crítica.
8. Temperatura superior a 30 °C genera advertencia.
9. Humedad relativa superior a 90% genera advertencia.
10. N, P o K por debajo de sus umbrales genera advertencia.

## Reglas planificadas para Glue

Los scripts Glue deben conservar las reglas batch, separar registros válidos de
cuarentena y registrar métricas de filas leídas, válidas, rechazadas e
imputadas. Antes de declarar el pipeline productivo deben añadirse pruebas de
integración con un CSV válido y uno inválido.
