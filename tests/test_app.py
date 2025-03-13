import pytest
from unittest.mock import patch, MagicMock
from app import app, query_deepseek, get_sheet_data
import responses
import json
import os
import tempfile
from dotenv import load_dotenv

load_dotenv('.env.test')


@pytest.fixture
def token_file():
    tests_dir = os.path.abspath(os.path.dirname(__file__))
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tf:
        tf.write(json.dumps({
            "access_token": "test",
            "refresh_token": "test",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "test",
            "client_secret": "test",
            "scopes": ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        }))
    yield tf.name
    os.unlink(tf.name)


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@patch('app.build')
@patch('app.authenticate_google_sheets')
def test_get_sheet_data(mock_auth, mock_build):
    mock_service = MagicMock()
    mock_service.spreadsheets().values().get().execute.return_value = {'values': [[1, 2], [3, 4]]}
    mock_build.return_value = mock_service
    assert get_sheet_data() == [[1, 2], [3, 4]]


@patch('app.requests.post')
def test_query_deepseek(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {'choices': [{'message': {'content': 'test'}}]}
    mock_post.return_value = mock_response
    assert 'test' in query_deepseek("test")['choices'][0]['message']['content']


@patch('app.query_deepseek')
def test_chat_route(mock_deepseek, client):
    mock_deepseek.return_value = {'choices': [{'message': {'content': 'test'}}]}
    response = client.post('/chat', json={'message': 'hi'})
    assert response.status_code == 200
    assert b'test' in response.data


@responses.activate
@patch('app.requests.post')
def test_analytics_route(mock_post, client, token_file):
    # Mock внешних сервисов
    responses.add(
        responses.POST,
        'https://oauth2.googleapis.com/token',
        json={'access_token': 'test'},
        status=200
    )
    responses.add(
        responses.GET,
        'https://sheets.googleapis.com/v4/spreadsheets/TEST/values/Sheet1!A1:D10',
        json={'values': [[1], [2]]},
        status=200
    )
    mock_post.return_value.json.return_value = {
        'choices': [{'message': {'content': 'analysis'}}]
    }

    # Mock Google аутентификации и сервисов
    with patch('google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file') as mock_flow, \
            patch('app.authenticate_google_sheets') as mock_auth, \
            patch('app.build') as mock_build:
        mock_service = MagicMock()
        mock_service.spreadsheets().values().get().execute.return_value = {'values': [[1], [2]]}
        mock_build.return_value = mock_service

        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_creds.expired = False
        mock_flow.return_value.run_local_server.return_value = mock_creds
        mock_auth.return_value = mock_creds

        # Mock файловых операций
        with patch('os.path.exists', return_value=True), \
                patch('builtins.open', create=True):
            response = client.get('/analytics')
            assert response.status_code == 200
            assert b'analysis' in response.data