import pytest
import responses
from unittest.mock import patch, MagicMock
from app import app
import requests


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@responses.activate
@patch('app.authenticate_google_sheets')
@patch('app.build')
def test_full_workflow(mock_build, mock_auth, client):
    mock_service = MagicMock()
    mock_service.spreadsheets().values().get().execute.return_value = {
        'values': [['test_data']]
    }
    mock_build.return_value = mock_service

    responses.add(
        responses.POST,
        'https://api.deepseek.com/v1/chat/completions',
        json={'choices': [{'message': {'content': 'success'}}]},
        status=200
    )

    response = client.get('/analytics')
    assert response.status_code == 200
    assert b'success' in response.data


"""@responses.activate
@patch('app.get_sheet_data')
def test_google_auth_failure(mock_sheet, client):
    mock_sheet.side_effect = Exception("Auth error")

    response = client.get('/generate_report')
    assert response.status_code == 500
    assert b'Auth error' in response.data
"""

@responses.activate
@patch('app.get_sheet_data')
def test_google_auth_failure(mock_sheet, client):
    mock_sheet.side_effect = Exception("Auth error")

    response = client.get('/generate_report')

    # Проверяем статус и содержимое JSON
    assert response.status_code == 500
    assert response.get_json() == {'error': 'Auth error'}


@responses.activate
def test_api_timeout(client):
    responses.add(
        responses.POST,
        'https://api.deepseek.com/v1/chat/completions',
        body=requests.exceptions.Timeout()
    )

    response = client.post('/chat', json={'message': 'test'})
    assert response.status_code == 504
    assert b'Timeout' in response.data