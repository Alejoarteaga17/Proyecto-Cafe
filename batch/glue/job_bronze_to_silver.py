"""Glue Job 1: validate and write Bronze historical data to Silver."""

import argparse
import sys
from datetime import date

import boto3
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext

sys.path.append('/opt/project')
from src.pipeline.transformations import bronze_to_silver  # noqa: E402


def main():
    args = _arguments()
    spark_context = SparkContext()
    glue_context = GlueContext(spark_context)
    job = Job(glue_context)
    job.init(args['JOB_NAME'], args)

    dynamic_frame = glue_context.create_dynamic_frame.from_options(
        connection_type='s3',
        connection_options={'paths': [args['input_path']], 'recurse': True},
        format='csv',
        format_options={'withHeader': True},
    )
    source_frame = dynamic_frame.toDF()
    rows = _iter_rows(source_frame)
    result = bronze_to_silver(rows)

    _write_json(glue_context, result.valid_rows, args['output_path'], True)
    run_id = args.get('JOB_RUN_ID', 'unknown')
    _write_json(
        glue_context, result.rejected_rows,
        _run_path(args['rejected_path'], run_id))
    _write_json(
        glue_context, result.duplicate_rows,
        _run_path(args['duplicate_path'], run_id))
    _write_quality_metrics(
        glue_context, args.get('quality_path'), run_id,
        len(result.valid_rows) + len(result.rejected_rows)
        + len(result.duplicate_rows),
        result)
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


def _write_quality_metrics(
        glue_context, path, run_id, input_count, result):
    if not path:
        return
    valid_rows = result.valid_rows
    partitions = sorted({
        (row['YEAR'], row['MM']) for row in valid_rows
    })
    dates = [
        date(row['YEAR'], row['MM'], row['DD']) for row in valid_rows
    ]
    metrics = [{
        'run_id': run_id,
        'input_count': input_count,
        'valid_count': len(valid_rows),
        'rejected_count': len(result.rejected_rows),
        'duplicate_count': len(result.duplicate_rows),
        'partition_count': len(partitions),
        'min_date': min(dates).isoformat() if dates else None,
        'max_date': max(dates).isoformat() if dates else None,
    }]
    _write_json(glue_context, metrics, _run_path(path, run_id))


def _write_json(glue_context, rows, path, partitioned=False):
    spark = glue_context.spark_session
    if rows:
        if partitioned:
            # Replace only the YEAR/MM partitions present in this run.
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
        partition_key = tuple(values)
        if partition_key in seen:
            continue
        seen.add(partition_key)
        partition_input = _partition_input(args, values)
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


def _partition_input(args, values):
    return {
        'Values': values,
        'StorageDescriptor': {
            'Columns': [
                {'Name': 'LON', 'Type': 'double'},
                {'Name': 'LAT', 'Type': 'double'},
                {'Name': 'DD', 'Type': 'int'},
                {'Name': 'DOY', 'Type': 'int'},
                {'Name': 'Date', 'Type': 'string'},
                {'Name': 'Temp_Max', 'Type': 'double'},
                {'Name': 'Temp_Min', 'Type': 'double'},
                {'Name': 'Humidity', 'Type': 'double'},
                {'Name': 'Solar_Radiation', 'Type': 'double'},
                {'Name': 'Precipitation_mm', 'Type': 'double'},
                {'Name': 'Location', 'Type': 'string'},
                {'Name': 'Close_USD_60kg', 'Type': 'double'},
                {'Name': 'Is_Weekend', 'Type': 'string'},
                {'Name': 'Is_Interpolated', 'Type': 'string'},
                {'Name': 'brl', 'Type': 'double'},
                {'Name': 'cny', 'Type': 'double'},
                {'Name': 'mxn', 'Type': 'double'},
            ],
            'Location': (
                f"{args['output_path'].rstrip('/')}/"
                f"YEAR={values[0]}/MM={values[1]}/"
            ),
            'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
            'OutputFormat': (
                'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
            ),
            'SerdeInfo': {
                'SerializationLibrary': 'org.openx.data.jsonserde.JsonSerDe',
            },
        },
    }


def _arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--JOB_NAME', required=True)
    parser.add_argument('--JOB_ID')
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
