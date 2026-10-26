"""Glue Job 2: aggregate validated Silver data into Gold."""

import argparse
import sys

import boto3
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql.functions import col, input_file_name, regexp_extract

sys.path.append('/opt/project')
from src.pipeline.transformations import silver_to_gold  # noqa: E402


def main():
    args = _arguments()
    spark_context = SparkContext()
    glue_context = GlueContext(spark_context)
    job = Job(glue_context)
    job.init(args['JOB_NAME'], args)

    frame = (
        glue_context.spark_session.read.json(args['input_path'])
        .withColumn('_source_path', input_file_name())
        .withColumn(
            'YEAR',
            regexp_extract(col('_source_path'), r'/YEAR=(\d+)(?:/|$)', 1)
            .cast('int'),
        )
        .withColumn(
            'MM',
            regexp_extract(col('_source_path'), r'/MM=(\d+)(?:/|$)', 1)
            .cast('int'),
        )
        .drop('_source_path')
    )
    summaries = silver_to_gold([
        row.asDict(recursive=True) for row in frame.collect()
    ])
    if summaries:
        glue_context.spark_session.createDataFrame(summaries).write.mode(
            'overwrite').partitionBy('YEAR', 'MM').parquet(args['output_path'])
        _register_partitions(args, summaries)
    job.commit()


def _register_partitions(args, summaries):
    glue = boto3.client('glue')
    partitions = []
    seen = set()
    for summary in summaries:
        values = [
            str(summary['YEAR']),
            str(summary['MM']),
        ]
        partition_key = tuple(values)
        if partition_key in seen:
            continue
        seen.add(partition_key)
        partitions.append({
            # Glue API requires partition values as strings, even for int keys.
            'Values': values,
            'StorageDescriptor': {
                'Columns': [
                    {'Name': 'Location', 'Type': 'string'},
                    {'Name': 'record_count', 'Type': 'bigint'},
                    {'Name': 'avg_temp_max', 'Type': 'double'},
                    {'Name': 'avg_temp_min', 'Type': 'double'},
                    {'Name': 'avg_humidity', 'Type': 'double'},
                    {'Name': 'total_precipitation_mm', 'Type': 'double'},
                    {'Name': 'avg_solar_radiation', 'Type': 'double'},
                    {'Name': 'avg_close_usd_60kg', 'Type': 'double'},
                ],
                'Location': (
                    f"{args['output_path'].rstrip('/')}/"
                    f"YEAR={values[0]}/MM={values[1]}/"
                ),
                'InputFormat': (
                    'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat'
                ),
                'OutputFormat': (
                    'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
                ),
                'SerdeInfo': {
                    'SerializationLibrary': (
                        'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
                    )
                },
            },
        })
    try:
        glue.batch_create_partition(
            DatabaseName=args['catalog_database'],
            TableName=args['catalog_table'],
            PartitionInputList=partitions,
        )
    except glue.exceptions.AlreadyExistsException:
        pass


def _arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--JOB_NAME', required=True)
    parser.add_argument('--JOB_ID')
    parser.add_argument('--JOB_RUN_ID')
    parser.add_argument('--input_path', required=True)
    parser.add_argument('--output_path', required=True)
    parser.add_argument('--catalog_database', required=True)
    parser.add_argument('--catalog_table', required=True)
    return vars(parser.parse_args())


if __name__ == '__main__':
    main()
