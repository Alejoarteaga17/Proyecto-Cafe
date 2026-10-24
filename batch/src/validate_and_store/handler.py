import base64
import binascii
import csv
import io
import json
import os
import uuid

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

DEFAULT_IMPUTATIONS = {
    'Temp_Max': 22.0,
    'Temp_Min': 18.0,
    'Humidity': 70.0,
    'Solar_Radiation': 450.0,
    'Precipitation_mm': 0.0,
    'Close_USD_60kg': 0.0,
    'brl': 1.0,
    'cny': 1.0,
    'mxn': 1.0,
}



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
    missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
    if missing:
        raise ValueError(f'Missing required column(s): {", ".join(missing)}')

    cleaned_rows = []
    for row_number, row in enumerate(reader, start=2):
        cleaned_row = {}
        for column in REQUIRED_COLUMNS:
            value = row.get(column)
            if value is None or (isinstance(value, str) and not value.strip()):
                cleaned_row[column] = DEFAULT_IMPUTATIONS.get(column, 0)
            else:
                cleaned_row[column] = value.strip()
        if cleaned_row['Location'] == 'nan':
            cleaned_row['Location'] = 'Unknown_Location'
        cleaned_rows.append(cleaned_row)

    if not cleaned_rows:
        raise ValueError('CSV file has no data rows')
    return cleaned_rows


def _response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body),
    }
