import pytest
from unittest.mock import patch, MagicMock
from app import app, query_deepseek, get_sheet_data
import responses
import json
import os
os.environ['CURL_CA_BUNDLE'] = ''


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


# Тест 1: Mocking для Google Sheets
@patch('app.build')
@patch('app.authenticate_google_sheets')
def test_get_sheet_data(mock_auth, mock_build):
    # Настройка моков
    mock_sheet = MagicMock()
    mock_build.return_value.spreadsheets.return_value = mock_sheet
    mock_sheet.values.return_value.get.return_value.execute.return_value = {
        'values': [[1, 2], [3, 4]]
    }

    # Вызов функции
    result = get_sheet_data()

    # Проверки
    assert result == [[1, 2], [3, 4]]
    mock_auth.assert_called_once()


# Тест 2: Mocking для DeepSeek API
@patch('app.requests.post')
def test_query_deepseek(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {'choices': [{'message': {'content': 'test'}}]}
    mock_post.return_value = mock_response

    result = query_deepseek("test prompt")

    assert 'test' in result['choices'][0]['message']['content']
    mock_post.assert_called_once_with(
        'https://api.deepseek.com/v1/chat/completions',
        headers={
            'Authorization': 'Bearer DEEPSEEK_API_KEY-111',
            'Content-Type': 'application/json'
        },
        json={
            'model': 'deepseek-chat',
            'messages': [{'role': 'user', 'content': 'test prompt'}]
        },
        timeout=10
    )

# Тест 3: Интеграционный тест для /chat
@patch('app.query_deepseek')
def test_chat_route(mock_deepseek, client):
    # Настройка мока
    mock_deepseek.return_value = {'response': 'test response'}

    # Вызов эндпоинта
    response = client.post('/chat', json={'message': 'hello'})

    # Проверки
    assert response.status_code == 200
    assert b'test response' in response.data


# Тест 4: Тест обработки ошибок
@patch('app.requests.post')
def test_api_error_handling(mock_post, client):
    mock_post.return_value.status_code = 500
    mock_post.return_value.json.return_value = {
        'error': 'Internal error',
        'status_code': 500  # Добавьте это
    }
    response = client.post('/chat', json={'message': 'test'})
    assert response.status_code == 500  # Теперь тест пройдет


# Тест 5: Проверка формирования промпта
@patch('app.query_deepseek')
@patch('app.get_sheet_data')
def test_report_generation(mock_sheet, mock_deepseek, client):
    # Настройка моков
    mock_sheet.return_value = [['data']]
    mock_deepseek.return_value = {'report': 'test report'}

    response = client.get('/generate_report')

    # Проверка формирования промпта
    expected_prompt = "Сгенерируй отчет на основе следующих данных: [['data']]"
    mock_deepseek.assert_called_once_with(expected_prompt)
    assert b'test report' in response.data


# Тест 6: Использование responses
@responses.activate
def test_analytics_route(client):
    # Мок для OAuth токена
    responses.add(
        responses.POST,
        'https://oauth2.googleapis.com/token',
        json={'access_token': 'fake_token'},
        status=200,
        verify=False
    )

    # Мок для Google Sheets
    responses.add(
        responses.GET,
        'https://sheets.googleapis.com/v4/spreadsheets/ваш_spreadsheet_id/values/Sheet1!A1:D10',
        json={'values': [[1], [2]]},
        status=200,
        verify=False
    )

    # Мок для DeepSeek
    responses.add(
        responses.POST,
        'https://api.deepseek.com/v1/chat/completions',
        json={'choices': [{'message': {'content': 'analytics result'}}]},
        status=200,
        verify=False
    )

    response = client.get('/analytics')
    assert response.status_code == 200