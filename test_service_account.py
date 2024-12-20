import os
import json
from googleapiclient.discovery import build
from google.oauth2 import service_account
from dotenv import load_dotenv

# Load environment variables from .env (for local development)
load_dotenv()

# Get the path or content of the service account JSON
service_account_path_or_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON', '~/.secrets/service-account.json')

try:
    # Check if the value is a JSON string (for GitHub Actions)
    service_account_info = json.loads(service_account_path_or_json)
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=['https://www.googleapis.com/auth/calendar.readonly']
    )
except json.JSONDecodeError:
    # If it's not JSON, assume it's a file path (for local development)
    service_account_path = os.path.expanduser(service_account_path_or_json)
    credentials = service_account.Credentials.from_service_account_file(
        service_account_path,
        scopes=['https://www.googleapis.com/auth/calendar.readonly']
    )

# Example usage (list calendar events)
calendar_id = 'your_calendar_id@group.calendar.google.com'
service = build('calendar', 'v3', credentials=credentials)
events_result = service.events().list(
    calendarId=calendar_id, 
    timeMin='2024-01-01T00:00:00Z', 
    maxResults=10, 
    singleEvents=True, 
    orderBy='startTime'
).execute()

events = events_result.get('items', [])
print(f"Found {len(events)} events.")
for event in events:
    start = event['start'].get('dateTime', event['start'].get('date'))
    print(f"{start} - {event['summary']}")
