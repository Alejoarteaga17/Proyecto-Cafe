-- Consultas para comparar el mismo resultado lógico antes y después de las
-- optimizaciones del data lake. Sustituir los valores de la plantilla antes
-- de ejecutarlas en Athena.
--
-- Parámetros:
--   <database>   Glue Data Catalog database
--   <year>       año existente en Gold
--   <month>      mes existente en Gold
--   <workgroup>  WorkGroup configurado para el proyecto

-- 1) Línea base: CSV Bronze sin particiones, con conversiones de tipo.
-- Esta consulta representa el costo de leer el archivo crudo completo.
SELECT
    CAST(YEAR AS integer) AS year,
    CAST(MM AS integer) AS month,
    COUNT(*) AS record_count
FROM "<database>"."coffee_historical_bronze"
WHERE CAST(YEAR AS integer) = <year>
  AND CAST(MM AS integer) = <month>
GROUP BY CAST(YEAR AS integer), CAST(MM AS integer);

-- 2) Particionado: mismo resultado lógico, leyendo únicamente YEAR/MM.
-- El predicado sobre las claves de partición permite partition pruning.
SELECT
    YEAR AS year,
    MM AS month,
    SUM(record_count) AS record_count
FROM "<database>"."coffee_historical_gold"
WHERE YEAR = <year>
  AND MM = <month>
GROUP BY YEAR, MM;

-- 3) Control de particionado: misma tabla Gold y mismo resultado, pero sin
-- predicate de partición. Debe leer todas las particiones disponibles.
SELECT
    YEAR AS year,
    MM AS month,
    SUM(record_count) AS record_count
FROM "<database>"."coffee_historical_gold"
GROUP BY YEAR, MM
HAVING YEAR = <year> AND MM = <month>;

-- 4) Control de formato/materialización: Gold Parquet contiene el resumen
-- persistido; la suma equivale al COUNT(*) de la línea base para el período.
-- Comparar esta consulta con la consulta 1 usando DataScannedInBytes y
-- TotalExecutionTimeInMillis. La comparación incluye Parquet y la
-- pre-agregación de Gold; no debe presentarse como una medición aislada de
-- Parquet si no se crea una tabla Parquet de detalle equivalente.
SELECT SUM(record_count) AS record_count
FROM "<database>"."coffee_historical_gold"
WHERE YEAR = <year>
  AND MM = <month>;
