def handler(event, context):
    return {
        'statusCode': 204,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type,X-Api-Key',
            'Access-Control-Allow-Methods': 'OPTIONS,POST',
            'Access-Control-Allow-Origin': '*',
        },
        'body': '',
    }
