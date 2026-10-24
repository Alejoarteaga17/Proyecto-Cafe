import json
import os
import re
import uuid

import boto3


s3_client = boto3.client('s3')
DATA_LAKE_BUCKET_NAME = os.environ['DATA_LAKE_BUCKET_NAME']
PRESIGNED_URL_EXPIRATION_SECONDS = 900
ALLOWED_CONTENT_TYPES = {
    'text/csv',
    'application/csv',
    'application/vnd.ms-excel',
}
DATASET_ID_PATTERN = re.compile(r'^[A-Za-z0-9_-]{1,64}$')


def handler(event, context):
    try:
        request = json.loads(event.get('body') or '{}')
    except json.JSONDecodeError:
        return _response(400, {'message': 'Request body must be valid JSON'})

    file_name = request.get('file_name')
    content_type = request.get('content_type', 'text/csv').lower()
    dataset_id = request.get('dataset_id') or str(uuid.uuid4())

    if not isinstance(file_name, str) or not _is_csv_file(file_name):
        return _response(400, {
            'message': 'file_name must be a CSV file',
        })
    if content_type not in ALLOWED_CONTENT_TYPES:
        return _response(415, {
            'message': 'Only CSV uploads are supported in this pipeline',
            'allowed_content_types': sorted(ALLOWED_CONTENT_TYPES),
        })
    if not isinstance(dataset_id, str) or not DATASET_ID_PATTERN.fullmatch(dataset_id):
        return _response(400, {
            'message': 'dataset_id must contain only letters, numbers, underscores or hyphens',
        })

    key = f'bronze/uploads/{dataset_id}/{uuid.uuid4()}-{file_name}'
    upload_url = s3_client.generate_presigned_url(
        ClientMethod='put_object',
        Params={
            'Bucket': DATA_LAKE_BUCKET_NAME,
            'Key': key,
            'ContentType': content_type,
        },
        ExpiresIn=PRESIGNED_URL_EXPIRATION_SECONDS,
    )

    return _response(200, {
        'upload_url': upload_url,
        'bucket': DATA_LAKE_BUCKET_NAME,
        'key': key,
        'expires_in': PRESIGNED_URL_EXPIRATION_SECONDS,
        'content_type': content_type,
        'upload_method': 'PUT',
    })


def _is_csv_file(file_name):
    return (
        file_name == file_name.strip()
        and '/' not in file_name
        and '\\' not in file_name
        and file_name.lower().endswith('.csv')
    )


def _response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(body),
    }
