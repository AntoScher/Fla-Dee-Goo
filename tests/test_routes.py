import pytest
from unittest.mock import patch, MagicMock
from app import app
import json

import pytest


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


@patch('app.authenticate_google_sheets')
def test_your_test_name(mock_auth):
    # Заглушка для учетных данных
    mock_creds = MagicMock()
    mock_creds.valid = True
    mock_auth.return_value = mock_creds

    # Остальная часть теста

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# Параметризация для разных сценариев ввода

@pytest.mark.parametrize("input_data,expected_status,expected_key", [
    ({'message': 'Hello'}, 200, 'response'),
    ({}, 400, 'error'),
    (None, 415, 'error'),
    ({'message': ''}, 400, 'error'),
])

#@pytest.mark.parametrize("error_code", [400, 500, 502])
#def test_error_responses(error_code):

@patch('app.query_deepseek')
def test_chat_route_validation(mock_deepseek, client, input_data, expected_status, expected_key):
    # Настройка мока для успешных случаев
    if expected_status == 200:
        mock_deepseek.return_value = {'response': 'test', 'status_code': 200}
    else:
        mock_deepseek.return_value = {}  # Заглушка для ошибок
    # Вызов эндпоинта
    response = client.post('/chat', json=input_data)

    # Проверки
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


# Тест формирования промпта для отчетов
@patch('app.query_deepseek')
@patch('app.get_sheet_data')
def test_report_prompt_generation(mock_sheet, mock_deepseek, client):
    mock_sheet.return_value = [['test_data']]
    mock_deepseek.return_value = {'report': 'OK'}

    response = client.get('/generate_report')

    mock_deepseek.assert_called_once_with(
        "Сгенерируй отчет на основе следующих данных: [['test_data']]"
    )
    assert response.status_code == 200


# Тест пустых данных из Google Sheets
@patch('app.get_sheet_data')
def test_empty_sheet_data(mock_sheet, client):
    mock_sheet.return_value = []

    response = client.get('/generate_report')

    assert response.status_code == 200
    assert 'Сгенерируй отчет на основе следующих данных: []' in response.json['report']['messages'][0]['content']