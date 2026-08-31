import datetime as dt
import json
import os

import boto3

from src.common import mongo
from src.common.coffee_batch_validator import BatchValidationError, validate_row

sqs_client = boto3.client('sqs')

MONGO_CREDENTIALS_SECRET_NAME = os.environ['MONGO_CREDENTIALS_SECRET_NAME']
COFFEE_BATCH_DLQ_URL = os.environ['COFFEE_BATCH_DLQ_URL']

MONGO_COLLECTION_NAME = 'coffeeHistoricalData'


def handler(event, context):
    for record in event['Records']:
        _process_record(record)


def _process_record(record):
    row = json.loads(record['body'])
    try:
        row = validate_row(row)
    except BatchValidationError as error:
        _send_to_dlq(row, error.errors)
        return

    now = dt.datetime.now(dt.timezone.utc).isoformat()
    document = dict(row)
    document['created_at'] = now
    document['updated_at'] = now

    collection = mongo.get_collection(MONGO_CREDENTIALS_SECRET_NAME,
                                      MONGO_COLLECTION_NAME)
    collection.insert_one(document)


def _send_to_dlq(row, errors):
    body = dict(row)
    body['validation_errors'] = errors
    sqs_client.send_message(QueueUrl=COFFEE_BATCH_DLQ_URL,
                            MessageBody=json.dumps(body))
