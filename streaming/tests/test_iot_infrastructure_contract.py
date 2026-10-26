from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_iot_infrastructure_keeps_sensor_topics_explicit():
    template = (
        ROOT / 'infrastructure/serverless/iot/iot.yml'
    ).read_text()

    for sensor_id in ('ST-01', 'ST-02', 'ST-03', 'ST-04'):
        assert f'topic/sensors/coffee/{sensor_id}/data' in template
    assert "topic(3) AS sensor_id" in template
    assert 'EventBridge' not in template


def test_iot_glue_jobs_use_year_month_partitions_and_separate_paths():
    template = (
        ROOT.parent / 'batch/infrastructure/serverless/data-platform/resources.yml'
    ).read_text()

    assert 'IotEtlStateMachine:' in template
    assert 'job_iot_bronze_to_silver.py' in template
    assert 'job_iot_silver_to_gold.py' in template
    assert 'silver/iot/' in template
    assert 'gold/iot/' in template
    assert 'Name: YEAR' in template
    assert 'Name: MM' in template
