import pytest
from unittest.mock import patch, MagicMock
from app import app
import json
import os
import responses
from dotenv import load_dotenv

load_dotenv('.env.test')
os.environ['CURL_CA_BUNDLE'] = ''


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.mark.parametrize("input_data,expected_status,expected_key", [
    ({'message': 'Hello'}, 200, 'choices'),
    ({}, 400, 'error'),
    (None, 415, 'error'),
    ({'message': ''}, 400, 'error'),
])
@patch('app.query_deepseek')
def test_chat_route_validation(mock_deepseek, client, input_data, expected_status, expected_key):
    # Настройка мока
    mock_deepseek.return_value = (
        {'choices': [{'message': {'content': 'test'}}]}
        if expected_status == 200
        else {'error': 'Validation error', 'status_code': expected_status}
    )

    # Отправка запроса
    if input_data is None:
        # Отправляем запрос с неверным Content-Type для 415
        response = client.post(
            '/chat',
            data='not_json',
            headers={'Content-Type': 'text/plain'}
        )
    else:
        response = client.post('/chat', json=input_data)

    # Проверки
    assert response.status_code == expected_status
    assert expected_key in response.get_json()


@responses.activate
@patch('app.query_deepseek')
def test_deepseek_error_propagation(mock_deepseek, client):
    # Настройка мока для ошибки
    mock_deepseek.return_value = {
        'error': 'Service Unavailable',
        'status_code': 503
    }

    response = client.post('/chat', json={'message': 'test'})
    assert response.status_code == 503
    assert response.get_json()['error'] == 'Service Unavailable'


@responses.activate
@patch('app.get_sheet_data')
def test_empty_sheet_data(mock_sheet, client):
    # Мокирование данных
    mock_sheet.return_value = []

    # Мок для DeepSeek API
    responses.add(
        responses.POST,
        'https://api.deepseek.com/v1/chat/completions',
        json={
            'choices': [{
                'message': {'content': 'Сгенерируй отчет на основе следующих данных: []'}
            }]
        },
        status=200
    )

    response = client.get('/generate_report')
    assert response.status_code == 200
    assert 'Сгенерируй отчет' in response.get_json()['choices'][0]['message']['content']