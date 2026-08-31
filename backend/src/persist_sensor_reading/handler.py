import datetime as dt
import json
import os

import boto3

from src.common import mongo
from src.common.coffee_rules import build_alert_summary, validate_coffee_reading

sqs_client = boto3.client('sqs')

MONGO_CREDENTIALS_SECRET_NAME = os.environ['MONGO_CREDENTIALS_SECRET_NAME']
SENSOR_READINGS_DLQ_URL = os.environ['SENSOR_READINGS_DLQ_URL']

MONGO_COLLECTION_NAME = 'coffeeSensorReadings'


def handler(event, context):
    for record in event['Records']:
        _process_record(record)


def _process_record(record):
    reading = json.loads(record['body'])
    reading['sensor_id'] = reading.pop('thing_name', reading.get('sensor_id'))
    errors = validate_coffee_reading(reading)
    if errors:
        _send_to_dlq(reading, errors)
        return

    alert_summary = build_alert_summary(reading)
    if alert_summary['status'] == 'alert':
        reading['alert_summary'] = alert_summary

    now = dt.datetime.now(dt.timezone.utc).isoformat()
    document = dict(reading)
    document['created_at'] = now
    document['updated_at'] = now

    collection = mongo.get_collection(MONGO_CREDENTIALS_SECRET_NAME,
                                      MONGO_COLLECTION_NAME)
    collection.insert_one(document)


def _send_to_dlq(reading, errors):
    body = dict(reading)
    body['validation_errors'] = errors
    sqs_client.send_message(QueueUrl=SENSOR_READINGS_DLQ_URL,
                            MessageBody=json.dumps(body))
