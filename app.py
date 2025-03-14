from flask import Flask, request, jsonify, render_template
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Добавьте этот код перед if __name__ == '__main__':

@app.route('/')  # 👈 Новый роут для главной страницы
def home():
    return render_template('index.html')  # Рендерим HTML-шаблон

# Настройки для Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID =os.environ.get("SPREADSHEET_ID")
RANGE_NAME = 'Sheet1!A1:D10'

# Настройки для DeepSeek API
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions'

# Функция для авторизации в Google Sheets API
def authenticate_google_sheets():
    creds = None
    if os.path.exists('tests/token.json'):
        creds = Credentials.from_authorized_user_file('tests/token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('tests/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('tests/token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

# Функция для получения данных из Google Sheets
def get_sheet_data():
    creds = authenticate_google_sheets()
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])
    return values

# Функция для отправки запроса в DeepSeek API
def query_deepseek(prompt):
    headers = {
        'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'model': 'deepseek-chat',
        'messages': [{'role': 'user', 'content': prompt}]
    }
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {'error': 'Timeout', 'status_code': 504}
    except requests.exceptions.RequestException as e:
        # Возвращаем статус код из исключения
        return {'error': str(e), 'status_code': e.response.status_code if e.response else 500}

# Маршрут для обработки запросов от клиентов
@app.route('/chat', methods=['POST'])
def chat():
    if not request.is_json:
        return jsonify({'error': 'Invalid content type'}), 415

    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Missing message'}), 400

    user_input = data['message']
    deepseek_response = query_deepseek(user_input)
    status_code = deepseek_response.get('status_code', 200)
    return jsonify(deepseek_response), status_code

@app.route('/generate_report', methods=['GET'])
def generate_report():
    try:
        data = get_sheet_data()
        report_prompt = "Сгенерируй отчет: " + str(data)
        report = query_deepseek(report_prompt)
        return jsonify(report)
    except Exception as e:
        # Явно возвращаем JSON с ошибкой и статусом 500
        return jsonify({'error': str(e)}), 500

# Маршрут для аналитики
@app.route('/analytics', methods=['GET'])
def analytics():
    # Получение данных из Google Sheets
    data = get_sheet_data()
    # Генерация аналитики с помощью DeepSeek
    analytics_prompt = "Проанализируй следующие данные и предоставь аналитику: " + str(data)
    analytics_result = query_deepseek(analytics_prompt)
    return jsonify(analytics_result)



if __name__ == '__main__':
    app.run(debug=True)