import datetime as dt

import pytest

from src.common.coffee_batch_validator import BatchValidationError, validate_row, validate_rows
from src.pipeline.transformations import bronze_to_silver, silver_to_gold


def _row(location='Armenia', day=23, temp=25):
    observed_date = dt.date(2026, 8, day)
    return {
        'LON': '-75.68', 'LAT': '4.53', 'YEAR': '2026', 'MM': '8',
        'DD': str(day), 'DOY': str(observed_date.timetuple().tm_yday),
        'Date': observed_date.isoformat(),
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


@pytest.mark.parametrize(
    'changes, expected_error',
    [
        ({'YEAR': '1800'}, '"YEAR" is outside'),
        ({'MM': '13'}, '"MM" must be between'),
        ({'DD': '0'}, '"DD" must be between'),
        ({'DOY': '367'}, '"DOY" must be between'),
        ({'Temp_Min': '30'}, '"Temp_Min" cannot exceed'),
        ({'Solar_Radiation': '-1'}, '"Solar_Radiation" cannot be negative'),
        ({'Precipitation_mm': '-1'}, '"Precipitation_mm" cannot be negative'),
        ({'Location': ''}, '"Location" cannot be empty'),
        ({'Close_USD_60kg': '-1'}, '"Close_USD_60kg" cannot be negative'),
    ],
)
def test_validate_row_rejects_invalid_ranges(changes, expected_error):
    row = _row()
    row.update(changes)

    with pytest.raises(BatchValidationError, match=expected_error):
        validate_row(row, 2)


def test_validate_row_rejects_missing_column_and_bad_date():
    row = _row()
    del row['LON']
    row['Date'] = 'not-a-date'

    with pytest.raises(BatchValidationError) as error:
        validate_row(row, 2)

    assert any('missing "LON"' in message for message in error.value.errors)
    assert '"Date" must be an ISO-8601 date' not in error.value.errors


def test_validate_row_rejects_non_integer_values_and_date_mismatch():
    row = _row()
    row.update({'YEAR': '2026.5', 'Date': '2026-09-23'})

    with pytest.raises(BatchValidationError) as error:
        validate_row(row, 2)

    assert any('"YEAR" must be an integer' in message
               for message in error.value.errors)
    assert any('"Date" month does not match "MM"' in message
               for message in error.value.errors)


@pytest.mark.parametrize(
    'changes, expected_error',
    [
        ({'DOY': '234'}, 'day of year does not match'),
        ({'LON': '-181'}, '"LON" must be between'),
        ({'LAT': '91'}, '"LAT" must be between'),
        ({'Humidity': 'NaN'}, '"Humidity" must be numeric'),
        ({'Solar_Radiation': 'Infinity'}, '"Solar_Radiation" must be numeric'),
    ],
)
def test_validate_row_rejects_inconsistent_coordinates_and_non_finite_values(
        changes, expected_error):
    row = _row()
    row.update(changes)

    with pytest.raises(BatchValidationError, match=expected_error):
        validate_row(row, 2)


def test_validate_row_accepts_day_366_only_in_leap_year():
    row = _row()
    row.update({
        'YEAR': '2024', 'MM': '12', 'DD': '31', 'DOY': '366',
        'Date': '2024-12-31',
    })
    validate_row(row, 2)

    row['YEAR'] = '2023'
    row['Date'] = '2023-12-31'
    with pytest.raises(BatchValidationError, match='non-leap year'):
        validate_row(row, 2)


def test_validate_rows_rejects_empty_and_too_many_rows():
    with pytest.raises(BatchValidationError, match='no data rows'):
        validate_rows([])

    with pytest.raises(BatchValidationError, match='maximum is 300'):
        validate_rows([_row()] * 301)
