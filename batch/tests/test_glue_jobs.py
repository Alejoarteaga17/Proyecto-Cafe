import importlib.util
import sys
import types
from pathlib import Path


GLUE_DIR = Path(__file__).resolve().parents[1] / 'glue'


class _Writer:
    def __init__(self):
        self.calls = []

    def mode(self, value):
        self.calls.append(('mode', value))
        return self

    def partitionBy(self, *columns):
        self.calls.append(('partitionBy', columns))
        return self

    def json(self, path):
        self.calls.append(('json', path))

    def parquet(self, path):
        self.calls.append(('parquet', path))


class _DataFrame:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.write = _Writer()

    def collect(self):
        return self.rows

    def withColumn(self, *_args):
        return self

    def drop(self, *_args):
        return self


class _Spark:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.read = self
        self.created = []
        self.conf = types.SimpleNamespace(
            values={},
            set=lambda key, value: self.conf.values.update({key: value}),
        )

    def json(self, _path):
        return _DataFrame(self.rows)

    def createDataFrame(self, rows):
        frame = _DataFrame()
        self.created.append((rows, frame))
        return frame


class _FakeJob:
    last = None

    def __init__(self, _context):
        self.initialized = None
        self.committed = False
        _FakeJob.last = self

    def init(self, name, args):
        self.initialized = (name, args)

    def commit(self):
        self.committed = True


def _install_glue_modules(monkeypatch, spark=None):
    spark = spark or _Spark()

    class FakeGlueContext:
        def __init__(self, _context):
            self.spark_session = spark
            self.create_dynamic_frame = types.SimpleNamespace(
                from_options=lambda **_kwargs: types.SimpleNamespace(
                    toDF=lambda: _DataFrame([])
                )
            )

    fake_context = types.ModuleType('awsglue.context')
    fake_context.GlueContext = FakeGlueContext
    fake_job = types.ModuleType('awsglue.job')
    fake_job.Job = _FakeJob
    fake_spark_context = types.ModuleType('pyspark.context')
    fake_spark_context.SparkContext = lambda: object()
    fake_spark_functions = types.ModuleType('pyspark.sql.functions')

    class _Expression:
        def cast(self, _type):
            return self

    fake_spark_functions.col = lambda _name: _Expression()
    fake_spark_functions.input_file_name = lambda: _Expression()
    fake_spark_functions.regexp_extract = lambda *_args: _Expression()
    fake_sql = types.ModuleType('pyspark.sql')
    fake_sql.functions = fake_spark_functions
    fake_boto3 = types.ModuleType('boto3')
    fake_boto3.client = lambda _name: None

    monkeypatch.setitem(sys.modules, 'awsglue', types.ModuleType('awsglue'))
    monkeypatch.setitem(sys.modules, 'awsglue.context', fake_context)
    monkeypatch.setitem(sys.modules, 'awsglue.job', fake_job)
    monkeypatch.setitem(sys.modules, 'pyspark', types.ModuleType('pyspark'))
    monkeypatch.setitem(sys.modules, 'pyspark.context', fake_spark_context)
    monkeypatch.setitem(sys.modules, 'pyspark.sql', fake_sql)
    monkeypatch.setitem(sys.modules, 'pyspark.sql.functions', fake_spark_functions)
    monkeypatch.setitem(sys.modules, 'boto3', fake_boto3)
    return spark


