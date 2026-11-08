"""Generate a short-lived QuickSight URL for the dashboard frontend."""

import json
import os

import boto3


_quicksight = boto3.client(
    'quicksight',
    region_name=os.environ.get('AWS_REGION', 'us-east-1'),
)


def handler(event, context):
    del context
    dashboard_id = os.environ['QUICKSIGHT_DASHBOARD_ID']
    account_id = os.environ['QUICKSIGHT_ACCOUNT_ID']
    user_arn = os.environ['QUICKSIGHT_USER_ARN']
    session_lifetime = int(
        os.environ.get('QUICKSIGHT_SESSION_LIFETIME_MINUTES', '60')
    )

    allowed_domains = [
        domain.strip()
        for domain in os.environ.get(
            'QUICKSIGHT_ALLOWED_DOMAINS',
            'http://localhost:8080',
        ).split(',')
        if domain.strip()
    ]
    response = _quicksight.generate_embed_url_for_registered_user(
        AwsAccountId=account_id,
        UserArn=user_arn,
        SessionLifetimeInMinutes=session_lifetime,
        AllowedDomains=allowed_domains,
        ExperienceConfiguration={
            'Dashboard': {
                'InitialDashboardId': dashboard_id,
            },
        },
    )
    return _response(200, {'embedUrl': response['EmbedUrl']})


def _response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,x-api-key',
            'Access-Control-Allow-Methods': 'GET,OPTIONS',
            'Content-Type': 'application/json',
        },
        'body': json.dumps(body),
    }
