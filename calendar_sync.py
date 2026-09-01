#!/usr/bin/env python3


import os
import datetime
import sqlite3
import database

# Try importing Google API client libraries
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    HAS_GOOGLE_CALENDAR_SDK = True
except ImportError:
    HAS_GOOGLE_CALENDAR_SDK = False

# Scopes required to read calendar events
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def authenticate_google_calendar():
    """
    Authenticates the user and returns a Google Calendar API service object.
    Uses token.json if cached, otherwise opens a browser flow for credentials.json.
    """
    if not HAS_GOOGLE_CALENDAR_SDK:
        print("[!] Error: Google Calendar SDK is not installed.")
        print("    Please run: pip install google-auth-oauthlib google-api-python-client")
        return None
        
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
                
        if not creds:
            if not os.path.exists("credentials.json"):
                print("[!] Error: 'credentials.json' not found in current directory.")
                print("    Please download your OAuth client ID credentials from Google Cloud Console.")
                return None
                
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
            
    try:
        service = build("calendar", "v3", credentials=creds)
        return service
    except Exception as e:
        print(f"[!] Error building Google Calendar service: {e}")
        return None

def sync_events(max_results=10):
    """
    Fetches upcoming events from the user's primary Google Calendar 
    and inserts them into the local SQLite database.
    """
    service = authenticate_google_calendar()
    if not service:
        print("[!] Sync skipped due to missing authentication configuration.")
        return
        
    try:
        # Get local ISO format string for current time
        now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
        print("Fetching upcoming events from Google Calendar...")
        
        events_result = service.events().list(
            calendarId="primary",
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        
        events = events_result.get("items", [])
        
        if not events:
            print("No upcoming events found on Google Calendar.")
            return
            
        print(f"Found {len(events)} events. Importing into SQLite...")
        
        # Ensure db exists
        database.init_db()
        
        imported_count = 0
        for event in events:
            title = event.get("summary", "No Title")
            description = event.get("description", "Imported from Google Calendar")
            
            # Google Calendar starts/ends can be date-only (all day) or datetime
            start = event["start"].get("dateTime", event["start"].get("date"))
            
            # Parse start time
            # Format expected by SQLite: YYYY-MM-DD and HH:MM AM/PM
            if "T" in start:
                # E.g. '2026-08-27T10:00:00+02:00' or '2026-08-27T10:00:00Z'
                # Clean timezone offset for simpler parsing
                clean_time = start.split("+")[0].split("-")
                # If there are negative values in timezone e.g. -05:00
                if len(clean_time) > 3: 
                    date_part = "-".join(clean_time[:3])
                    time_part = clean_time[3].split("Z")[0]
                else:
                    date_part = start.split("T")[0]
                    time_part = start.split("T")[1].split("Z")[0]
                
                # Parse to check validity
                try:
                    dt = datetime.datetime.strptime(f"{date_part} {time_part[:5]}", "%Y-%m-%d %H:%M")
                    date_str = dt.strftime("%Y-%m-%d")
                    time_str = dt.strftime("%I:%M %p") # e.g. '10:00 AM'
                except Exception:
                    # Fallback to defaults
                    date_str = start.split("T")[0]
                    time_str = "12:00 PM"
            else:
                # All day event (just date, e.g. '2026-08-27')
                date_str = start
                time_str = "09:00 AM" # default start time for all-day events
                
            # Check if this event already exists to prevent duplicate syncs
            # (Simple title and date matching)
            conn = database.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM events WHERE title = ? AND event_date = ?", (title, date_str))
            exists = cursor.fetchone()
            conn.close()
            
            if not exists:
                database.add_event(title, date_str, time_str, description)
                print(f" -> Scheduled: '{title}' on {date_str} at {time_str}")
                imported_count += 1
            else:
                print(f" -> Skipped (already exists): '{title}' on {date_str}")
                
        print(f"Sync complete! {imported_count} new events imported.")
        
    except HttpError as error:
        print(f"[!] An API error occurred: {error}")

if __name__ == "__main__":
    print("=== STEP 8: GOOGLE CALENDAR SYNC MOCK/RUN ===")
    
    if not HAS_GOOGLE_CALENDAR_SDK:
        print("\n[Google Calendar SDK not installed]")
        print("To test this script, install dependencies:")
        print("  pip install google-auth-oauthlib google-api-python-client")
    else:
        print("\nGoogle Calendar SDK is installed!")
        print("Ensure 'credentials.json' is present in this directory, then call:")
        print("  python -c 'import calendar_sync; calendar_sync.sync_events()'")
