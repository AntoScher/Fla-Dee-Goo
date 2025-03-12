import pytest
import responses, requests
from app import app
import os
os.environ['CURL_CA_BUNDLE'] = ''



@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# Интеграционный тест полного потока
@responses.activate
def test_full_workflow(client):
    # Мок для OAuth
    responses.add(
        responses.POST,
        'https://oauth2.googleapis.com/token',
        json={'access_token': 'fake_token'},
        status=200,
        verify=False
    )

    # Мокируем Google Sheets API
    responses.add(
        responses.GET,
        'https://sheets.googleapis.com/v4/spreadsheets/TEST_ID/values/Sheet1!A1:D10',
        json={'values': [['data1'], ['data2']]},
        status=200,
        match_querystring = True,
        verify = False
    )
    # Мокируем DeepSeek API
    responses.add(
        responses.POST,
        'https://api.deepseek.com/v1/chat/completions',
        json={'choices': [{'message': 'integration test result'}]},
        status=200,
        verify=False
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
        responses.POST,
        'https://oauth2.googleapis.com/token',
        json={'error': 'invalid_grant', 'error_description': 'Invalid grant'},
        status=400,
        verify=False
    )

    responses.add(  # Добавить мок для запроса к Google Sheets API
        responses.GET,
        'https://sheets.googleapis.com/...',
        status=401,
        verify=False
    )

    response = client.get('/generate_report')
    assert response.status_code == 500

# Тест таймаутов
@responses.activate
def test_api_timeout(client):
    responses.add(
        responses.POST,
        'https://api.deepseek.com/v1/chat/completions',
        body=requests.exceptions.Timeout()
    )

    response = client.post('/chat', json={'message': 'timeout test'})
    assert response.status_code == 504