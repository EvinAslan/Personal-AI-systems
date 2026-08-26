#!/usr/bin/env python3
"""
Step 1: Learn Basic Python
This script serves as a simple tutorial covering Python fundamentals 
needed for building our personal calendar assistant.

Key concepts covered:
1. Variables & Data Types
2. Control Flow (if/else, loops)
3. Functions
4. Built-in datetime module
"""

from datetime import datetime, timedelta

def main():
    print("=== STEP 1: PYTHON BASICS TUTORIAL ===")

    # 1. Variables & Data Types
    print("\n1. Variables & Data Types:")
    # Storing a string (event name)
    event_title = "Math Exam"
    # Storing dates as strings
    event_date_str = "2026-08-27"
    event_time_str = "10:00 AM"
    
    print(f"Event: '{event_title}' is scheduled on {event_date_str} at {event_time_str}")
    print(f"Data types: event_title is {type(event_title)}, event_date_str is {type(event_date_str)}")

    # 2. Working with the datetime module
    print("\n2. Working with Datetime:")
    # Today's date
    today = datetime.today()
    print(f"Today's date and time object: {today}")
    print(f"Today formatted (YYYY-MM-DD): {today.strftime('%Y-%m-%d')}")

    # Calculating relative dates (e.g. tomorrow)
    tomorrow = today + timedelta(days=1)
    tomorrow_str = tomorrow.strftime('%Y-%m-%d')
    print(f"Tomorrow's date: {tomorrow_str}")

    # 3. Simple Database Mock (List of Dictionaries)
    # Storing multiple events in a list
    sample_events = [
        {
            "title": "Math Exam",
            "date": tomorrow_str,  # Scheduled for tomorrow
            "time": "10:00 AM"
        },
        {
            "title": "Gym Workout",
            "date": today.strftime('%Y-%m-%d'),  # Scheduled for today
            "time": "05:00 PM"
        },
        {
            "title": "Project Meeting",
            "date": tomorrow_str,  # Scheduled for tomorrow
            "time": "02:00 PM"
        }
    ]

    # 4. Functions & Control Flow
    print("\n3. Functions & Control Flow:")
    
    def get_events_for_day(date_query):
        """
        Filters and returns events matching a specific date string (YYYY-MM-DD).
        Demonstrates: functions, loops, and conditional (if) statements.
        """
        matching_events = []
        
        # Loop through each event in our list
        for event in sample_events:
            # Control flow: Check if the event date matches our query date
            if event["date"] == date_query:
                matching_events.append(event)
                
        return matching_events

    # Let's test the function for today and tomorrow
    today_query = today.strftime('%Y-%m-%d')
    print(f"Querying events for today ({today_query}):")
    today_events = get_events_for_day(today_query)
    for ev in today_events:
        print(f"  - [{ev['time']}] {ev['title']}")
        
    print(f"\nQuerying events for tomorrow ({tomorrow_str}):")
    tomorrow_events = get_events_for_day(tomorrow_str)
    for ev in tomorrow_events:
        print(f"  - [{ev['time']}] {ev['title']}")

    print("\n=== Tutorial Finished Successfully ===")

if __name__ == "__main__":
    main()
