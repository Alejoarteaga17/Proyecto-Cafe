import json

from src.iot_simulator import handler as simulator


class LambdaStub:
    def __init__(self):
        self.calls = []

    def invoke(self, **kwargs):
        self.calls.append(kwargs)
        return {'ResponseMetadata': {'RequestId': 'request-123'}}


def test_simulation_starts_async_worker(monkeypatch):
    client = LambdaStub()
    monkeypatch.setattr(simulator, 'lambda_client', client)
    monkeypatch.setenv(
        'SIMULATOR_WORKER_FUNCTION_NAME',
        'coffee-cultivation-backend-batch-IotSimulationWorker',
    )

    response = simulator.handler({
        'body': json.dumps({'count': 3, 'interval': 2, 'seed': 7}),
    }, None)

    assert response['statusCode'] == 202
    assert json.loads(response['body'])['request_id'] == 'request-123'
    assert client.calls[0]['InvocationType'] == 'Event'
    assert json.loads(client.calls[0]['Payload']) == {
        'count': 3,
        'interval': 2,
        'seed': 7,
    }


def test_simulation_rejects_invalid_limits(monkeypatch):
    client = LambdaStub()
    monkeypatch.setattr(simulator, 'lambda_client', client)

    response = simulator.handler({'body': '{"count": 101, "interval": 0}'}, None)

    assert response['statusCode'] == 400
    assert not client.calls
