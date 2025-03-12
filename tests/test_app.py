import pytest
from unittest.mock import patch, MagicMock
from app import app, query_deepseek, get_sheet_data
import responses
import json
import os

from dotenv import load_dotenv
load_dotenv('.env.test')  # Явно указываем файл для тестов

os.environ['CURL_CA_BUNDLE'] = ''

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@patch('app.build')
@patch('app.authenticate_google_sheets')
def test_get_sheet_data(mock_auth, mock_build):
    mock_sheet = MagicMock()
    mock_build.return_value.spreadsheets.return_value = mock_sheet
    mock_sheet.values.return_value.get.return_value.execute.return_value = {
        'values': [[1, 2], [3, 4]]
    }
    result = get_sheet_data()
    assert result == [[1, 2], [3, 4]]
    mock_auth.assert_called_once()

@patch('app.requests.post')
def test_query_deepseek(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {'choices': [{'message': {'content': 'test'}}]}
    mock_post.return_value = mock_response

    result = query_deepseek("test prompt")
    assert 'test' in result['choices'][0]['message']['content']

@patch('app.query_deepseek')
def test_chat_route(mock_deepseek, client):
    mock_deepseek.return_value = {'choices': [{'message': {'content': 'test response'}}]}
    response = client.post('/chat', json={'message': 'hello'})
    assert response.status_code == 200
    assert b'test response' in response.data
@responses.activate
def test_analytics_route(client):
    # Мок для OAuth токена
    responses.add(
        responses.POST,
        'https://oauth2.googleapis.com/token',
        json={'access_token': 'fake_token'},
        status=200
    )

    # Мок для Google Sheets
    responses.add(
        responses.GET,
        'https://sheets.googleapis.com/v4/spreadsheets/TEST_ID/values/Sheet1!A1:D10',
        json={'values': [[1], [2]]},
        status=200
    )

    # Мок для DeepSeek
    responses.add(
        responses.POST,
        'https://api.deepseek.com/v1/chat/completions',
        json={'choices': [{'message': {'content': 'analytics result'}}]},
        status=200
    )

    # Мок для аутентификации Google
    with patch('google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file') as mock_flow:
        mock_creds = MagicMock()
        mock_flow.return_value.run_local_server.return_value = mock_creds

        response = client.get('/analytics')
        assert response.status_code == 200

"""
@responses.activate
def test_analytics_route(client):
    responses.add(
        responses.POST,
        'https://oauth2.googleapis.com/token',
        json={'access_token': 'fake_token'},
        status=200
    )

    responses.add(
        responses.GET,
        'https://sheets.googleapis.com/v4/spreadsheets/TEST_ID/values/Sheet1!A1:D10',
        json={'values': [[1], [2]]},
        status=200
    )

    responses.add(
        responses.POST,
        'https://api.deepseek.com/v1/chat/completions',
        json={'choices': [{'message': {'content': 'analytics result'}}]},
        status=200
    )

    response = client.get('/analytics')
    assert response.status_code == 200
"""