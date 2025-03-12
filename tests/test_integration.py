import pytest
import responses
import requests
from app import app

from dotenv import load_dotenv
load_dotenv('.env.test')  # Явно указываем файл для тестов

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@responses.activate
def test_full_workflow(client):
    responses.add(
        responses.POST,
        'https://oauth2.googleapis.com/token',
        json={'access_token': 'fake_token'},
        status=200
    )

    responses.add(
        responses.GET,
        'https://sheets.googleapis.com/v4/spreadsheets/TEST_ID/values/Sheet1!A1:D10',
        json={'values': [['data1'], ['data2']]},
        status=200
    )

    responses.add(
        responses.POST,
        'https://api.deepseek.com/v1/chat/completions',
        json={'choices': [{'message': {'content': 'integration test result'}}]},
        status=200
    )

    response = client.get('/analytics')
    assert response.status_code == 200
    assert b'integration test result' in response.data

@responses.activate
def test_google_auth_failure(client):
    responses.add(
        responses.POST,
        'https://oauth2.googleapis.com/token',
        json={'error': 'invalid_grant', 'error_description': 'Invalid grant'},
        status=400
    )

    response = client.get('/generate_report')
    assert response.status_code == 500

@responses.activate
def test_api_timeout(client):
    responses.add(
        responses.POST,
        'https://api.deepseek.com/v1/chat/completions',
        body=requests.exceptions.Timeout()
    )

    response = client.post('/chat', json={'message': 'timeout test'})
    assert response.status_code == 504