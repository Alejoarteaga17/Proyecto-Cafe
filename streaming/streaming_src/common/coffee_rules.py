"""Business rules for coffee crop monitoring and agronomic alerting."""

from __future__ import annotations

from numbers import Real

COFFEE_REQUIRED_FIELDS = (
    'sensor_id',
    'location',
    'timestamp',
    'Temp_Max',
    'Temp_Min',
    'Humidity',
    'Solar_Radiation',
    'Precipitation_mm',
    'soil_ph',
    'soil_moisture',
    'nutrients_mg_kg',
)

SOIL_PH_TARGET = (5.0, 6.0)
SOIL_MOISTURE_TARGET = (50.0, 75.0)
TEMPERATURE_TARGET = (18.0, 23.0)
RELATIVE_HUMIDITY_TARGET = (65.0, 85.0)
NUTRIENT_FLOOR = {
    'N': 25.0,
    'P': 10.0,
    'K': 80.0,
}


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


def evaluate_coffee_alerts(record):
    """Return human-readable agronomic warnings for a coffee-reading payload."""
    warnings = []

    soil_ph = _as_float(record.get('soil_ph'))
    if soil_ph is not None:
        if soil_ph < 4.8:
            warnings.append(
                'pH del suelo crítico: inferior a 4.8 (toxicidad por aluminio)'
            )
        elif soil_ph > 6.5:
            warnings.append(
                'pH del suelo crítico: superior a 6.5 (bloqueo de hierro/zinc)'
            )

    soil_moisture = _as_float(record.get('soil_moisture'))
    if soil_moisture is None:
        soil_moisture = _as_float(record.get('soil_moisture_pct'))
    if soil_moisture is not None:
        if soil_moisture < 40.0:
            warnings.append(
                'Humedad del suelo crítica: inferior a 40% (estrés hídrico)'
            )
        elif soil_moisture > 85.0:
            warnings.append(
                'Humedad del suelo crítica: superior a 85% (asfixia radicular/hongos)'
            )

    temperature = _as_float(record.get('Temp_Max'))
    if temperature is None:
        temperature = _as_float(record.get('temperature'))
    if temperature is not None and temperature > 30.0:
        warnings.append(
            'Temperatura alta: superior a 30 °C (maduración prematura / daño en taza)'
        )

    relative_humidity = _as_float(record.get('Humidity'))
    if relative_humidity is not None and relative_humidity > 90.0:
        warnings.append(
            'Humedad relativa alta: superior a 90% (riesgo de roya del café)'
        )

    nutrients = record.get('nutrients_mg_kg') or {}
    if isinstance(nutrients, dict):
        for nutrient_name, floor in NUTRIENT_FLOOR.items():
            value = _as_float(nutrients.get(nutrient_name))
            if value is not None and value < floor:
                warnings.append(
                    f'Nutriente {nutrient_name} bajo: {value} mg/kg por debajo de {floor}'
                )

    return warnings


def validate_coffee_reading(record):
    """Validate a coffee sensor payload and return a list of validation errors."""
    errors = []

    sensor_id = record.get('sensor_id')
    if not isinstance(sensor_id, str) or not sensor_id.strip():
        errors.append('"sensor_id" cannot be empty')

    location = record.get('location')
    if not isinstance(location, str) or not location.strip():
        errors.append('"location" cannot be empty')

    timestamp = record.get('timestamp')
    if not isinstance(timestamp, str) or not timestamp.strip():
        errors.append('"timestamp" cannot be empty')
    else:
        try:
            if timestamp.endswith('Z'):
                timestamp = timestamp[:-1] + '+00:00'
            __import__('datetime').datetime.fromisoformat(timestamp)
        except (TypeError, ValueError):
            errors.append('"timestamp" must be a valid ISO-8601 datetime')

    for field_name in ('Temp_Max', 'Temp_Min', 'Humidity', 'Solar_Radiation',
                       'Precipitation_mm', 'soil_ph'):
        value = _as_float(record.get(field_name))
        if value is None:
            errors.append(f'Field "{field_name}" must be numeric')

    for field_name in ('soil_moisture', 'soil_moisture_pct'):
        if field_name in record and _as_float(record.get(field_name)) is None:
            errors.append(f'Field "{field_name}" must be numeric')

    temperature_max = _as_float(record.get('Temp_Max'))
    temperature_min = _as_float(record.get('Temp_Min'))
    if temperature_min is not None and temperature_max is not None:
        if temperature_min > temperature_max:
            errors.append('"Temp_Min" cannot exceed "Temp_Max"')
    humidity = _as_float(record.get('Humidity'))
    if humidity is not None and not 0 <= humidity <= 100:
        errors.append('"Humidity" must be between 0 and 100')
    soil_moisture = _as_float(record.get('soil_moisture'))
    if soil_moisture is None:
        soil_moisture = _as_float(record.get('soil_moisture_pct'))
    if 'soil_moisture' not in record:
        errors.append('"soil_moisture" cannot be empty')
    if soil_moisture is not None and not 0 <= soil_moisture <= 100:
        errors.append('"soil_moisture" must be between 0 and 100')
    for field_name in ('Solar_Radiation', 'Precipitation_mm'):
        value = _as_float(record.get(field_name))
        if value is not None and value < 0:
            errors.append(f'"{field_name}" cannot be negative')

    nutrients = record.get('nutrients_mg_kg')
    if not isinstance(nutrients, dict):
        errors.append('"nutrients_mg_kg" must be an object with N, P and K')
    else:
        nutrient_values = {
            str(name).lower(): value for name, value in nutrients.items()
        }
        for nutrient_name in ('n', 'p', 'k'):
            if nutrient_name not in nutrient_values:
                errors.append(
                    f'"nutrients_mg_kg" is missing "{nutrient_name.upper()}"'
                )
            elif _as_float(nutrient_values[nutrient_name]) is None:
                errors.append(
                    f'"nutrients_mg_kg.{nutrient_name.upper()}" must be numeric'
                )

    return errors


def build_alert_summary(record):
    warnings = evaluate_coffee_alerts(record)
    if not warnings:
        return {
            'status': 'ok',
            'warnings': [],
        }

    critical = any(
        'crítico' in warning.lower() or 'bajo:' in warning.lower()
        for warning in warnings
    )
    status = 'critical' if critical or len(warnings) > 2 else 'suspicious'
    return {
        'status': status,
        'warnings': warnings,
    }
