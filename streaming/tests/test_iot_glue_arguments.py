import importlib.util
import sys
import types
from pathlib import Path


GLUE_DIR = Path(__file__).resolve().parents[1] / 'glue'


def _load(filename, monkeypatch):
    fake_awsglue = types.ModuleType('awsglue')
    fake_context = types.ModuleType('awsglue.context')
    fake_context.GlueContext = object
    fake_job = types.ModuleType('awsglue.job')
    fake_job.Job = object
    fake_spark_context = types.ModuleType('pyspark.context')
    fake_spark_context.SparkContext = object
    fake_functions = types.ModuleType('pyspark.sql.functions')
    fake_functions.col = lambda name: name
    fake_functions.input_file_name = lambda: ''
    fake_functions.regexp_extract = lambda *args: ''
    fake_sql = types.ModuleType('pyspark.sql')
    fake_sql.functions = fake_functions
    fake_boto3 = types.ModuleType('boto3')
    fake_boto3.client = lambda name: None
    for name, module in {
        'awsglue': fake_awsglue,
        'awsglue.context': fake_context,
        'awsglue.job': fake_job,
        'pyspark': types.ModuleType('pyspark'),
        'pyspark.context': fake_spark_context,
        'pyspark.sql': fake_sql,
        'pyspark.sql.functions': fake_functions,
        'boto3': fake_boto3,
    }.items():
        monkeypatch.setitem(sys.modules, name, module)

    spec = importlib.util.spec_from_file_location(
        f'test_{filename}', GLUE_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_iot_job_one_accepts_glue_job_id(monkeypatch):
    module = _load('job_iot_bronze_to_silver.py', monkeypatch)
    monkeypatch.setattr(sys, 'argv', [
        'job.py', '--JOB_NAME', 'iot-one', '--JOB_ID', 'id',
        '--JOB_RUN_ID', 'run', '--input_path', 'in',
        '--output_path', 'out', '--rejected_path', 'reject',
        '--duplicate_path', 'duplicate', '--catalog_database', 'coffee',
        '--catalog_table', 'silver',
    ])

    assert module._arguments()['JOB_ID'] == 'id'


def test_iot_job_two_accepts_glue_job_id(monkeypatch):
    module = _load('job_iot_silver_to_gold.py', monkeypatch)
    monkeypatch.setattr(sys, 'argv', [
        'job.py', '--JOB_NAME', 'iot-two', '--JOB_ID', 'id',
        '--JOB_RUN_ID', 'run', '--input_path', 'in',
        '--output_path', 'out', '--catalog_database', 'coffee',
        '--catalog_table', 'gold',
    ])

    assert module._arguments()['JOB_ID'] == 'id'
