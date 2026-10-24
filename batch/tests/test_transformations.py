from src.pipeline.transformations import bronze_to_silver, silver_to_gold


def _row(location='Armenia', day=23, temp=25):
    return {
        'LON': '-75.68', 'LAT': '4.53', 'YEAR': '2026', 'MM': '8',
        'DD': str(day), 'DOY': '234', 'Date': '2026-08-23',
        'Temp_Max': str(temp), 'Temp_Min': '17', 'Humidity': '70',
        'Solar_Radiation': '500', 'Precipitation_mm': '2',
        'Location': location, 'Close_USD_60kg': '160',
        'Is_Weekend': 'false', 'Is_Interpolated': 'false',
        'brl': '5', 'cny': '7', 'mxn': '18',
    }


def test_bronze_to_silver_rejects_invalid_and_deduplicates():
    result = bronze_to_silver([_row(), _row(), {**_row(), 'Humidity': 'bad'}])

    assert len(result.valid_rows) == 1
    assert len(result.duplicate_rows) == 1
    assert result.rejected_rows[0]['row_number'] == 4


def test_silver_to_gold_groups_by_location_year_and_month():
    result = bronze_to_silver([_row(temp=24), _row(day=24, temp=26)])
    summaries = silver_to_gold(result.valid_rows)

    assert summaries == [{
        'Location': 'Armenia', 'YEAR': 2026, 'MM': 8,
        'record_count': 2, 'avg_temp_max': 25.0, 'avg_temp_min': 17.0,
        'avg_humidity': 70.0, 'total_precipitation_mm': 4.0,
        'avg_solar_radiation': 500.0, 'avg_close_usd_60kg': 160.0,
    }]
