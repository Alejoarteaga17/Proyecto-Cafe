import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql.types import BooleanType, DateType, DoubleType, IntegerType


REQUIRED_COLUMNS = [
    'LON', 'LAT', 'YEAR', 'MM', 'DD', 'DOY', 'Date', 'Temp_Max',
    'Temp_Min', 'Humidity', 'Solar_Radiation', 'Precipitation_mm',
    'Location', 'Close_USD_60kg', 'Is_Weekend', 'Is_Interpolated',
    'brl', 'cny', 'mxn',
]


def main():
    args = getResolvedOptions(
        sys.argv,
        ['JOB_NAME', 'input_path', 'silver_path', 'quarantine_path', 'dataset_id'],
    )
    context = GlueContext(SparkContext.getOrCreate())
    spark = context.spark_session
    job = Job(context)
    job.init(args['JOB_NAME'], args)

    source = spark.read.option('header', True).option('mode', 'PERMISSIVE').csv(
        args['input_path'])
    missing_columns = sorted(set(REQUIRED_COLUMNS) - set(source.columns))
    if missing_columns:
        raise ValueError(
            f'Missing required columns: {", ".join(missing_columns)}')

    typed = _cast_columns(source)
    valid_condition = _valid_condition(typed)
    valid = (
        typed.filter(valid_condition)
        .withColumn('dataset_id', F.lit(args['dataset_id']))
        .withColumn('ingested_at', F.current_timestamp())
    )
    invalid = (
        typed.filter(~valid_condition)
        .withColumn('dataset_id', F.lit(args['dataset_id']))
        .withColumn('ingested_at', F.current_timestamp())
        .withColumn('validation_error', F.lit('Invalid value or required field'))
    )

    valid.write.mode('append').format('parquet').partitionBy(
        'YEAR', 'MM', 'Location').save(args['silver_path'])
    invalid.write.mode('append').format('json').save(args['quarantine_path'])
    job.commit()


def _cast_columns(dataframe):
    numeric_double = [
        'LON', 'LAT', 'Temp_Max', 'Temp_Min', 'Humidity',
        'Solar_Radiation', 'Precipitation_mm', 'Close_USD_60kg',
        'brl', 'cny', 'mxn',
    ]
    numeric_int = ['YEAR', 'MM', 'DD', 'DOY']
    result = dataframe
    for column in numeric_double:
        result = result.withColumn(column, F.col(column).cast(DoubleType()))
    for column in numeric_int:
        result = result.withColumn(column, F.col(column).cast(IntegerType()))
    result = (
        result.withColumn('Date', F.to_date('Date'))
        .withColumn('Is_Weekend', _to_boolean('Is_Weekend'))
        .withColumn('Is_Interpolated', _to_boolean('Is_Interpolated'))
    )
    return result


def _to_boolean(column_name):
    normalized = F.lower(F.trim(F.col(column_name).cast('string')))
    return (
        F.when(normalized.isin('true', '1', 'yes'), F.lit(True))
        .when(normalized.isin('false', '0', 'no'), F.lit(False))
        .otherwise(F.lit(None).cast(BooleanType()))
    )


def _valid_condition(dataframe):
    numeric_columns = [
        'LON', 'LAT', 'YEAR', 'MM', 'DD', 'DOY', 'Date', 'Temp_Max',
        'Temp_Min', 'Humidity', 'Solar_Radiation', 'Precipitation_mm',
        'Location', 'Close_USD_60kg', 'Is_Weekend', 'Is_Interpolated',
        'brl', 'cny', 'mxn',
    ]
    condition = F.lit(True)
    for column in numeric_columns:
        condition = condition & F.col(column).isNotNull()
    condition = condition & (F.col('YEAR').between(1900, 2100))
    condition = condition & (F.col('MM').between(1, 12))
    condition = condition & (F.col('DD').between(1, 31))
    condition = condition & (F.col('DOY').between(1, 366))
    condition = condition & (F.col('Temp_Min') <= F.col('Temp_Max'))
    condition = condition & F.col('Humidity').between(0, 100)
    condition = condition & (F.col('Solar_Radiation') >= 0)
    condition = condition & (F.col('Precipitation_mm') >= 0)
    condition = condition & (F.length(F.trim(F.col('Location'))) > 0)
    for column in ('Close_USD_60kg', 'brl', 'cny', 'mxn'):
        condition = condition & (F.col(column) >= 0)
    return condition


if __name__ == '__main__':
    main()
