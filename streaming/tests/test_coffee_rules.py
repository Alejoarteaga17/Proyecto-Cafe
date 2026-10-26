import pytest

from streaming_src.common.coffee_rules import (
    build_alert_summary,
    evaluate_coffee_alerts,
    validate_coffee_reading,
)


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


def test_sensor_contract_rejects_missing_fields_and_invalid_nutrients():
    errors = validate_coffee_reading({})

    assert '"sensor_id" cannot be empty' in errors
    assert '"nutrients_mg_kg" must be an object with N, P and K' in errors

    reading = _reading()
    reading['nutrients_mg_kg'] = {'N': 'bad', 'P': 1}
    errors = validate_coffee_reading(reading)

    assert '"nutrients_mg_kg.N" must be numeric' in errors
    assert '"nutrients_mg_kg" is missing "K"' in errors


@pytest.mark.parametrize(
    'field, value, expected',
    [
        ('Temp_Max', 31, 'Temperatura alta'),
        ('Humidity', 91, 'Humedad relativa alta'),
        ('soil_ph', 4.7, 'pH del suelo crítico'),
        ('soil_ph', 6.6, 'pH del suelo crítico'),
        ('soil_moisture', 39, 'Humedad del suelo crítica'),
        ('soil_moisture_pct', 86, 'Humedad del suelo crítica'),
    ],
)
def test_evaluate_coffee_alerts_reports_agronomic_anomalies(field, value, expected):
    reading = _reading()
    reading[field] = value
    if field == 'soil_moisture_pct':
        del reading['soil_moisture']

    warnings = evaluate_coffee_alerts(reading)

    assert any(expected in warning for warning in warnings)


def test_evaluate_coffee_alerts_reports_low_nutrients_and_string_values():
    reading = _reading()
    reading['nutrients_mg_kg'] = {'N': '1', 'P': '2', 'K': '3'}

    warnings = evaluate_coffee_alerts(reading)

    assert len(warnings) == 3
    assert all('bajo' in warning for warning in warnings)


def test_build_alert_summary_classifies_status():
    assert build_alert_summary(_reading()) == {'status': 'ok', 'warnings': []}

    suspicious = _reading()
    suspicious['Temp_Max'] = 31
    assert build_alert_summary(suspicious)['status'] == 'suspicious'

    critical = _reading()
    critical['nutrients_mg_kg'] = {'N': 1, 'P': 1, 'K': 1}
    assert build_alert_summary(critical)['status'] == 'critical'
