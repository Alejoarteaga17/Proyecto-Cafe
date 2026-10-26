import base64
import binascii
import csv
import io
import json
import os
import uuid

from src.common.coffee_batch_validator import BatchValidationError, validate_rows

try:
    import boto3
except ModuleNotFoundError:  # Local tests can inject an S3 client stub.
    boto3 = None

REQUIRED_COLUMNS = [
    'LON',
    'LAT',
    'YEAR',
    'MM',
    'DD',
    'DOY',
    'Date',
    'Temp_Max',
    'Temp_Min',
    'Humidity',
    'Solar_Radiation',
    'Precipitation_mm',
    'Location',
    'Close_USD_60kg',
    'Is_Weekend',
    'Is_Interpolated',
    'brl',
    'cny',
    'mxn',
]

class _UnavailableS3Client:
    def put_object(self, **kwargs):
        raise RuntimeError('boto3 is required to upload to S3')


s3_client = boto3.client('s3') if boto3 else _UnavailableS3Client()

BRONZE_BUCKET_NAME = os.environ.get('BRONZE_BUCKET_NAME', 'coffee-data-lake-bronze')
MAX_FILE_BYTES = 5 * 1024 * 1024


def handler(event, context):
    try:
        payload = json.loads(event.get('body') or '{}')
    except json.JSONDecodeError:
        return _response(400, {
            'message': 'Request body must be valid JSON'
        })

    encoded_file = payload.get('file')
    if not encoded_file:
        return _response(400, {
            'message': '"file" is required'
        })

    try:
        file_bytes = base64.b64decode(encoded_file, validate=True)
    except binascii.Error:
        return _response(400, {
            'message': '"file" is not valid base64'
        })
    if not file_bytes or len(file_bytes) > MAX_FILE_BYTES:
        return _response(413, {
            'message': 'CSV file must be non-empty and no larger than 5 MiB'
        })

    try:
        text = file_bytes.decode('utf-8-sig')
        rows = _parse_csv_rows(text)
    except ValueError as error:
        return _response(400, {
            'message': 'Validation failed',
            'errors': [str(error)],
        })

    report_key = f'bronze/historical/ingested_at={uuid.uuid4()}/{uuid.uuid4()}.csv'
    s3_client.put_object(
        Bucket=BRONZE_BUCKET_NAME,
        Key=report_key,
        Body=text.encode('utf-8'),
        ContentType='text/csv',
    )

    return _response(
        202, {
            'message': 'Coffee historical dataset accepted',
            's3_key': report_key,
            'rows_accepted': len(rows),
        })


def _parse_csv_rows(csv_text):
    reader = csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames is None:
        raise ValueError('CSV file is missing a header row')

    fieldnames = [str(name).strip() for name in reader.fieldnames]
    if len(fieldnames) != len(set(fieldnames)):
        raise ValueError('CSV header contains duplicate columns')
    reader.fieldnames = fieldnames
    missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
    if missing:
        raise ValueError(f'Missing required column(s): {", ".join(missing)}')
    unexpected = [
        column for column in fieldnames if column not in REQUIRED_COLUMNS
    ]
    if unexpected:
        raise ValueError(
            f'CSV contains unexpected column(s): {", ".join(unexpected)}'
        )

    cleaned_rows = []
    for row_number, row in enumerate(reader, start=2):
        if None in row and any(value not in (None, '') for value in row[None]):
            raise ValueError(f'Row {row_number} contains unexpected columns')
        cleaned_rows.append({
            column: (row.get(column) or '').strip()
            for column in REQUIRED_COLUMNS
        })
    try:
        return validate_rows(cleaned_rows)
    except BatchValidationError as error:
        raise ValueError(str(error)) from error


def _response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type,X-Api-Key',
            'Access-Control-Allow-Methods': 'OPTIONS,POST',
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json',
        },
        'body': json.dumps(body),
    }
