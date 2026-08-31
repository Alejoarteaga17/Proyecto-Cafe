import datetime as dt
import json
import os

import boto3

from src.common import mongo
from src.common.coffee_rules import build_alert_summary, validate_coffee_reading

sqs_client = boto3.client('sqs')

MONGO_CREDENTIALS_SECRET_NAME = os.getenv('MONGO_CREDENTIALS_SECRET_NAME')
SENSOR_READINGS_DLQ_URL = os.getenv('SENSOR_READINGS_DLQ_URL')

MONGO_COLLECTION_NAME = 'coffeeSensorReadings'


class PayloadValidationError(ValueError):
    """Raised when a sensor payload is malformed or fails validation."""


def handler(event, context):
    for record in event.get('Records', []):
        _process_record(record)


def _process_record(record):
    reading = _parse_reading(record)
    errors = validate_coffee_reading(reading)
    if errors:
        _send_to_dlq(reading, errors)
        raise PayloadValidationError(
            f'Invalid sensor reading: {errors}'
        )

    alert_summary = build_alert_summary(reading)
    validation_status = {
        'status': 'ok',
        'errors': [],
        'warnings': alert_summary.get('warnings', []),
    }
    if alert_summary['status'] == 'alert':
        reading['alert_summary'] = alert_summary
        validation_status['status'] = 'alert'
        validation_status['warnings'] = alert_summary.get('warnings', [])

    now = dt.datetime.now(dt.timezone.utc).isoformat()
    document = dict(reading)
    document['validation'] = validation_status
    document['is_alert'] = alert_summary['status'] == 'alert'
    document['created_at'] = now
    document['updated_at'] = now
    document['source'] = 'iot_sensor'

    collection = mongo.get_collection(MONGO_CREDENTIALS_SECRET_NAME,
                                      MONGO_COLLECTION_NAME)
    collection.insert_one(document)


def _parse_reading(record):
    if not isinstance(record, dict):
        raise PayloadValidationError('SQS record is not a JSON object')

    body = record.get('body')
    if body is None:
        raise PayloadValidationError('SQS record is missing the message body')

    try:
        reading = json.loads(body)
    except (TypeError, ValueError) as exc:
        _send_to_dlq({'raw_body': body, 'error': 'Malformed JSON payload'},
                     ['Malformed JSON payload'])
        raise PayloadValidationError(
            f'Malformed sensor payload: {exc}'
        ) from exc

    if not isinstance(reading, dict):
        raise PayloadValidationError('Sensor payload must be a JSON object')

    if 'thing_name' in reading and 'sensor_id' not in reading:
        reading['sensor_id'] = reading.pop('thing_name')

    return reading


def _send_to_dlq(reading, errors):
    if not SENSOR_READINGS_DLQ_URL:
        raise RuntimeError('SENSOR_READINGS_DLQ_URL is not configured')

    body = dict(reading)
    body['validation_errors'] = list(errors)
    sqs_client.send_message(QueueUrl=SENSOR_READINGS_DLQ_URL,
                            MessageBody=json.dumps(body))
