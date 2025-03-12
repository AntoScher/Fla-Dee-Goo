import pytest
import responses, requests
from app import app



@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# Интеграционный тест полного потока
@responses.activate
def test_full_workflow(client):
    # Мокируем Google Sheets API
    responses.add(
        responses.GET,
        'https://sheets.googleapis.com/v4/spreadsheets/TEST_ID/values/Sheet1!A1:D10',
        json={'values': [['data1'], ['data2']]},
        status=200
    )

    # Мокируем DeepSeek API
    responses.add(
        responses.POST,
        'https://api.deepseek.com/v1/chat/completions',
        json={'choices': [{'message': 'integration test result'}]},
        status=200
    )

    # Вызываем аналитику
    response = client.get('/analytics')

    # Проверяем полную цепочку
    assert response.status_code == 200
    assert b'integration test result' in response.data
    assert len(responses.calls) == 2  # Проверка количества вызовов API


# Тест ошибок авторизации
@responses.activate
def test_google_auth_failure(client):
    responses.add(
        responses.GET,
        'https://sheets.googleapis.com/v4/spreadsheets/TEST_ID/values/Sheet1!A1:D10',
        json={'error': 'Invalid credentials'},
        status=401
    )

    response = client.get('/generate_report')

    assert response.status_code == 500
    assert 'Invalid credentials' in response.json['error']


# Тест таймаутов
@responses.activate
def test_api_timeout(client):
    responses.add(
        responses.POST,
        'https://api.deepseek.com/v1/chat/completions',
        body=requests.exceptions.Timeout(),
        status=504
    )

    response = client.post('/chat', json={'message': 'timeout test'})

    assert response.status_code == 504