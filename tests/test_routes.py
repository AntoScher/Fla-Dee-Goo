import pytest
from unittest.mock import patch, MagicMock
from app import app
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


@pytest.mark.parametrize("input_data,expected_status,expected_key", [
    ({'message': 'Hello'}, 200, 'choices'),
    ({}, 400, 'error'),
    (None, 415, 'error'),  # Исправлено с 400 на 415
    ({'message': ''}, 400, 'error'),
])
@patch('app.query_deepseek')
def test_chat_route_validation(mock_deepseek, client, input_data, expected_status, expected_key):
    # Настройка мока
    if expected_status == 200:
        mock_deepseek.return_value = {'choices': [{'message': {'content': 'test'}}]}
    else:
        mock_deepseek.return_value = {'error': 'test error', 'status_code': expected_status}

    # Отправка запроса
    if input_data is None:
        response = client.post(
            '/chat',
            data=json.dumps({}),
            headers={'Content-Type': 'application/json'}
        )
    else:
        response = client.post('/chat', json=input_data)

    # Проверки
    assert response.status_code == expected_status
    assert expected_key in response.json


@patch('app.query_deepseek')
def test_deepseek_error_propagation(mock_deepseek, client):
    mock_deepseek.return_value = {
        'error': 'Service Unavailable',
        'status_code': 503
    }
    response = client.post('/chat', json={'message': 'test'})
    assert response.status_code == 503
    assert response.json['error'] == 'Service Unavailable'

"""
@patch('app.requests.post')
def test_deepseek_error_propagation(mock_post, client):
    # Создаем mock-объект с нужными атрибутами
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.json.return_value = {'error': 'Service Unavailable'}
    mock_post.return_value = mock_response

    response = client.post('/chat', json={'message': 'test'})
    assert response.status_code == 503
    assert response.json['error'] == 'Service Unavailable'


@pytest.mark.parametrize("input_data,expected_status,expected_key", [
    ({'message': 'Hello'}, 200, 'choices'),
    ({}, 400, 'error'),
    (None, 415, 'error'),
    ({'message': ''}, 400, 'error'),
])
@patch('app.query_deepseek')
def test_chat_route_validation(mock_deepseek, client, input_data, expected_status, expected_key):
    if expected_status == 200:
        mock_deepseek.return_value = {'choices': [{'message': {'content': 'test'}}]}
    else:
        mock_deepseek.return_value = {'error': 'Invalid request', 'status_code': expected_status}

    if input_data is None:
        response = client.post('/chat',
                               data=json.dumps({}),
                               headers={'Content-Type': 'application/json'})
    else:
        response = client.post('/chat', json=input_data)

    assert response.status_code == expected_status
    assert expected_key in response.json

@patch('app.requests.post')
def test_deepseek_error_propagation(mock_post, client):
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.json.return_value = {'error': 'Service Unavailable'}
    mock_post.return_value = mock_response

    response = client.post('/chat', json={'message': 'test'})
    assert response.status_code == 503
    assert response.json['error'] == 'Service Unavailable'
"""

@patch('app.query_deepseek')
@patch('app.get_sheet_data')
def test_empty_sheet_data(mock_sheet, mock_deepseek, client):
    mock_sheet.return_value = []
    mock_deepseek.return_value = {
        'choices': [{
            'message': {
                'content': 'Сгенерируй отчет на основе следующих данных: []'
            }
        }]
    }

    response = client.get('/generate_report')
    assert response.status_code == 200
    assert 'Сгенерируй отчет' in response.json['choices'][0]['message']['content']