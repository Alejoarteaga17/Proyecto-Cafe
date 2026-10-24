from streaming_src.common.coffee_rules import validate_coffee_reading


def _reading():
    return {
        'sensor_id': 'ST-01',
        'location': 'Lote_Norte_Arabica',
        'timestamp': '2026-10-24T00:00:00Z',
        'Temp_Max': 24,
        'Temp_Min': 18,
        'Humidity': 70,
        'Solar_Radiation': 500,
        'Precipitation_mm': 2,
        'soil_ph': 5.5,
        'soil_moisture': 60,
        'nutrients_mg_kg': {'N': 30, 'P': 15, 'K': 100},
    }


def test_sensor_contract_accepts_valid_reading():
    assert validate_coffee_reading(_reading()) == []


def test_sensor_contract_rejects_invalid_ranges_and_timestamp():
    reading = _reading()
    reading.update({
        'timestamp': 'not-a-date',
        'Temp_Min': 30,
        'Humidity': 110,
        'soil_moisture': -1,
    })

    errors = validate_coffee_reading(reading)

    assert '"timestamp"' in ' '.join(errors)
    assert '"Temp_Min"' in ' '.join(errors)
    assert '"Humidity"' in ' '.join(errors)
    assert '"soil_moisture"' in ' '.join(errors)
