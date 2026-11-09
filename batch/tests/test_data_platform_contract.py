from pathlib import Path


ROOT = Path(__file__).parents[2]
DATA_PLATFORM = (
    ROOT / 'batch' / 'infrastructure' / 'serverless' / 'data-platform'
)


def test_data_platform_keeps_historical_and_iot_state_machines_separate():
    template = (DATA_PLATFORM / 'resources.yml').read_text()

    assert 'HistoricalEtlStateMachine:' in template
    assert 'IotEtlStateMachine:' in template
    assert '"BronzeToSilver"' in template
    assert '"SilverToGold"' in template
    assert '"IotBronzeToSilver"' in template
    assert '"IotSilverToGold"' in template
    assert 'IotBronzeJob: !Ref IotBronzeToSilverJob' in template
    assert 'IotGoldJob: !Ref IotSilverToGoldJob' in template


def test_quicksight_configuration_targets_both_gold_catalog_tables():
    template = (DATA_PLATFORM / 'quicksight.yml').read_text()

    assert 'Type: AWS::QuickSight::DataSource' in template
    assert 'Name: coffee_historical_gold' in template
    assert 'Name: coffee_iot_gold' in template
    assert "Default: 'false'" in template
    assert 'WorkGroup: !Ref GoldWorkGroup' in template
