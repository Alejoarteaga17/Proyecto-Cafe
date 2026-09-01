"""Utilities to map batch and streaming coffee records into the MongoDB measurement model."""

from __future__ import annotations

import datetime as dt
from numbers import Real


def _as_float(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, Real):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {'true', '1', 'yes'}:
            return True
        if normalized in {'false', '0', 'no'}:
            return False
    return False


def _clean_string(value):
    if value is None:
        return ''
    if not isinstance(value, str):
        value = str(value)
    return value.strip()


def _parse_date(value):
    if value is None:
        return None
    if isinstance(value, dt.datetime):
        return value.date().isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return None
        if normalized.endswith('Z'):
            normalized = normalized[:-1] + '+00:00'
        try:
            parsed = dt.datetime.fromisoformat(normalized)
            return parsed.date().isoformat()
        except ValueError:
            try:
                return dt.datetime.strptime(normalized, '%Y-%m-%d').date().isoformat()
            except ValueError:
                return None
    return None


def _infer_country(location_name):
    cleaned = _clean_string(location_name)
    if not cleaned:
        return 'Unknown'
    prefix = cleaned.split('_', 1)[0]
    return prefix if prefix else 'Unknown'


def _build_temporal(date_value, year=None, month=None, day=None, day_of_year=None,
                    is_weekend=None):
    iso_date = _parse_date(date_value)
    if iso_date:
        parsed_date = dt.date.fromisoformat(iso_date)
        year = parsed_date.year if year is None else year
        month = parsed_date.month if month is None else month
        day = parsed_date.day if day is None else day
        day_of_year = parsed_date.timetuple().tm_yday if day_of_year is None else day_of_year
        is_weekend = parsed_date.weekday() >= 5 if is_weekend is None else is_weekend
    else:
        year = int(year) if year is not None else None
        month = int(month) if month is not None else None
        day = int(day) if day is not None else None
        day_of_year = int(day_of_year) if day_of_year is not None else None
        if is_weekend is not None:
            is_weekend = bool(is_weekend)

    return {
        'date': iso_date,
        'year': year,
        'month': month,
        'day': day,
        'day_of_year': day_of_year,
        'is_weekend': is_weekend,
    }


def _build_location(location_name, latitude=None, longitude=None):
    location_text = _clean_string(location_name)
    return {
        'name': location_text,
        'country': _infer_country(location_text),
        'latitude': _as_float(latitude),
        'longitude': _as_float(longitude),
    }


def _build_climate(record):
    return {
        'temperature_max': _as_float(record.get('Temp_Max', record.get('temperature_max'))),
        'temperature_min': _as_float(record.get('Temp_Min', record.get('temperature_min'))),
        'humidity': _as_float(record.get('Humidity', record.get('humidity'))),
        'solar_radiation': _as_float(record.get('Solar_Radiation', record.get('solar_radiation'))),
        'precipitation_mm': _as_float(record.get('Precipitation_mm', record.get('precipitation_mm'))),
    }


def _build_market(record):
    return {
        'close_usd_60kg': _as_float(record.get('Close_USD_60kg')),
        'brl': _as_float(record.get('brl')),
        'cny': _as_float(record.get('cny')),
        'mxn': _as_float(record.get('mxn')),
    }


def build_batch_measurement(row):
    location_name = row.get('Location')
    document = {
        'temporal': _build_temporal(
            row.get('Date'),
            year=row.get('YEAR'),
            month=row.get('MM'),
            day=row.get('DD'),
            day_of_year=row.get('DOY'),
            is_weekend=row.get('Is_Weekend'),
        ),
        'location': _build_location(
            location_name,
            latitude=row.get('LAT'),
            longitude=row.get('LON'),
        ),
        'climate': _build_climate(row),
        'market': _build_market(row),
        'data_quality': {
            'is_interpolated': _as_bool(row.get('Is_Interpolated')),
        },
        'source': {
            'type': 'batch',
            'dataset': 'Coffee_Data_Set.csv',
        },
    }
    return document


def build_sensor_measurement(reading, alert_summary=None):
    if alert_summary is None:
        alert_summary = {'status': 'ok', 'warnings': []}

    location_name = reading.get('location')
    latitude = reading.get('latitude')
    longitude = reading.get('longitude')
    timestamp = reading.get('timestamp')
    date_value = _parse_date(timestamp)
    if date_value:
        parsed_date = dt.date.fromisoformat(date_value)
        sensor_date = date_value
        temporal = {
            'date': sensor_date,
            'year': parsed_date.year,
            'month': parsed_date.month,
            'day': parsed_date.day,
            'day_of_year': parsed_date.timetuple().tm_yday,
            'is_weekend': parsed_date.weekday() >= 5,
        }
    else:
        temporal = {
            'date': None,
            'year': None,
            'month': None,
            'day': None,
            'day_of_year': None,
            'is_weekend': None,
        }

    document = {
        'temporal': temporal,
        'location': _build_location(location_name, latitude=latitude, longitude=longitude),
        'climate': _build_climate(reading),
        'market': {},
        'data_quality': {
            'is_interpolated': False,
            'alert_status': alert_summary.get('status', 'ok'),
        },
        'source': {
            'type': 'streaming',
            'device_id': reading.get('sensor_id') or reading.get('thing_name') or 'unknown',
        },
    }
    return document
