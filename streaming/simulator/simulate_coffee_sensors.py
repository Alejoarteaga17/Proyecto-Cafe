#!/usr/bin/env python3
"""Continuously emit coffee sensor payloads and surface agronomic warnings."""

import json
import random
import argparse
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streaming_src.common.coffee_rules import (
    evaluate_coffee_alerts,
    validate_coffee_reading,
)

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


def build_payload(sensor_id, location, random_generator=None):
    random_generator = random_generator or random
    temp_max = round(random_generator.uniform(18.0, 35.0), 2)
    temp_min = round(random_generator.uniform(12.0, temp_max), 2)
    humidity = round(random_generator.uniform(50.0, 95.0), 2)
    soil_moisture = round(random_generator.uniform(35.0, 90.0), 2)
    solar = round(random_generator.uniform(120.0, 750.0), 2)
    precipitation = round(random_generator.uniform(0.0, 30.0), 2)
    soil_ph = round(random_generator.uniform(4.6, 6.8), 2)
    nutrients = {
        'N': round(random_generator.uniform(18.0, 70.0), 2),
        'P': round(random_generator.uniform(6.0, 35.0), 2),
        'K': round(random_generator.uniform(60.0, 180.0), 2),
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
        'soil_moisture': soil_moisture,
        'nutrients_mg_kg': nutrients,
    }
    errors = validate_coffee_reading(payload | {'sensor_id': sensor_id})
    if errors:
        raise ValueError(f'Generated invalid sensor payload: {errors}')
    warnings = evaluate_coffee_alerts(payload)
    if warnings:
        print(f'ALERTA AGRONÓMICA [{sensor_id}] {location}: {warnings}')
    print(json.dumps(payload))
    return payload


def _create_iot_data_client(endpoint=None):
    try:
        import boto3
    except ImportError as error:
        raise RuntimeError(
            'boto3 is required when publishing to AWS IoT. '
            'Run the simulator in the project Docker container.'
        ) from error

    if endpoint is None:
        endpoint = boto3.client('iot').describe_endpoint(
            endpointType='iot:Data-ATS'
        )['endpointAddress']
    return boto3.client('iot-data', endpoint_url=f'https://{endpoint}')


def publish_payload(client, topic, payload):
    client.publish(
        topic=topic,
        qos=0,
        payload=json.dumps(payload).encode('utf-8'),
    )


def build_topic(sensor_id, topic_template=None):
    return (
        topic_template.format(sensor_id=sensor_id)
        if topic_template
        else f'sensors/coffee/{sensor_id}/data'
    )


def _arguments():
    deploy_app = os.getenv('DEPLOY_APP', 'coffee-cultivation')
    parser = argparse.ArgumentParser(
        description='Generate valid coffee sensor events for IoT Core.'
    )
    parser.add_argument('--count', type=int, default=0,
                        help='Number of events; 0 runs continuously.')
    parser.add_argument('--interval', type=float, default=2.0,
                        help='Seconds between events.')
    parser.add_argument('--seed', type=int, help='Seed for reproducible events.')
    parser.add_argument(
        '--publish',
        action='store_true',
        help='Publish generated events to AWS IoT Core.',
    )
    parser.add_argument(
        '--thing-name',
        default=f'{deploy_app}-iot-sensor-simulator',
        help='IoT Thing name used by the publishing credentials.',
    )
    parser.add_argument(
        '--topic',
        help='MQTT topic template; use {sensor_id} for the selected sensor.',
    )
    parser.add_argument(
        '--endpoint',
        help='AWS IoT Data ATS endpoint; discovered automatically if omitted.',
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = _arguments()
    generator = random.Random(args.seed)
    client = _create_iot_data_client(args.endpoint) if args.publish else None
    generated = 0
    while args.count == 0 or generated < args.count:
        sensor = generator.choice(SENSOR_IDS)
        location = generator.choice(LOCATIONS)
        payload = build_payload(sensor, location, generator)
        topic = build_topic(sensor, args.topic)
        if client is not None:
            publish_payload(client, topic, payload)
            print(f'PUBLICADO en {topic}')
        generated += 1
        if args.count == 0 or generated < args.count:
            time.sleep(args.interval)
