import pytest
from unittest.mock import patch, MagicMock
from app import app
import json
import os

# Отключаем проверку SSL для тестов
os.environ['CURL_CA_BUNDLE'] = ''


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# Тест проверки кодов ответа
@pytest.mark.parametrize("status_code,expected", [
    (200, True),
    (400, False),
    (500, False)
])
@patch('app.query_deepseek')
def test_response_codes(mock_deepseek, client, status_code, expected):
    mock_deepseek.return_value = {'status_code': status_code}
    response = client.post('/chat', json={'message': 'test'})
    assert (response.status_code == 200) == expected


# Тест валидации ввода
@pytest.mark.parametrize("input_data,expected_status,expected_key", [
    ({'message': 'Hello'}, 200, 'choices'),
    ({}, 400, 'error'),
    (None, 415, 'error'),
    ({'message': ''}, 400, 'error'),
])
@patch('app.query_deepseek')
def test_chat_route_validation(mock_deepseek, client, input_data, expected_status, expected_key):
    if input_data is None:
        response = client.post('/chat',
                               data=json.dumps({}),
                               headers={'Content-Type': 'application/json'})
    else:
        response = client.post('/chat', json=input_data)

    assert response.status_code == expected_status
    assert expected_key in response.json


# Тест обработки ошибок DeepSeek
@patch('app.requests.post')
def test_deepseek_error_propagation(mock_post, client):
    mock_post.return_value.status_code = 503
    mock_post.return_value.json.return_value = {'error': 'Service Unavailable'}

    response = client.post('/chat', json={'message': 'test'})

    assert response.status_code == 503
    assert response.json['error'] == 'Service Unavailable'


# Тест пустых данных из Google Sheets
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