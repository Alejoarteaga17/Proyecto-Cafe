"""Glue Job IoT 2: aggregate validated Silver readings into Gold."""

import argparse
import sys

import boto3
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql.functions import col, input_file_name, regexp_extract

sys.path.append('/opt/project')
from streaming_src.pipeline.transformations import silver_to_gold  # noqa: E402


def main():
    args = _arguments()
    context = GlueContext(SparkContext())
    job = Job(context)
    job.init(args['JOB_NAME'], args)
    frame = (
        context.spark_session.read.json(args['input_path'])
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
    summaries = silver_to_gold(_iter_rows(frame))
    if summaries:
        context.spark_session.conf.set(
            'spark.sql.sources.partitionOverwriteMode', 'dynamic')
        context.spark_session.createDataFrame(summaries).write.mode(
            'overwrite').partitionBy('YEAR', 'MM').parquet(args['output_path'])
        _register_partitions(args, summaries)
    job.commit()


def _iter_rows(frame):
    iterator = getattr(frame, 'toLocalIterator', None)
    if iterator is not None:
        return (row.asDict(recursive=True) for row in iterator())
    return (row.asDict(recursive=True) for row in frame.collect())


def _register_partitions(args, summaries):
    glue = boto3.client('glue')
    seen = set()
    for summary in summaries:
        values = [str(summary['YEAR']), str(summary['MM'])]
        if tuple(values) in seen:
            continue
        seen.add(tuple(values))
        partition_input = {
            'Values': values,
            'StorageDescriptor': {
                'Columns': _gold_columns(),
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
                    ),
                },
            },
        }
        try:
            glue.create_partition(
                DatabaseName=args['catalog_database'],
                TableName=args['catalog_table'],
                PartitionInput=partition_input,
            )
        except glue.exceptions.AlreadyExistsException:
            glue.update_partition(
                DatabaseName=args['catalog_database'],
                TableName=args['catalog_table'],
                PartitionValueList=values,
                PartitionInput=partition_input,
            )


def _gold_columns():
    return [
        {'Name': 'sensor_id', 'Type': 'string'},
        {'Name': 'location', 'Type': 'string'},
        {'Name': 'record_count', 'Type': 'bigint'},
        {'Name': 'avg_temp_max', 'Type': 'double'},
        {'Name': 'avg_temp_min', 'Type': 'double'},
        {'Name': 'avg_humidity', 'Type': 'double'},
        {'Name': 'avg_solar_radiation', 'Type': 'double'},
        {'Name': 'total_precipitation_mm', 'Type': 'double'},
        {'Name': 'avg_soil_ph', 'Type': 'double'},
        {'Name': 'avg_soil_moisture', 'Type': 'double'},
        {'Name': 'avg_n', 'Type': 'double'},
        {'Name': 'avg_p', 'Type': 'double'},
        {'Name': 'avg_k', 'Type': 'double'},
    ]


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
