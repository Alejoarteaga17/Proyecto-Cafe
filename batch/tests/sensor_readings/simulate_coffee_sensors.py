#!/usr/bin/env python3
"""Continuously emit coffee sensor payloads and surface agronomic warnings."""

import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.common.coffee_rules import evaluate_coffee_alerts

SENSOR_IDS = [
    'ST-01',
    'ST-02',
    'ST-03',
    'ST-04',
]
LOCATIONS = [
    'Lote_Norte_Arabica',
    'Lote_Sur_Robusta',
    'Lote_Este_Catuai',
]


def build_payload(sensor_id, location):
    temp_max = round(random.uniform(18.0, 35.0), 2)
    temp_min = round(random.uniform(12.0, temp_max), 2)
    humidity = round(random.uniform(50.0, 95.0), 2)
    solar = round(random.uniform(120.0, 750.0), 2)
    precipitation = round(random.uniform(0.0, 30.0), 2)
    soil_ph = round(random.uniform(4.6, 6.8), 2)
    nutrients = {
        'N': round(random.uniform(18.0, 70.0), 2),
        'P': round(random.uniform(6.0, 35.0), 2),
        'K': round(random.uniform(60.0, 180.0), 2),
    }
    payload = {
        'location': location,
        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'Temp_Max': temp_max,
        'Temp_Min': temp_min,
        'Humidity': humidity,
        'Solar_Radiation': solar,
        'Precipitation_mm': precipitation,
        'soil_ph': soil_ph,
        'nutrients_mg_kg': nutrients,
    }
    warnings = evaluate_coffee_alerts(payload)
    if warnings:
        print(f'ALERTA AGRONÓMICA [{sensor_id}] {location}: {warnings}')
    print(json.dumps(payload))
    return payload


if __name__ == '__main__':
    while True:
        sensor = random.choice(SENSOR_IDS)
        location = random.choice(LOCATIONS)
        build_payload(sensor, location)
        time.sleep(2)
