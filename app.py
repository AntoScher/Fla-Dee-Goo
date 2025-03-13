from flask import Flask, request, jsonify
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Конфигурация
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
RANGE_NAME = 'Sheet1!A1:D10'
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions'


def authenticate_google_sheets():
    creds = None
    token_path = 'tests/token.json'

    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as e:
            app.logger.error(f"Error loading credentials: {str(e)}")

    if not creds or not creds.valid:
        try:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'tests/credentials.json', SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        except Exception as e:
            app.logger.error(f"Authentication failed: {str(e)}")
            raise

    return creds


def get_sheet_data():
    try:
        creds = authenticate_google_sheets()
        service = build('sheets', 'v4', credentials=creds)
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        return result.get('values', [])
    except Exception as e:
        app.logger.error(f"Sheet data error: {str(e)}")
        raise


def query_deepseek(prompt):
    try:
        response = requests.post(
            DEEPSEEK_API_URL,
            headers={
                'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'deepseek-chat',
                'messages': [{'role': 'user', 'content': prompt}]
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {'error': 'Timeout', 'status_code': 504}
    except Exception as e:
        return {
            'error': str(e),
            'status_code': e.response.status_code if hasattr(e, 'response') else 500
        }


@app.route('/chat', methods=['POST'])
def chat():
    if not request.is_json:
        return jsonify({'error': 'Invalid content type'}), 415

    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Missing message'}), 400

    try:
        response = query_deepseek(data['message'])
        status_code = response.get('status_code', 200)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/generate_report', methods=['GET'])
def generate_report():
    try:
        data = get_sheet_data()
        report = query_deepseek(f"Сгенерируй отчет на основе данных: {data}")
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/analytics', methods=['GET'])
def analytics():
    try:
        data = get_sheet_data()
        analysis = query_deepseek(f"Проанализируй данные: {data}")
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)