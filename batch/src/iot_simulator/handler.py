"""Start and execute controlled IoT sensor simulations."""

import json
import os
import random
import time
from datetime import datetime, timezone

import boto3

SENSOR_IDS = ('ST-01', 'ST-02', 'ST-03', 'ST-04')
LOCATIONS = (
    'Lote_Norte_Arabica',
    'Lote_Sur_Robusta',
    'Lote_Este_Catuai',
)
MAX_COUNT = 100
MAX_INTERVAL_SECONDS = 60
AWS_REGION = os.environ.get('AWS_REGION') or os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')

lambda_client = boto3.client('lambda', region_name=AWS_REGION)


def handler(event, context):
    del context
    try:
        body = json.loads(event.get('body') or '{}')
        count = int(body.get('count', 1))
        interval = float(body.get('interval', 2))
        seed = body.get('seed')
        if seed is not None:
            seed = int(seed)
        if not 1 <= count <= MAX_COUNT:
            raise ValueError(f'count must be between 1 and {MAX_COUNT}')
        if not 0 <= interval <= MAX_INTERVAL_SECONDS:
            raise ValueError(
                f'interval must be between 0 and {MAX_INTERVAL_SECONDS} seconds'
            )
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        return _response(400, {'message': f'Invalid simulation parameters: {error}'})

    invocation = lambda_client.invoke(
        FunctionName=os.environ['SIMULATOR_WORKER_FUNCTION_NAME'],
        InvocationType='Event',
        Payload=json.dumps({
            'count': count,
            'interval': interval,
            'seed': seed,
        }).encode(),
    )
    return _response(202, {
        'message': 'IoT simulation started',
        'count': count,
        'interval': interval,
        'request_id': invocation['ResponseMetadata']['RequestId'],
    })


def worker(event, context):
    del context
    generator = random.Random(event.get('seed'))
    iot = _iot_client()
    published = 0
    for index in range(event['count']):
        sensor_id = generator.choice(SENSOR_IDS)
        location = generator.choice(LOCATIONS)
        payload = _build_payload(sensor_id, location, generator)
        iot.publish(
            topic=f'sensors/coffee/{sensor_id}/data',
            qos=0,
            payload=json.dumps(payload).encode('utf-8'),
        )
        published += 1
        if index + 1 < event['count']:
            time.sleep(event['interval'])
    return {'published': published}


def _iot_client():
    endpoint = boto3.client('iot', region_name=AWS_REGION).describe_endpoint(
        endpointType='iot:Data-ATS'
    )['endpointAddress']
    return boto3.client(
        'iot-data',
        endpoint_url=f'https://{endpoint}',
        region_name=AWS_REGION,
    )


def _build_payload(sensor_id, location, generator):
    temp_max = round(generator.uniform(18.0, 35.0), 2)
    temp_min = round(generator.uniform(12.0, temp_max), 2)
    return {
        'location': location,
        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'Temp_Max': temp_max,
        'Temp_Min': temp_min,
        'Humidity': round(generator.uniform(50.0, 95.0), 2),
        'Solar_Radiation': round(generator.uniform(120.0, 750.0), 2),
        'Precipitation_mm': round(generator.uniform(0.0, 30.0), 2),
        'soil_ph': round(generator.uniform(4.6, 6.8), 2),
        'soil_moisture': round(generator.uniform(35.0, 90.0), 2),
        'nutrients_mg_kg': {
            'N': round(generator.uniform(18.0, 70.0), 2),
            'P': round(generator.uniform(6.0, 35.0), 2),
            'K': round(generator.uniform(60.0, 180.0), 2),
        },
    }


def _response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,x-api-key',
            'Access-Control-Allow-Methods': 'POST,OPTIONS',
            'Content-Type': 'application/json',
        },
        'body': json.dumps(body),
    }
