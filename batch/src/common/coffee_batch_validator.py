"""Validation for coffee historical batch rows."""

import datetime as dt
import math

REQUIRED_COLUMNS = (
    'LON', 'LAT', 'YEAR', 'MM', 'DD', 'DOY', 'Date', 'Temp_Max',
    'Temp_Min', 'Humidity', 'Solar_Radiation', 'Precipitation_mm',
    'Location', 'Close_USD_60kg', 'Is_Weekend', 'Is_Interpolated', 'brl',
    'cny', 'mxn')
MAX_ROWS = 300


class BatchValidationError(Exception):

    def __init__(self, errors):
        super().__init__('; '.join(errors))
        self.errors = errors


def validate_rows(rows):
    if not rows:
        raise BatchValidationError(['CSV file has no data rows'])
    if len(rows) > MAX_ROWS:
        raise BatchValidationError(
            [f'CSV file has {len(rows)} rows, maximum is {MAX_ROWS}'])

    validated = []
    errors = []
    for row_number, row in enumerate(rows, start=2):
        try:
            validated.append(validate_row(row, row_number))
        except BatchValidationError as error:
            errors.extend(error.errors)
    if errors:
        raise BatchValidationError(errors)
    return validated


def validate_row(row, row_number=None):
    errors = []
    prefix = f'Row {row_number}: ' if row_number else ''
    values = {}

    for column in REQUIRED_COLUMNS:
        if column not in row:
            errors.append(f'{prefix}missing "{column}"')
            continue
        value = row[column]
        if isinstance(value, str):
            value = value.strip()
        values[column] = value

    if errors:
        raise BatchValidationError(errors)

    for column in ('LON', 'LAT', 'Temp_Max', 'Temp_Min', 'Humidity',
                   'Solar_Radiation', 'Precipitation_mm', 'Close_USD_60kg',
                   'brl', 'cny', 'mxn'):
        number = _to_float(values[column])
        if number is None:
            errors.append(f'{prefix}"{column}" must be numeric')
        else:
            values[column] = number

    for column in ('YEAR', 'MM', 'DD', 'DOY'):
        number = _to_int(values[column])
        if number is None:
            errors.append(f'{prefix}"{column}" must be an integer')
        else:
            values[column] = number

    try:
        date_value = dt.date.fromisoformat(str(values['Date']))
    except (TypeError, ValueError):
        date_value = None
        errors.append(f'{prefix}"Date" must be an ISO-8601 date')
    if date_value is not None:
        if date_value.year != values.get('YEAR'):
            errors.append(f'{prefix}"Date" year does not match "YEAR"')
        if date_value.month != values.get('MM'):
            errors.append(f'{prefix}"Date" month does not match "MM"')
        if date_value.day != values.get('DD'):
            errors.append(f'{prefix}"Date" day does not match "DD"')
        if date_value.timetuple().tm_yday != values.get('DOY'):
            errors.append(f'{prefix}"Date" day of year does not match "DOY"')

    if isinstance(values.get('YEAR'), int) and not 1900 <= values['YEAR'] <= 2100:
        errors.append(f'{prefix}"YEAR" is outside the supported range')
    if isinstance(values.get('MM'), int) and not 1 <= values['MM'] <= 12:
        errors.append(f'{prefix}"MM" must be between 1 and 12')
    if isinstance(values.get('DD'), int) and not 1 <= values['DD'] <= 31:
        errors.append(f'{prefix}"DD" must be between 1 and 31')
    if isinstance(values.get('DOY'), int) and not 1 <= values['DOY'] <= 366:
        errors.append(f'{prefix}"DOY" must be between 1 and 366')
    if (date_value is not None and values.get('DOY') == 366
            and not _is_leap_year(date_value.year)):
        errors.append(f'{prefix}"DOY" 366 is invalid for a non-leap year')
    if (isinstance(values.get('LON'), float)
            and not -180 <= values['LON'] <= 180):
        errors.append(f'{prefix}"LON" must be between -180 and 180')
    if (isinstance(values.get('LAT'), float)
            and not -90 <= values['LAT'] <= 90):
        errors.append(f'{prefix}"LAT" must be between -90 and 90')
    if (isinstance(values.get('Temp_Min'), float)
            and isinstance(values.get('Temp_Max'), float)):
        if values['Temp_Min'] > values['Temp_Max']:
            errors.append(f'{prefix}"Temp_Min" cannot exceed "Temp_Max"')
    if (isinstance(values.get('Humidity'), float)
            and not 0 <= values['Humidity'] <= 100):
        errors.append(f'{prefix}"Humidity" must be between 0 and 100')
    if (isinstance(values.get('Solar_Radiation'), float)
            and values['Solar_Radiation'] < 0):
        errors.append(f'{prefix}"Solar_Radiation" cannot be negative')
    if (isinstance(values.get('Precipitation_mm'), float)
            and values['Precipitation_mm'] < 0):
        errors.append(f'{prefix}"Precipitation_mm" cannot be negative')
    if not isinstance(values.get('Location'), str) or not values['Location']:
        errors.append(f'{prefix}"Location" cannot be empty')
    for column in ('Close_USD_60kg', 'brl', 'cny', 'mxn'):
        if isinstance(values.get(column), float) and values[column] < 0:
            errors.append(f'{prefix}"{column}" cannot be negative')

    if errors:
        raise BatchValidationError(errors)
    return values


def _to_float(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _to_int(value):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if float(value) == number else None


def _is_leap_year(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)