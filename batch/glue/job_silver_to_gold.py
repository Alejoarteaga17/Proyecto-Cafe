"""Glue Job 2: aggregate validated Silver data into Gold."""

import argparse
import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext

sys.path.append('/opt/project')
from src.pipeline.transformations import silver_to_gold  # noqa: E402


def main():
    args = _arguments()
    spark_context = SparkContext()
    glue_context = GlueContext(spark_context)
    job = Job(glue_context)
    job.init(args['JOB_NAME'], args)

    frame = glue_context.create_dynamic_frame.from_options(
        connection_type='s3',
        connection_options={'paths': [args['input_path']], 'recurse': True},
        format='json',
    )
    summaries = silver_to_gold([
        row.asDict(recursive=True) for row in frame.collect()
    ])
    if summaries:
        glue_context.spark_session.createDataFrame(summaries).write.mode(
            'overwrite').partitionBy('YEAR', 'MM').parquet(args['output_path'])
    job.commit()


def _arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--JOB_NAME', required=True)
    parser.add_argument('--input_path', required=True)
    parser.add_argument('--output_path', required=True)
    return vars(parser.parse_args())


if __name__ == '__main__':
    main()
