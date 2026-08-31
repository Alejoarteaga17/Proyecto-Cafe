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

    for field_name in ('Temp_Max', 'Temp_Min', 'Humidity', 'Solar_Radiation',
                       'Precipitation_mm', 'soil_ph'):
        value = _as_float(record.get(field_name))
        if value is None:
            errors.append(f'Field "{field_name}" must be numeric')

    nutrients = record.get('nutrients_mg_kg')
    if not isinstance(nutrients, dict):
        errors.append('"nutrients_mg_kg" must be an object with N, P and K')
    else:
        for nutrient_name in ('N', 'P', 'K'):
            if nutrient_name not in nutrients:
                errors.append(f'"nutrients_mg_kg" is missing "{nutrient_name}"')
            elif _as_float(nutrients.get(nutrient_name)) is None:
                errors.append(
                    f'"nutrients_mg_kg.{nutrient_name}" must be numeric'
                )

    return errors


def build_alert_summary(record):
    warnings = evaluate_coffee_alerts(record)
    return {
        'status': 'alert' if warnings else 'ok',
        'warnings': warnings,
    }
