"""Validation, deduplication and aggregation for IoT Bronze records."""

from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone

from streaming_src.common.coffee_rules import validate_coffee_reading


class IotTransformationResult:
    def __init__(self, valid_rows, rejected_rows, duplicate_rows):
        self.valid_rows = valid_rows
        self.rejected_rows = rejected_rows
        self.duplicate_rows = duplicate_rows


def bronze_to_silver(rows):
    """Normalize valid readings and keep the first sensor/timestamp reading."""
    valid_rows = []
    rejected_rows = []
    duplicate_rows = []
    seen = set()

    for row_number, raw_row in enumerate(rows, start=1):
        row = _normalize_input(raw_row)
        errors = validate_coffee_reading(row)
        if errors:
            rejected_rows.append({
                'row_number': row_number,
                'record': deepcopy(raw_row),
                'errors': errors,
            })
            continue

        try:
            timestamp = _parse_timestamp(row['timestamp'])
        except ValueError as error:
            rejected_rows.append({
                'row_number': row_number,
                'record': deepcopy(raw_row),
                'errors': [str(error)],
            })
            continue
        normalized = {
            'sensor_id': row['sensor_id'].strip(),
            'location': row['location'].strip(),
            'timestamp': timestamp.isoformat(),
            'YEAR': timestamp.year,
            'MM': timestamp.month,
            'Temp_Max': _number(row['Temp_Max']),
            'Temp_Min': _number(row['Temp_Min']),
            'Humidity': _number(row['Humidity']),
            'Solar_Radiation': _number(row['Solar_Radiation']),
            'Precipitation_mm': _number(row['Precipitation_mm']),
            'soil_ph': _number(row['soil_ph']),
            'soil_moisture': _number(row['soil_moisture']),
            'n': _number(row['nutrients_mg_kg']['n']),
            'p': _number(row['nutrients_mg_kg']['p']),
            'k': _number(row['nutrients_mg_kg']['k']),
        }
        duplicate_key = (normalized['sensor_id'], normalized['timestamp'])
        if duplicate_key in seen:
            duplicate_rows.append({
                'row_number': row_number,
                'record': normalized,
                'reason': 'duplicate_sensor_timestamp',
            })
            continue
        seen.add(duplicate_key)
        valid_rows.append(normalized)

    return IotTransformationResult(
        valid_rows, rejected_rows, duplicate_rows)


def silver_to_gold(rows):
    """Aggregate IoT readings by sensor, location and YEAR/MM."""
    groups = defaultdict(list)
    for row in rows:
        groups[(
            row['sensor_id'], row['location'], row['YEAR'], row['MM']
        )].append(row)

    summaries = []
    for (sensor_id, location, year, month), group in sorted(groups.items()):
        summaries.append({
            'sensor_id': sensor_id,
            'location': location,
            'YEAR': year,
            'MM': month,
            'record_count': len(group),
            'avg_temp_max': _average(group, 'Temp_Max'),
            'avg_temp_min': _average(group, 'Temp_Min'),
            'avg_humidity': _average(group, 'Humidity'),
            'avg_solar_radiation': _average(group, 'Solar_Radiation'),
            'total_precipitation_mm': round(
                sum(row['Precipitation_mm'] for row in group), 6),
            'avg_soil_ph': _average(group, 'soil_ph'),
            'avg_soil_moisture': _average(group, 'soil_moisture'),
            'avg_n': _average(group, 'n'),
            'avg_p': _average(group, 'p'),
            'avg_k': _average(group, 'k'),
        })
    return summaries


def _normalize_input(raw_row):
    row = dict(raw_row)
    nutrients = row.get('nutrients_mg_kg')
    if isinstance(nutrients, dict):
        row['nutrients_mg_kg'] = {
            key.lower(): value for key, value in nutrients.items()
        }
    return row


def _parse_timestamp(value):
    timestamp = value[:-1] + '+00:00' if value.endswith('Z') else value
    parsed = datetime.fromisoformat(timestamp)
    if parsed.tzinfo is None:
        raise ValueError('timestamp must include a timezone')
    if parsed.tzinfo is None:
        raise ValueError('timestamp must include a timezone')
    return parsed.astimezone(timezone.utc)


def _number(value):
    return float(value)


def _average(rows, field):
    return round(sum(row[field] for row in rows) / len(rows), 6)
