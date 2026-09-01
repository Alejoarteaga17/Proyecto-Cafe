"""Validation for coffee historical batch rows."""

import datetime as dt

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

    if values.get('YEAR') is not None and not 1900 <= values['YEAR'] <= 2100:
        errors.append(f'{prefix}"YEAR" is outside the supported range')
    if values.get('MM') is not None and not 1 <= values['MM'] <= 12:
        errors.append(f'{prefix}"MM" must be between 1 and 12')
    if values.get('DD') is not None and not 1 <= values['DD'] <= 31:
        errors.append(f'{prefix}"DD" must be between 1 and 31')
    if values.get('DOY') is not None and not 1 <= values['DOY'] <= 366:
        errors.append(f'{prefix}"DOY" must be between 1 and 366')
    if values.get('Temp_Min') is not None and values.get('Temp_Max') is not None:
        if values['Temp_Min'] > values['Temp_Max']:
            errors.append(f'{prefix}"Temp_Min" cannot exceed "Temp_Max"')
    if values.get('Humidity') is not None and not 0 <= values['Humidity'] <= 100:
        errors.append(f'{prefix}"Humidity" must be between 0 and 100')
    if values.get('Solar_Radiation') is not None and values['Solar_Radiation'] < 0:
        errors.append(f'{prefix}"Solar_Radiation" cannot be negative')
    if values.get('Precipitation_mm') is not None and values['Precipitation_mm'] < 0:
        errors.append(f'{prefix}"Precipitation_mm" cannot be negative')
    if not isinstance(values.get('Location'), str) or not values['Location']:
        errors.append(f'{prefix}"Location" cannot be empty')
    for column in ('Close_USD_60kg', 'brl', 'cny', 'mxn'):
        if values.get(column) is not None and values[column] < 0:
            errors.append(f'{prefix}"{column}" cannot be negative')

    if errors:
        raise BatchValidationError(errors)
    return values


def _to_float(value):
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if float(value) == number else None