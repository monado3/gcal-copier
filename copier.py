import os.path
import argparse
import json
from typing import List, Dict, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError

# Scope for Google Calendar API access
SCOPES = ['https://www.googleapis.com/auth/calendar']
TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'credentials.json'

def get_calendar_service() -> Optional[Resource]:
    """Authenticates with Google Calendar API and returns the service object."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    try:
        return build('calendar', 'v3', credentials=creds)
    except Exception as error:
        print(f'Failed to build calendar service: {error}')
        return None

def fetch_all_events(service: Resource, calendar_id: str) -> List[Dict]:
    """Fetches all events from the specified calendar, handling pagination."""
    events = []
    page_token = None
    try:
        while True:
            results = service.events().list(calendarId=calendar_id, pageToken=page_token).execute()
            events.extend(results.get('items', []))
            page_token = results.get('nextPageToken')
            if not page_token:
                break
        return events
    except HttpError as error:
        print(f'An error occurred while fetching events from {calendar_id}: {error}')
        return []

def copy_event(service: Resource, event: Dict, destination_calendar_id: str, dry_run: bool = False) -> bool:
    """Copies the specified event to the destination calendar or prints it in dry-run mode."""
    if dry_run:
        print("\n[Dry Run] Event to be copied:")
        print(json.dumps(event, indent=2, ensure_ascii=False))
        print(f"  Destination Calendar ID: {destination_calendar_id}")
        return True
    else:
        try:
            copied_event = service.events().insert(calendarId=destination_calendar_id, body=event).execute()
            print(f"Event '{copied_event.get('htmlLink')}' copied to calendar '{destination_calendar_id}'.")
            return True
        except HttpError as error:
            print(f'An error occurred while copying the event: {error}')
            return False

def main():
    """Copies all events from a source calendar to a destination calendar."""
    parser = argparse.ArgumentParser(description='Copies events from one Google Calendar to another.')
    parser.add_argument('source_calendar_id', help='The ID of the source calendar')
    parser.add_argument('destination_calendar_id', help='The ID of the destination calendar')
    parser.add_argument('--dry-run', action='store_true', help='Print events to be copied without actually copying them.')
    args = parser.parse_args()

    source_calendar_id = args.source_calendar_id
    destination_calendar_id = args.destination_calendar_id
    dry_run = args.dry_run

    service = get_calendar_service()
    if not service:
        return

    events_to_copy = fetch_all_events(service, source_calendar_id)
    total_events = len(events_to_copy)
    successful_copies = 0
    failed_copies = 0

    if events_to_copy:
        for event in events_to_copy:
            if copy_event(service, event, destination_calendar_id, dry_run):
                successful_copies += 1
            else:
                failed_copies += 1
    else:
        print(f'No events found in the source calendar "{source_calendar_id}".')

    print("\n--- Summary ---")
    print(f"Total events processed: {total_events}")
    print(f"Successfully copied: {successful_copies}")
    print(f"Failed to copy: {failed_copies}")

if __name__ == '__main__':
    main()
