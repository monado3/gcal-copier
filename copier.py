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

def modify_event_body(event: Dict, override_color: Optional[str] = None, prepend_description: Optional[str] = None) -> Dict:
    """Modifies the event body with optional color override and description prepending."""
    body = event.copy()
    if override_color:
        body['colorId'] = override_color
        print(f"[Override Color] Setting colorId to '{override_color}' for event: {body.get('summary', 'No Summary')}")

    if prepend_description:
        if 'description' in body:
            body['description'] = prepend_description + body['description']
            print(f"[Prepend Description] Prepended '{prepend_description}' to event: {body.get('summary', 'No Summary')}")
        else:
            body['description'] = prepend_description
            print(f"[Prepend Description] Set description to '{prepend_description}' for event: {body.get('summary', 'No Summary')}")
    return body

def copy_event(service: Resource, event: Dict, destination_calendar_id: str, dry_run: bool = False, override_color: Optional[str] = None, prepend_description: Optional[str] = None) -> bool:
    """Copies the specified event to the destination calendar or prints it in dry-run mode."""
    body = modify_event_body(event, override_color, prepend_description)

    if dry_run:
        print("\n[Dry Run] Event to be copied:")
        print(json.dumps(body, indent=2, ensure_ascii=False))
        print(f"  Destination Calendar ID: {destination_calendar_id}")
        return True
    else:
        try:
            copied_event = service.events().insert(calendarId=destination_calendar_id, body=body).execute()
            print(f"Event {copied_event.get('summary', 'No Summary')} '{copied_event.get('htmlLink')}' copied to calendar '{destination_calendar_id}'.")
            if override_color:
                print(f"  Color overridden to '{override_color}'.")
            if prepend_description:
                print(f"  Description prepended with '{prepend_description}'.")
            return True
        except HttpError as error:
            print(f'An error occurred while copying the event: {error}')
            print(f'Failed event details:')
            print(json.dumps(event, indent=2, ensure_ascii=False))
            return False

def main():
    """Copies all events from a source calendar to a destination calendar."""
    parser = argparse.ArgumentParser(description='Copies events from one Google Calendar to another.')
    parser.add_argument('source_calendar_id', help='The ID of the source calendar')
    parser.add_argument('destination_calendar_id', help='The ID of the destination calendar')
    parser.add_argument('--dry-run', action='store_true', help='Print events to be copied without actually copying them.')
    parser.add_argument('--override-color', help='Override the colorId of the copied events with this value.')
    parser.add_argument('--prepend-description', help='String to prepend to the description of copied events.')
    args = parser.parse_args()

    source_calendar_id = args.source_calendar_id
    destination_calendar_id = args.destination_calendar_id
    dry_run = args.dry_run
    override_color = args.override_color
    prepend_description = args.prepend_description

    service = get_calendar_service()
    if not service:
        return

    events_to_copy = fetch_all_events(service, source_calendar_id)
    total_events = len(events_to_copy)
    successful_copies = 0
    failed_copies = 0

    if events_to_copy:
        for event in events_to_copy:
            if copy_event(service, event, destination_calendar_id, dry_run, override_color, prepend_description):
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
