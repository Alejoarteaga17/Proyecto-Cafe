"""Glue Job 1: validate and write Bronze historical data to Silver."""

import argparse
import sys
from datetime import date

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
    return vars(parser.parse_args())


if __name__ == '__main__':
    main()