def _load_module(monkeypatch, filename, module_name):
    _install_glue_modules(monkeypatch)
    spec = importlib.util.spec_from_file_location(
        module_name, GLUE_DIR / filename
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_job_one_arguments_and_write_json(monkeypatch):
    module = _load_module(monkeypatch, 'job_bronze_to_silver.py', 'job_one_test')
    monkeypatch.setattr(
        sys,
        'argv',
        [
            'job.py', '--JOB_NAME', 'job-one', '--JOB_ID', 'id',
            '--JOB_RUN_ID', 'run', '--input_path', 'in',
            '--output_path', 'out', '--rejected_path', 'reject',
            '--duplicate_path', 'duplicate', '--catalog_database', 'coffee',
            '--catalog_table', 'silver',
        ],
    )

    args = module._arguments()
    assert args['JOB_NAME'] == 'job-one'
    assert args['JOB_ID'] == 'id'

    spark = types.SimpleNamespace(
        spark_session=_Spark()
    )
    module._write_json(spark, [{'YEAR': 2026, 'MM': 8}], 'out', True)
    writer = spark.spark_session.created[0][1].write
    assert ('partitionBy', ('YEAR', 'MM')) in writer.calls
    assert ('json', 'out') in writer.calls
    assert spark.spark_session.conf.values == {
        'spark.sql.sources.partitionOverwriteMode': 'dynamic',
    }


def test_job_one_write_json_skips_empty_rows(monkeypatch):
    module = _load_module(monkeypatch, 'job_bronze_to_silver.py', 'job_one_empty')
    spark = types.SimpleNamespace(spark_session=_Spark())

    module._write_json(spark, [], 'out')

    assert spark.spark_session.created == []


def test_job_one_iter_rows_uses_incremental_iterator(monkeypatch):
    module = _load_module(monkeypatch, 'job_bronze_to_silver.py', 'job_one_iter')

    class Frame:
        def toLocalIterator(self):
            return iter([
                types.SimpleNamespace(asDict=lambda recursive=True: {'id': 1}),
            ])

        def collect(self):
            raise AssertionError('collect should not be used when available')

    assert list(module._iter_rows(Frame())) == [{'id': 1}]


def test_job_one_main_reads_transforms_and_commits(monkeypatch):
    module = _load_module(monkeypatch, 'job_bronze_to_silver.py', 'job_one_main')
    args = {
        'JOB_NAME': 'job-one',
        'input_path': 's3://in',
        'output_path': 's3://out',
        'rejected_path': 's3://reject',
        'duplicate_path': 's3://duplicate',
        'catalog_database': 'coffee',
        'catalog_table': 'silver',
    }
    source_rows = [types.SimpleNamespace(
        asDict=lambda recursive=True: {'YEAR': 2026, 'MM': 8}
    )]
    source = types.SimpleNamespace(
        toDF=lambda: _DataFrame(source_rows)
    )
    spark = _Spark()

    class Context:
        def __init__(self, _context):
            self.spark_session = spark
            self.create_dynamic_frame = types.SimpleNamespace(
                from_options=lambda **_kwargs: source
            )

    result = types.SimpleNamespace(
        valid_rows=[{'YEAR': 2026, 'MM': 8}],
        rejected_rows=[],
        duplicate_rows=[],
    )
    monkeypatch.setattr(module, '_arguments', lambda: args)
    monkeypatch.setattr(module, 'GlueContext', Context)
    monkeypatch.setattr(module, 'bronze_to_silver', lambda rows: result)
    monkeypatch.setattr(module, '_register_partitions', lambda *_args: None)

    module.main()

    assert _FakeJob.last.initialized == ('job-one', args)
    assert _FakeJob.last.committed is True
    assert spark.created[0][1].write.calls[-1] == ('json', 's3://out')


def test_job_one_registers_and_updates_unique_partitions(monkeypatch):
    module = _load_module(
        monkeypatch, 'job_bronze_to_silver.py', 'job_one_partitions')

    class GlueClient:
        class exceptions:
            class AlreadyExistsException(Exception):
                pass

        def __init__(self):
            self.created = []
            self.updated = []

        def create_partition(self, **kwargs):
            self.created.append(kwargs)

        def update_partition(self, **kwargs):
            self.updated.append(kwargs)

    client = GlueClient()
    monkeypatch.setattr(
        module, 'boto3', types.SimpleNamespace(client=lambda _name: client))
    args = {
        'catalog_database': 'coffee',
        'catalog_table': 'silver',
        'output_path': 's3://bucket/silver/historical/',
    }
    rows = [
        {'YEAR': 2024, 'MM': 1},
        {'YEAR': 2024, 'MM': 1},
        {'YEAR': 2025, 'MM': 3},
    ]

    module._register_partitions(args, rows)

    assert len(client.created) == 2
    assert client.created[0]['PartitionInput']['Values'] == ['2024', '1']
    assert client.created[0]['PartitionInput']['StorageDescriptor'][
        'Location'
    ] == 's3://bucket/silver/historical/YEAR=2024/MM=1/'


def test_job_two_registers_unique_partitions(monkeypatch):
    module = _load_module(monkeypatch, 'job_silver_to_gold.py', 'job_two_test')

    class GlueClient:
        class exceptions:
            class AlreadyExistsException(Exception):
                pass

        def __init__(self):
            self.created = []
            self.updated = []

        def create_partition(self, **kwargs):
            self.created.append(kwargs)

        def update_partition(self, **kwargs):
            self.updated.append(kwargs)

    client = GlueClient()
    fake_boto3 = types.SimpleNamespace(client=lambda _name: client)
    monkeypatch.setattr(module, 'boto3', fake_boto3)
    args = {
        'catalog_database': 'coffee',
        'catalog_table': 'gold',
        'output_path': 's3://bucket/gold',
    }
    summaries = [
        {'YEAR': 2026, 'MM': 8},
        {'YEAR': 2026, 'MM': 8},
        {'YEAR': 2027, 'MM': 1},
    ]

    module._register_partitions(args, summaries)

    assert len(client.created) == 2
    assert client.created[0]['PartitionInput']['Values'] == ['2026', '8']
    assert client.created[0]['PartitionInput']['StorageDescriptor'][
        'Location'
    ] == 's3://bucket/gold/YEAR=2026/MM=8/'


def test_job_two_ignores_existing_partitions(monkeypatch):
    module = _load_module(monkeypatch, 'job_silver_to_gold.py', 'job_two_existing')

    class GlueClient:
        class exceptions:
            class AlreadyExistsException(Exception):
                pass

        def create_partition(self, **_kwargs):
            raise self.exceptions.AlreadyExistsException()

        def update_partition(self, **kwargs):
            self.request = kwargs

    monkeypatch.setattr(
        module,
        'boto3',
        types.SimpleNamespace(client=lambda _name: GlueClient()),
    )

    module._register_partitions(
        {
            'catalog_database': 'coffee',
            'catalog_table': 'gold',
            'output_path': 's3://bucket/gold',
        },
        [{'YEAR': 2026, 'MM': 8}],
    )


def test_job_two_arguments(monkeypatch):
    module = _load_module(monkeypatch, 'job_silver_to_gold.py', 'job_two_args')
    monkeypatch.setattr(
        sys,
        'argv',
        [
            'job.py', '--JOB_NAME', 'job-two', '--input_path', 'in',
            '--output_path', 'out', '--catalog_database', 'coffee',
            '--catalog_table', 'gold',
        ],
    )

    assert module._arguments()['catalog_table'] == 'gold'


def test_job_two_main_writes_gold_and_commits(monkeypatch):
    module = _load_module(monkeypatch, 'job_silver_to_gold.py', 'job_two_main')
    args = {
        'JOB_NAME': 'job-two',
        'input_path': 's3://silver',
        'output_path': 's3://gold',
        'catalog_database': 'coffee',
        'catalog_table': 'gold',
    }
    source_rows = [types.SimpleNamespace(
        asDict=lambda recursive=True: {
            'Location': 'Armenia',
            'YEAR': 2026,
            'MM': 8,
            'Temp_Max': 25,
            'Temp_Min': 17,
            'Humidity': 70,
            'Precipitation_mm': 2,
            'Solar_Radiation': 500,
            'Close_USD_60kg': 160,
        }
    )]
    spark = _Spark(source_rows)

    class Context:
        def __init__(self, _context):
            self.spark_session = spark

    monkeypatch.setattr(module, '_arguments', lambda: args)
    monkeypatch.setattr(module, 'GlueContext', Context)
    monkeypatch.setattr(module, 'silver_to_gold', lambda rows: [
        {'YEAR': 2026, 'MM': 8, 'Location': 'Armenia', 'record_count': 1}
    ])
    registered = []
    monkeypatch.setattr(
        module,
        '_register_partitions',
        lambda received_args, summaries: registered.append(
            (received_args, summaries)
        ),
    )

    module.main()

    assert _FakeJob.last.initialized == ('job-two', args)
    assert _FakeJob.last.committed is True
    assert registered == [(args, [
        {'YEAR': 2026, 'MM': 8, 'Location': 'Armenia', 'record_count': 1}
    ])]
    assert spark.conf.values == {
        'spark.sql.sources.partitionOverwriteMode': 'dynamic',
    }
    assert spark.created[0][1].write.calls[-2:] == [
        ('partitionBy', ('YEAR', 'MM')),
        ('parquet', 's3://gold'),
    ]
