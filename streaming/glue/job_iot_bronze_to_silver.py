"""Glue Job IoT 1: validate, normalize and deduplicate Bronze readings."""

import argparse
import sys

import boto3
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext

sys.path.append('/opt/project')
from streaming_src.pipeline.transformations import bronze_to_silver  # noqa: E402


def main():
    args = _arguments()
    context = GlueContext(SparkContext())
    job = Job(context)
    job.init(args['JOB_NAME'], args)

    frame = context.spark_session.read.json(args['input_path'])
    result = bronze_to_silver(_iter_rows(frame))
    _write_json(context, result.valid_rows, args['output_path'], True)
    run_id = args.get('JOB_RUN_ID', 'unknown')
    _write_json(context, result.rejected_rows,
                _run_path(args['rejected_path'], run_id))
    _write_json(context, result.duplicate_rows,
                _run_path(args['duplicate_path'], run_id))
    _write_quality(context, args.get('quality_path'), run_id, result)
    if result.valid_rows:
        _register_partitions(args, result.valid_rows)
    job.commit()


def _iter_rows(frame):
    iterator = getattr(frame, 'toLocalIterator', None)
    if iterator is not None:
        return (row.asDict(recursive=True) for row in iterator())
    return (row.asDict(recursive=True) for row in frame.collect())


def _run_path(path, run_id):
    return f"{path.rstrip('/')}/run_id={run_id}/"


def _write_quality(context, path, run_id, result):
    if not path:
        return
    metrics = [{
        'run_id': run_id,
        'input_count': (
            len(result.valid_rows) + len(result.rejected_rows)
            + len(result.duplicate_rows)
        ),
        'valid_count': len(result.valid_rows),
        'rejected_count': len(result.rejected_rows),
        'duplicate_count': len(result.duplicate_rows),
        'partition_count': len({
            (row['YEAR'], row['MM']) for row in result.valid_rows
        }),
    }]
    _write_json(context, metrics, _run_path(path, run_id))


def _write_json(context, rows, path, partitioned=False):
    if not rows:
        return
    spark = context.spark_session
    if partitioned:
        spark.conf.set(
            'spark.sql.sources.partitionOverwriteMode', 'dynamic')
    writer = spark.createDataFrame(rows).write.mode('overwrite')
    if partitioned:
        writer = writer.partitionBy('YEAR', 'MM')
    writer.json(path)


def _register_partitions(args, rows):
    glue = boto3.client('glue')
    seen = set()
    for row in rows:
        values = [str(row['YEAR']), str(row['MM'])]
        if tuple(values) in seen:
            continue
        seen.add(tuple(values))
        partition_input = {
            'Values': values,
            'StorageDescriptor': {
                'Columns': _silver_columns(),
                'Location': (
                    f"{args['output_path'].rstrip('/')}/"
                    f"YEAR={values[0]}/MM={values[1]}/"
                ),
                'InputFormat': (
                    'org.apache.hadoop.mapred.TextInputFormat'
                ),
                'OutputFormat': (
                    'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
                ),
                'SerdeInfo': {
                    'SerializationLibrary': (
                        'org.openx.data.jsonserde.JsonSerDe'
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


def _silver_columns():
    return [
        {'Name': 'sensor_id', 'Type': 'string'},
        {'Name': 'location', 'Type': 'string'},
        {'Name': 'timestamp', 'Type': 'string'},
        {'Name': 'Temp_Max', 'Type': 'double'},
        {'Name': 'Temp_Min', 'Type': 'double'},
        {'Name': 'Humidity', 'Type': 'double'},
        {'Name': 'Solar_Radiation', 'Type': 'double'},
        {'Name': 'Precipitation_mm', 'Type': 'double'},
        {'Name': 'soil_ph', 'Type': 'double'},
        {'Name': 'soil_moisture', 'Type': 'double'},
        {'Name': 'n', 'Type': 'double'},
        {'Name': 'p', 'Type': 'double'},
        {'Name': 'k', 'Type': 'double'},
    ]


def _arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--JOB_NAME', required=True)
    parser.add_argument('--JOB_RUN_ID')
    parser.add_argument('--input_path', required=True)
    parser.add_argument('--output_path', required=True)
    parser.add_argument('--rejected_path', required=True)
    parser.add_argument('--duplicate_path', required=True)
    parser.add_argument('--quality_path')
    parser.add_argument('--catalog_database', required=True)
    parser.add_argument('--catalog_table', required=True)
    return vars(parser.parse_args())


if __name__ == '__main__':
    main()
