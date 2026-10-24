import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F


def main():
    args = getResolvedOptions(
        sys.argv,
        ['JOB_NAME', 'silver_path', 'gold_path', 'dataset_id'],
    )
    context = GlueContext(SparkContext.getOrCreate())
    spark = context.spark_session
    job = Job(context)
    job.init(args['JOB_NAME'], args)

    silver = spark.read.parquet(args['silver_path'])
    summary = (
        silver.groupBy('YEAR', 'MM', 'Location')
        .agg(
            F.count('*').alias('record_count'),
            F.avg('Temp_Max').alias('avg_temp_max'),
            F.avg('Temp_Min').alias('avg_temp_min'),
            F.avg('Humidity').alias('avg_humidity'),
            F.sum('Precipitation_mm').alias('total_precipitation_mm'),
            F.avg('Solar_Radiation').alias('avg_solar_radiation'),
            F.min('Date').alias('period_start'),
            F.max('Date').alias('period_end'),
        )
        .withColumn('dataset_id', F.lit(args['dataset_id']))
        .withColumn('generated_at', F.current_timestamp())
    )
    summary.write.mode('append').format('parquet').partitionBy(
        'YEAR', 'MM', 'Location').save(args['gold_path'])
    job.commit()


if __name__ == '__main__':
    main()
