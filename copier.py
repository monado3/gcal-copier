import os.path
import argparse
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Scope for Google Calendar API access
SCOPES = ['https://www.googleapis.com/auth/calendar']

def copy_event(service, event, destination_calendar_id, dry_run=False):
    """Copies the specified event to the specified calendar.

    Args:
        service: Google Calendar API service object.
        event: The event data to copy (dictionary).
        destination_calendar_id: The ID of the destination calendar.
        dry_run: If True, prints the event information instead of copying.

    Returns:
        True if the event was (or would be) copied successfully, False otherwise.
    """
    if dry_run:
        print(f"\n[Dry Run] Event to be copied:")
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
    """Copies all events from one calendar to another and prints the counts of successful and failed copies."""
    parser = argparse.ArgumentParser(description='Copies events from one Google Calendar to another.')
    parser.add_argument('source_calendar_id', help='The ID of the source calendar')
    parser.add_argument('destination_calendar_id', help='The ID of the destination calendar')
    parser.add_argument('--dry-run', action='store_true', help='Print events to be copied without actually copying them.')
    args = parser.parse_args()

    source_calendar_id = args.source_calendar_id
    destination_calendar_id = args.destination_calendar_id
    dry_run = args.dry_run

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)

        # Get all events from the source calendar
        events_result = service.events().list(calendarId=source_calendar_id).execute()
        events = events_result.get('items', [])
        print(f"Fetch events from the source calendar: {len(events)}")


        successful_copies = 0
        failed_copies = 0

        if events:
            for event_to_copy in events:
                if copy_event(service, event_to_copy, destination_calendar_id, dry_run):
                    successful_copies += 1
                else:
                    failed_copies += 1
        else:
            print(f'No events found in the source calendar "{source_calendar_id}".')

        print(f"\n--- Summary ---")
        print(f"Total events processed: {len(events)}")
        print(f"Successfully copied: {successful_copies}")
        print(f"Failed to copy: {failed_copies}")

    except HttpError as error:
        print(f'An API error occurred: {error}')

if __name__ == '__main__':
    main()
