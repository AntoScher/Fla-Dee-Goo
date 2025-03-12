from flask import Flask, request, jsonify
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import requests
import os

app = Flask(__name__)

# Настройки для Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = 'ваш_spreadsheet_id'
RANGE_NAME = 'Sheet1!A1:D10'

# Настройки для DeepSeek API
DEEPSEEK_API_KEY = 'ваш_api_key'
DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions'

# Функция для авторизации в Google Sheets API
def authenticate_google_sheets():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
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
    response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data)
    return response.json()

# Маршрут для обработки запросов от клиентов
@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    # Генерация ответа с помощью DeepSeek
    response = query_deepseek(user_input)
    return jsonify(response)

# Маршрут для генерации отчетов
@app.route('/generate_report', methods=['GET'])
def generate_report():
    # Получение данных из Google Sheets
    data = get_sheet_data()
    # Генерация отчета с помощью DeepSeek
    report_prompt = "Сгенерируй отчет на основе следующих данных: " + str(data)
    report = query_deepseek(report_prompt)
    return jsonify(report)

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