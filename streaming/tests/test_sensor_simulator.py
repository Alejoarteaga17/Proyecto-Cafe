import random

from simulator.simulate_coffee_sensors import build_payload
from streaming_src.common.coffee_rules import validate_coffee_reading


def test_simulator_generates_contract_compatible_payload():
    payload = build_payload('ST-01', 'Lote_Norte_Arabica', random.Random(7))

    assert 'sensor_id' not in payload
    assert validate_coffee_reading(payload | {'sensor_id': 'ST-01'}) == []
    assert payload['location'] == 'Lote_Norte_Arabica'
    assert payload['timestamp'].endswith('Z')


def test_simulator_is_reproducible_with_seed():
    first = build_payload('ST-01', 'Lote_Norte_Arabica', random.Random(11))
    second = build_payload('ST-01', 'Lote_Norte_Arabica', random.Random(11))

    assert first == second
