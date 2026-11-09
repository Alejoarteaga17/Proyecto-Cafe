from streaming_src.pipeline.transformations import bronze_to_silver, silver_to_gold


def _reading(sensor_id='ST-01', timestamp='2026-10-24T00:00:00Z'):
    return {
        'sensor_id': sensor_id,
        'location': 'Lote_Norte_Arabica',
        'timestamp': timestamp,
        'Temp_Max': 24,
        'Temp_Min': 18,
        'Humidity': 70,
        'Solar_Radiation': 500,
        'Precipitation_mm': 2,
        'soil_ph': 5.5,
        'soil_moisture': 60,
        'nutrients_mg_kg': {'N': 30, 'P': 15, 'K': 100},
    }


def test_iot_bronze_to_silver_normalizes_and_keeps_first_duplicate():
    result = bronze_to_silver([
        _reading(),
        _reading(),
        _reading(timestamp='2026-11-01T00:00:00Z'),
    ])

    assert len(result.valid_rows) == 2
    assert len(result.duplicate_rows) == 1
    assert result.valid_rows[0]['n'] == 30.0
    assert result.valid_rows[0]['p'] == 15.0
    assert result.valid_rows[0]['k'] == 100.0
    assert result.valid_rows[0]['YEAR'] == 2026
    assert result.valid_rows[0]['MM'] == 10


def test_iot_bronze_to_silver_rejects_invalid_readings():
    reading = _reading()
    reading['soil_moisture'] = 101

    result = bronze_to_silver([reading])

    assert not result.valid_rows
    assert result.rejected_rows[0]['row_number'] == 1
    assert 'soil_moisture' in ' '.join(result.rejected_rows[0]['errors'])


def test_iot_bronze_to_silver_rejects_timezone_less_timestamp():
    result = bronze_to_silver([_reading(timestamp='2026-10-24T00:00:00')])

    assert not result.valid_rows
    assert 'timezone' in result.rejected_rows[0]['errors'][0]


def test_iot_silver_to_gold_aggregates_by_sensor_location_and_month():
    first = bronze_to_silver([
        _reading(),
        _reading(timestamp='2026-10-24T01:00:00Z'),
    ])

    summaries = silver_to_gold(first.valid_rows)

    assert summaries == [{
        'sensor_id': 'ST-01',
        'location': 'Lote_Norte_Arabica',
        'YEAR': 2026,
        'MM': 10,
        'record_count': 2,
        'avg_temp_max': 24.0,
        'avg_temp_min': 18.0,
        'avg_humidity': 70.0,
        'avg_solar_radiation': 500.0,
        'total_precipitation_mm': 4.0,
        'avg_soil_ph': 5.5,
        'avg_soil_moisture': 60.0,
        'avg_n': 30.0,
        'avg_p': 15.0,
        'avg_k': 100.0,
    }]
