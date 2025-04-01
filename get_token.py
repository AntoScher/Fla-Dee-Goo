from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json
import os
from dotenv import load_dotenv
import ssl

# Временное отключение проверки SSL (для тестов!)
ssl._create_default_https_context = ssl._create_unverified_context

load_dotenv()


def test_google_sheets():
    try:
        tokens_str = os.getenv("GOOGLE_TOKENS")
        if not tokens_str:
            raise ValueError("GOOGLE_TOKENS не найден!")

        tokens = json.loads(tokens_str)
        creds = Credentials.from_authorized_user_info(tokens)

        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()

        # Тестовые данные (замените на свои!)
        spreadsheet_id = 'ваш_ID_таблицы'
        range_name = 'Sheet1!A1:E10'

        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()

        print("Результат:", result.get('values', [])[:3])

    except Exception as e:
        print(f"Ошибка: {str(e)}")


if __name__ == "__main__":
    test_google_sheets()
"""
r"C:\cacert.pem"
# Создайте сервис для работы с API
service = build('calendar', 'v3', credentials=creds)

# Тестовый запрос: получите список календарей
calendars = service.calendarList().list().execute()
print("Таблица:", calendars.get('items', []))
"""


"""from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

flow = InstalledAppFlow.from_client_secrets_file(
    'credentials.json',
    SCOPES
)
creds = flow.run_local_server(port=0)  # Откроет браузер для авторизации

# Сохраните токен
tokens = {
    "token": creds.token,
    "refresh_token": creds.refresh_token,
    "scopes": creds.scopes
}
print(tokens)  # Скопируйте это в .env как GOOGLE_TOKENS
"""