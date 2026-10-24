import base64
import json

from src.validate_and_store import handler as upload_module


CSV = """LON,LAT,YEAR,MM,DD,DOY,Date,Temp_Max,Temp_Min,Humidity,Solar_Radiation,Precipitation_mm,Location,Close_USD_60kg,Is_Weekend,Is_Interpolated,brl,cny,mxn
-75.68,4.53,2026,8,23,234,2026-08-23,25,17,70,500,2,Armenia,160,false,false,5,7,18
"""


class S3Stub:
    def __init__(self):
        self.calls = []

    def put_object(self, **kwargs):
        self.calls.append(kwargs)


def _event(content):
    encoded = base64.b64encode(content.encode()).decode()
    return {'body': json.dumps({'file': encoded})}


def test_upload_writes_raw_csv_to_bronze(monkeypatch):
    s3 = S3Stub()
    monkeypatch.setattr(upload_module, 's3_client', s3)
    monkeypatch.setattr(upload_module, 'BRONZE_BUCKET_NAME', 'test-bronze')

    response = upload_module.handler(_event(CSV), None)
    body = json.loads(response['body'])

    assert response['statusCode'] == 202
    assert body['rows_accepted'] == 1
    assert s3.calls[0]['Bucket'] == 'test-bronze'
    assert s3.calls[0]['Key'].startswith('bronze/historical/ingested_at=')
    assert s3.calls[0]['ContentType'] == 'text/csv'


def test_upload_rejects_missing_required_column(monkeypatch):
    s3 = S3Stub()
    monkeypatch.setattr(upload_module, 's3_client', s3)
    invalid_csv = CSV.replace(',mxn\n', '\n')

    response = upload_module.handler(_event(invalid_csv), None)

    assert response['statusCode'] == 400
    assert 'mxn' in json.loads(response['body'])['errors'][0]
    assert not s3.calls


def test_upload_rejects_oversized_file(monkeypatch):
    s3 = S3Stub()
    monkeypatch.setattr(upload_module, 's3_client', s3)

    response = upload_module.handler(_event('x' * (5 * 1024 * 1024 + 1)), None)

    assert response['statusCode'] == 413
    assert not s3.calls


def test_upload_rejects_invalid_row_values(monkeypatch):
    s3 = S3Stub()
    monkeypatch.setattr(upload_module, 's3_client', s3)
    invalid_csv = CSV.replace('25,17,70', 'not-a-number,17,70')

    response = upload_module.handler(_event(invalid_csv), None)

    assert response['statusCode'] == 400
    assert 'Temp_Max' in json.loads(response['body'])['errors'][0]
    assert not s3.calls


def test_upload_rejects_invalid_date_consistency(monkeypatch):
    s3 = S3Stub()
    monkeypatch.setattr(upload_module, 's3_client', s3)
    invalid_csv = CSV.replace('2026-08-23,25', '2026-08-24,25')

    response = upload_module.handler(_event(invalid_csv), None)

    assert response['statusCode'] == 400
    assert 'Date' in json.loads(response['body'])['errors'][0]
    assert not s3.calls


def test_upload_rejects_duplicate_headers(monkeypatch):
    s3 = S3Stub()
    monkeypatch.setattr(upload_module, 's3_client', s3)
    invalid_csv = CSV.replace(
        'LON,LAT,YEAR',
        'LON,LON,YEAR',
    )

    response = upload_module.handler(_event(invalid_csv), None)

    assert response['statusCode'] == 400
    assert 'duplicate' in json.loads(response['body'])['errors'][0]
    assert not s3.calls


def test_upload_rejects_unexpected_columns(monkeypatch):
    s3 = S3Stub()
    monkeypatch.setattr(upload_module, 's3_client', s3)
    invalid_csv = CSV.replace(
        'mxn\n',
        'mxn,unexpected\n',
    ).replace(
        ',18\n',
        ',18,unexpected-value\n',
    )

    response = upload_module.handler(_event(invalid_csv), None)

    assert response['statusCode'] == 400
    assert 'unexpected column' in json.loads(response['body'])['errors'][0]
    assert not s3.calls
