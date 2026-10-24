"""Glue Job 1: validate and write Bronze historical data to Silver."""

import argparse
import sys

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
    rows = [
        row.asDict(recursive=True)
        for row in dynamic_frame.toDF().collect()
    ]
    result = bronze_to_silver(rows)

    _write_json(glue_context, result.valid_rows, args['output_path'], True)
    _write_json(glue_context, result.rejected_rows, args['rejected_path'])
    _write_json(glue_context, result.duplicate_rows, args['duplicate_path'])
    job.commit()


def _write_json(glue_context, rows, path, partitioned=False):
    spark = glue_context.spark_session
    if rows:
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
    return vars(parser.parse_args())


if __name__ == '__main__':
    main()
