import json
from urllib.parse import quote_plus

import boto3
from pymongo import MongoClient

secrets_client = boto3.client('secretsmanager')

_CACHE = {}
LEGACY_COLLECTION_ALIASES = {
    'coffeeHistoricalData': 'coffee_measurements',
    'coffeeSensorReadings': 'coffee_measurements',
}


def resolve_collection_name(collection_name):
    return LEGACY_COLLECTION_ALIASES.get(collection_name, collection_name)


def get_collection(secret_name, collection_name):
    target_collection = resolve_collection_name(collection_name)
    if secret_name not in _CACHE:
        secret = json.loads(
            secrets_client.get_secret_value(
                SecretId=secret_name)['SecretString'])
        username = quote_plus(secret['username'])
        password = quote_plus(secret['password'])
        host = secret['host'].rstrip()
        options = 'retryWrites=true&w=majority'
        if '?' in host:
            separator = '&' if not host.endswith('?') else ''
            uri = (f"mongodb+srv://{username}:{password}@{host}"
                   f"{separator}{options}")
        else:
            uri = (f"mongodb+srv://{username}:{password}"
                   f"@{host}/?{options}")
        _CACHE[secret_name] = {
            'client': MongoClient(uri),
            'dbname': secret['dbname'],
        }
    cached = _CACHE[secret_name]
    return cached['client'][cached['dbname']][target_collection]
