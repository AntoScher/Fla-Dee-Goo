from flask import Flask, jsonify, render_template, abort
from flask_wtf.csrf import CSRFProtect
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from jinja2.exceptions import TemplateNotFound
import os
from dotenv import load_dotenv
import logging
from cachetools import cached, TTLCache

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Инициализация
load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
#csrf = CSRFProtect(app)

# Конфигурация
CACHE = TTLCache(maxsize=100, ttl=300)
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


class GoogleSheetService:
    def __init__(self):
        self.spreadsheet_id = os.getenv("SPREADSHEET_ID")
        if not self.spreadsheet_id:
            raise ValueError("SPREADSHEET_ID environment variable is missing")

    def _authenticate(self):
        """Google Sheets API Authentication"""
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
            logging.error(f"Auth error: {str(e)}")
            raise

    @cached(CACHE)
    def get_data(self, range_name='Sheet1!A1:D4'):
        try:
            creds = self._authenticate()
            service = build('sheets', 'v4', credentials=creds)
            result = service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            return result.get('values', [])
        except HttpError as e:
            logging.error(f"API Error: {e}")
            raise
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            return []


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Service is running"}), 200


@app.route('/app-test')
def app_test_page():
    """Отображает HTML-страницу"""
    try:
        template_path = os.path.join(app.root_path, 'templates', 'app-test.html')
        logging.info(f"Trying to render template at: {template_path}")

        if not os.path.exists(template_path):
            logging.error(f"Template file not found at: {template_path}")
            abort(404)

        return render_template('app-test.html')

    except TemplateNotFound as e:
        logging.error(f"Template not found: {str(e)}")
        abort(404)
    except Exception as e:
        logging.error(f"Error rendering template: {str(e)}")
        abort(500)


@app.route('/api/generate-report')
def generate_report():
    """Генерирует отчет в формате JSON"""
    try:
        sheet_service = GoogleSheetService()
        data = sheet_service.get_data()

        if not data:
            return jsonify({'error': 'No data available'}), 404

        return jsonify({
            'status': 'success',
            'data': data,
            'metadata': {
                'count': len(data),
                'columns': ['A', 'B', 'C', 'D']
            }
        })
    except Exception as e:
        logging.error(f"Report error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    if not os.getenv("SPREADSHEET_ID"):
        logging.error("SPREADSHEET_ID environment variable is required!")
        exit(1)

    # Проверка существования шаблона
    template_path = os.path.join(app.root_path, 'templates', 'app-test.html')
    if not os.path.exists(template_path):
        logging.error(f"Template file not found at: {template_path}")
        exit(1)

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
    )