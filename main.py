import os
import json
from datetime import datetime, timezone
from googleapiclient.discovery import build
from google.oauth2 import service_account
from dotenv import load_dotenv

# Load environment variables from .env (for local development)
load_dotenv()

def get_credentials():
    """Get the credentials for the Google Calendar API."""
    service_account_path_or_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON', '~/.secrets/borrel-calendar-9c562381bf19.json')
    calendar_id = os.getenv('GOOGLE_CALENDAR_ID')

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

    if not calendar_id:
        raise ValueError("GOOGLE_CALENDAR_ID is not set. Make sure it's in the .env file or GitHub Secrets.")
    
    return credentials, calendar_id

def get_events(credentials, calendar_id, max_results=50, time_min=None):
    """Get the events from the Google Calendar API."""
    if time_min is None:
        time_min = datetime.now(timezone.utc).isoformat()

    service = build('calendar', 'v3', credentials=credentials)
    events_result = service.events().list(
        calendarId=calendar_id, 
        timeMin=time_min, 
        maxResults=max_results, 
        singleEvents=True, 
        orderBy='startTime'
    ).execute()

    events = [
        {
            "start": ev['start'].get('dateTime', ev['start'].get('date')),
            "name": ev.get('summary', 'Unnamed Event')
        }
        for ev in events_result.get('items', [])
    ]

    return events

def borrel_info(events):

    current_date = datetime.now(timezone.utc).date()
    borrel_today = False
    days_until_next_borrel = None

    for event in events:
        event_date = datetime.fromisoformat(event["start"]).date()
        if event_date == current_date:
            borrel_today = True
        else:
            days_df = (event_date - current_date).days
            if days_df > 0 and (days_until_next_borrel is None or days_df < days_until_next_borrel):
                days_until_next_borrel = days_df
    return {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "borrel_today": borrel_today,
        "borrel_days": days_until_next_borrel
    }

def write_to_json(borrel_status):
    with open('borrel_status.json', 'w') as f:
        json.dump(borrel_status, f, indent=2)

def main():
    """Main execution logic."""
    try:
        credentials, calendar_id = get_credentials()
        events = get_events(credentials, calendar_id)
        borrel_status = borrel_info(events)
        write_to_json(borrel_status)
        print(f"Found {len(events)} events.")
        print(json.dumps(borrel_status, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
