#!/usr/bin/env python3
"""
Step 4: Terminal-Based Assistant
This command-line script interacts with the SQLite database.
It parses rigid keywords (like 'today', 'tomorrow', weekdays, and date formats)
to display and manage calendar events.
"""

import sys
from datetime import datetime, timedelta
import database

# Ensure database is initialized
database.init_db()

def print_help():
    print("""
Available Commands:
  help                           - Show this help menu
  list                           - List all events in the database
  today                          - Show events scheduled for today
  tomorrow                       - Show events scheduled for tomorrow
  weekday <name> (e.g., monday)   - Show events for the next occurrence of that weekday
  add <title> | <date> | <time> [| <description>]
                                 - Add a new event. Date must be YYYY-MM-DD.
                                   Example: add Gym | 2026-08-28 | 05:00 PM | Chest day
  delete <id>                    - Delete an event by ID
  exit / quit                    - Exit the assistant
""")

def get_next_weekday(weekday_name):
    """
    Calculates the date of the next occurrence of a given weekday name (e.g., 'monday').
    If today is that weekday, returns today's date.
    """
    weekdays = {
        "monday": 0, "tues": 1, "tuesday": 1, "wed": 2, "wednesday": 2,
        "thurs": 3, "thursday": 3, "fri": 4, "friday": 4, "sat": 5, "saturday": 5,
        "sun": 6, "sunday": 6
    }
    
    query = weekday_name.strip().lower()
    if query not in weekdays:
        return None
        
    target_weekday = weekdays[query]
    today = datetime.today()
    current_weekday = today.weekday()
    
    # Calculate days until the next occurrence
    days_ahead = target_weekday - current_weekday
    if days_ahead < 0:
        days_ahead += 7  # It occurred earlier this week, so target next week
        
    target_date = today + timedelta(days=days_ahead)
    return target_date.strftime("%Y-%m-%d")

def format_events(events, date_label):
    if not events:
        return f"No events found for {date_label}."
    
    output = [f"=== Events for {date_label} ==="]
    for ev in events:
        desc_str = f" - {ev['description']}" if ev['description'] else ""
        output.append(f"[{ev['id']}] {ev['event_time']}: {ev['title']}{desc_str}")
    return "\n".join(output)

def parse_and_execute(user_input):
    user_input = user_input.strip()
    if not user_input:
        return ""
        
    lower_input = user_input.lower()
    
    # Exit command
    if lower_input in ["exit", "quit"]:
        print("Goodbye!")
        sys.exit(0)
        
    # Help command
    elif lower_input == "help":
        print_help()
        return ""
        
    # List command
    elif lower_input == "list":
        events = database.get_all_events()
        if not events:
            return "No events scheduled."
        output = ["=== All Scheduled Events ==="]
        for ev in events:
            desc_str = f" ({ev['description']})" if ev['description'] else ""
            output.append(f"[{ev['id']}] {ev['event_date']} at {ev['event_time']} - {ev['title']}{desc_str}")
        return "\n".join(output)
        
    # Today command
    elif "today" in lower_input:
        today_str = datetime.today().strftime("%Y-%m-%d")
        events = database.get_events_by_date(today_str)
        return format_events(events, f"Today ({today_str})")
        
    # Tomorrow command
    elif "tomorrow" in lower_input:
        tomorrow_str = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        events = database.get_events_by_date(tomorrow_str)
        return format_events(events, f"Tomorrow ({tomorrow_str})")
        
    # Weekday command (direct parsing, e.g., "monday" or "on friday")
    elif any(day in lower_input for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]):
        # Find which day matches
        matched_day = None
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
            if day in lower_input:
                matched_day = day
                break
                
        target_date_str = get_next_weekday(matched_day)
        events = database.get_events_by_date(target_date_str)
        return format_events(events, f"Next {matched_day.capitalize()} ({target_date_str})")
        
    # Add event command
    elif lower_input.startswith("add "):
        parts = user_input[4:].split("|")
        if len(parts) < 3:
            return "Error: Add command requires at least: title | date (YYYY-MM-DD) | time (HH:MM AM/PM)"
        
        title = parts[0].strip()
        date_str = parts[1].strip()
        time_str = parts[2].strip()
        desc = parts[3].strip() if len(parts) > 3 else None
        
        try:
            event_id = database.add_event(title, date_str, time_str, desc)
            return f"Success: Event added with ID {event_id}."
        except ValueError as e:
            return f"Error adding event: {str(e)}"
            
    # Delete event command
    elif lower_input.startswith("delete "):
        id_str = lower_input[7:].strip()
        if not id_str.isdigit():
            return "Error: Delete requires a numeric event ID."
        
        event_id = int(id_str)
        success = database.delete_event(event_id)
        if success:
            return f"Success: Event with ID {event_id} has been deleted."
        else:
            return f"Error: Event with ID {event_id} not found."
            
    # Match specific YYYY-MM-DD dates in the query
    else:
        # Check if there is a substring matching YYYY-MM-DD
        import re
        date_match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", user_input)
        if date_match:
            date_str = date_match.group(0)
            try:
                events = database.get_events_by_date(date_str)
                return format_events(events, date_str)
            except Exception as e:
                return f"Error reading date {date_str}: {str(e)}"
        else:
            return "Command not recognized. Type 'help' to see available options."

def main():
    print("====================================================")
    print("     Welcome to your Personal Calendar Assistant   ")
    print("====================================================")
    print("Type 'help' for a list of commands, or 'exit' to quit.")
    
    while True:
        try:
            user_input = input("\nYou: ")
            result = parse_and_execute(user_input)
            if result:
                print(f"Assistant: {result}")
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    main()
