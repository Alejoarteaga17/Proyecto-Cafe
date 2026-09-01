from src.common.coffee_measurement_model import build_batch_measurement, build_sensor_measurement
from src.common.coffee_rules import build_alert_summary


def test_build_batch_measurement_uses_nested_data_model():
    row = {
        'LON': -75.6,
        'LAT': 5.6,
        'YEAR': 2000,
        'MM': 1,
        'DD': 3,
        'DOY': 3,
        'Date': '2000-01-03',
        'Temp_Max': 24.5,
        'Temp_Min': 15.2,
        'Humidity': 78.4,
        'Solar_Radiation': 18.5,
        'Precipitation_mm': 4.2,
        'Location': 'Colombia_Andes',
        'Close_USD_60kg': 154.1,
        'Is_Weekend': False,
        'Is_Interpolated': False,
        'brl': 1.805,
        'cny': 8.2798,
        'mxn': 9.4015,
    }

    document = build_batch_measurement(row)

    assert document['temporal']['date'] == '2000-01-03'
    assert document['temporal']['year'] == 2000
    assert document['location']['country'] == 'Colombia'
    assert document['location']['name'] == 'Colombia_Andes'
    assert document['climate']['temperature_max'] == 24.5
    assert document['market']['close_usd_60kg'] == 154.1
    assert document['data_quality']['is_interpolated'] is False
    assert document['source'] == {'type': 'batch', 'dataset': 'Coffee_Data_Set.csv'}


def test_build_sensor_measurement_uses_streaming_source_and_alert_status():
    reading = {
        'sensor_id': 'sensor_001',
        'location': 'Colombia_Andes',
        'timestamp': '2024-01-05T12:00:00Z',
        'Temp_Max': 30.5,
        'Temp_Min': 17.5,
        'Humidity': 92.0,
        'Solar_Radiation': 160.0,
        'Precipitation_mm': 2.0,
        'soil_ph': 5.8,
        'soil_moisture': 35.0,
        'nutrients_mg_kg': {'N': 30.0, 'P': 12.0, 'K': 90.0},
    }

    alert_summary = build_alert_summary(reading)
    document = build_sensor_measurement(reading, alert_summary)

    assert document['source'] == {'type': 'streaming', 'device_id': 'sensor_001'}
    assert document['data_quality']['alert_status'] in {'suspicious', 'critical'}
    assert document['temporal']['date'] == '2024-01-05'
    assert document['location']['name'] == 'Colombia_Andes'
    assert document['source']['type'] == 'streaming'
