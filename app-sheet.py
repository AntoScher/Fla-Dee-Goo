from flask import Flask, request, jsonify, render_template
from flask_wtf.csrf import CSRFProtect
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import requests
import os
from dotenv import load_dotenv
import logging

# Настройка логов
logging.basicConfig(level=logging.INFO)

# Загрузка переменных окружения
load_dotenv()

# Инициализация приложения
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')
csrf = CSRFProtect(app)

# Конфигурация API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
RANGE_NAME = 'Sheet1!A1:D4'
def google_auth():
    """Аутентификация в Google Sheets API"""
    creds = None
    try:
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    raise FileNotFoundError("credentials.json not found")

                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)

            with open('token.json', 'w') as token_file:
                token_file.write(creds.to_json())

        return creds

    except Exception as e:
        logging.error(f"Google Auth Error: {str(e)}")
        raise


def get_sheet_data():
    """Получение данных из Google Sheets"""
    try:
        service = build('sheets', 'v4', credentials=google_auth())
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        return result.get('values', [])

    except HttpError as e:
        logging.error(f"Google Sheets API Error: {str(e)}")
        return []
    except Exception as e:
        logging.error(f"General Error: {str(e)}")
        return []

@app.route('/generate_report', methods=['GET'])
def generate_report():
    """Генерация отчета"""
    try:
        data = get_sheet_data()
        print(f"Получены данные из таблицы: {data}")  # Добавьте эту строку
        if not data:
            return jsonify({'error': 'No data found in sheet'}), 404
        response =service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        )
        #response = query_deepseek(f"Сгенерируй детальный отчет на основе данных: {data}")
        return jsonify(response)

    except Exception as e:
        logging.error(f"Report Generation Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        ssl_context=None
    )