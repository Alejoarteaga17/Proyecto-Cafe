import random

import pytest

from simulator.simulate_coffee_sensors import build_payload
from streaming_src.common.coffee_rules import validate_coffee_reading


def test_simulator_generates_contract_compatible_payload():
    payload = build_payload('ST-01', 'Lote_Norte_Arabica', random.Random(7))

    assert 'sensor_id' not in payload
    assert validate_coffee_reading(payload | {'sensor_id': 'ST-01'}) == []
    assert payload['location'] == 'Lote_Norte_Arabica'
    assert payload['timestamp'].endswith('Z')
    assert 0 <= payload['soil_moisture'] <= 100


def test_simulator_is_reproducible_with_seed():
    first = build_payload('ST-01', 'Lote_Norte_Arabica', random.Random(11))
    second = build_payload('ST-01', 'Lote_Norte_Arabica', random.Random(11))

    assert first == second


def test_simulator_uses_default_random_generator(monkeypatch):
    monkeypatch.setattr('simulator.simulate_coffee_sensors.random.uniform',
                        lambda low, high: (low + high) / 2)

    payload = build_payload('ST-02', 'Lote_Sur_Robusta')

    assert payload['Temp_Max'] == 26.5
    assert payload['Temp_Min'] == 19.25


def test_simulator_arguments_support_finite_seeded_runs(monkeypatch):
    from simulator import simulate_coffee_sensors

    monkeypatch.setattr(
        'sys.argv',
        ['simulate_coffee_sensors.py', '--count', '2', '--interval', '0',
         '--seed', '7'],
    )

    args = simulate_coffee_sensors._arguments()

    assert args.count == 2
    assert args.interval == 0
    assert args.seed == 7


def test_publish_payload_sends_json_to_iot_data_client():
    from simulator.simulate_coffee_sensors import publish_payload

    class FakeClient:
        def __init__(self):
            self.arguments = None

        def publish(self, **kwargs):
            self.arguments = kwargs

    client = FakeClient()
    payload = {'location': 'Lote_Norte_Arabica', 'value': 1}

    publish_payload(client, 'sensors/coffee/test/data', payload)

    assert client.arguments == {
        'topic': 'sensors/coffee/test/data',
        'qos': 0,
        'payload': b'{"location": "Lote_Norte_Arabica", "value": 1}',
    }


def test_publish_arguments_define_topic_and_thing_name(monkeypatch):
    from simulator import simulate_coffee_sensors

    monkeypatch.setattr(
        'sys.argv',
        [
            'simulate_coffee_sensors.py',
            '--publish',
            '--thing-name',
            'my-sensor',
            '--count',
            '1',
        ],
    )

    args = simulate_coffee_sensors._arguments()

    assert args.publish is True
    assert args.thing_name == 'my-sensor'
    assert args.topic is None


def test_simulator_topic_can_include_selected_sensor():
    from simulator.simulate_coffee_sensors import SENSOR_IDS, build_topic

    assert 'ST-01' in SENSOR_IDS
    assert build_topic('ST-01') == 'sensors/coffee/ST-01/data'
    assert build_topic('ST-02', 'sensors/coffee/{sensor_id}/data') == (
        'sensors/coffee/ST-02/data'
    )


def test_default_thing_name_uses_deploy_app(monkeypatch):
    from simulator import simulate_coffee_sensors

    monkeypatch.setenv('DEPLOY_APP', 'farm-project')
    monkeypatch.setattr(
        'sys.argv',
        ['simulate_coffee_sensors.py'],
    )

    args = simulate_coffee_sensors._arguments()

    assert args.thing_name == 'farm-project-iot-sensor-simulator'
