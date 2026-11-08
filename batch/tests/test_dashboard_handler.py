import json
import importlib


def test_dashboard_handler_generates_registered_user_embed_url(monkeypatch):
    calls = {}

    class QuickSightStub:
        def generate_embed_url_for_registered_user(self, **kwargs):
            calls.update(kwargs)
            return {'EmbedUrl': 'https://quicksight.example/embed'}

    monkeypatch.setenv('QUICKSIGHT_ACCOUNT_ID', '123456789012')
    monkeypatch.setenv(
        'QUICKSIGHT_USER_ARN',
        'arn:aws:quicksight:us-east-1:123456789012:user/default/test',
    )
    monkeypatch.setenv('QUICKSIGHT_DASHBOARD_ID', 'dashboard-id')
    monkeypatch.setenv(
        'QUICKSIGHT_ALLOWED_DOMAINS',
        'http://localhost:8080',
    )
    monkeypatch.setattr(
        'boto3.client',
        lambda service, region_name=None: QuickSightStub(),
    )
    module = importlib.import_module('src.dashboard.handler')
    module._quicksight = QuickSightStub()

    response = module.handler({}, None)

    assert response['statusCode'] == 200
    assert json.loads(response['body'])['embedUrl'].startswith('https://')
    assert calls['ExperienceConfiguration']['Dashboard'] == {
        'InitialDashboardId': 'dashboard-id',
    }
    assert calls['AllowedDomains'] == ['http://localhost:8080']
