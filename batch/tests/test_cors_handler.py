from src.validate_and_store.cors_handler import handler


def test_cors_handler_returns_preflight_response():
    response = handler({}, None)

    assert response == {
        'statusCode': 204,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type,X-Api-Key',
            'Access-Control-Allow-Methods': 'OPTIONS,POST',
            'Access-Control-Allow-Origin': '*',
        },
        'body': '',
    }
