# Glue ETL

`bronze_to_silver.py` reads the original historical CSV from Bronze, validates
and types its columns, writes valid records as partitioned Parquet in Silver,
and writes rejected records as JSON in the quarantine prefix.

`silver_to_gold.py` aggregates Silver by year, month and location and writes
the analytical result as partitioned Parquet in Gold.

The jobs are intentionally independent of MongoDB. Glue receives paths and the
dataset identifier as job arguments from Step Functions.
