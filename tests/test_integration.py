import pytest
import responses, requests
from unittest.mock import patch, MagicMock
from app import app
import json


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@responses.activate
@patch('app.authenticate_google_sheets')
def test_full_workflow(mock_auth, client):
    # Мокируем аутентификацию Google
    mock_creds = MagicMock()
    mock_creds.valid = True
    mock_auth.return_value = mock_creds

    # Мокируем внешние сервисы
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
@patch('app.authenticate_google_sheets')
def test_google_auth_failure(mock_auth, client):
    # Мокируем ошибку аутентификации
    mock_auth.side_effect = Exception("Auth error")

    response = client.get('/generate_report')
    assert response.status_code == 500
    assert b'Auth error' in response.data


@responses.activate
def test_api_timeout(client):
    # Мокируем таймаут API
    responses.add(
        responses.POST,
        'https://api.deepseek.com/v1/chat/completions',
        body=requests.exceptions.Timeout()
    )

    response = client.post('/chat', json={'message': 'timeout test'})
    assert response.status_code == 504
    assert b'Timeout' in response.data