#!/usr/bin/env python3
"""Store and retrieve calendar events in the PostgreSQL database."""

import os
from datetime import datetime, timedelta

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

from date_utils import parse_event_date

load_dotenv()

def get_connection():
    """Returns a connection to the PostgreSQL database given by DATABASE_URL."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set.")
    # Return rows as dictionaries instead of tuples for cleaner API usage
    return psycopg.connect(database_url, row_factory=dict_row)

def init_db(force_recreate=False):
    """
    Initializes the database by creating the events table if it doesn't exist.
    If force_recreate is True, it drops the existing table and starts fresh.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    if force_recreate:
        cursor.execute("DROP TABLE IF EXISTS events")
        
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            event_date TEXT NOT NULL,  -- Format: YYYY-MM-DD
            event_time TEXT NOT NULL,  -- Format: HH:MM AM/PM
            description TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def add_event(title, date_str, time_str, description=None):
    """
    Inserts a new event into the database.
    The date must use the YYYY-MM-DD format.
    """
    date_str = parse_event_date(date_str)
        
    conn = get_connection()
    cursor = conn.cursor()
    
    # Use parameterized query (%s) to protect against SQL Injection
    cursor.execute(
        "INSERT INTO events (title, event_date, event_time, description) VALUES (%s, %s, %s, %s) RETURNING id",
        (title, date_str, time_str, description)
    )
    event_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return event_id

def get_events_by_date(date_str):
    """
    Fetches all events scheduled for a specific date (YYYY-MM-DD).
    The date must use the YYYY-MM-DD format.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM events WHERE event_date = %s ORDER BY event_time ASC",
        (date_str,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_all_events():
    """Fetches all events in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events ORDER BY event_date ASC, event_time ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_event(event_id):
    """Deletes an event by its ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE id = %s", (event_id,))
    changes = cursor.rowcount
    conn.commit()
    conn.close()
    return changes > 0

def seed_sample_data():
    """Seeds the database with some realistic sample events for today and tomorrow."""
    today_str = datetime.today().strftime('%Y-%m-%d')
    tomorrow_str = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Clear any old data first by re-initializing
    init_db(force_recreate=True)
    
    # Seed events
    add_event("Morning Jog", today_str, "07:30 AM", "Run around the park")
    add_event("Team Sync Meeting", today_str, "10:00 AM", "Weekly project alignment")
    add_event("Math Exam Preparation", tomorrow_str, "02:00 PM", "Study chapters 4 to 6")
    add_event("Dinner with Sarah", tomorrow_str, "07:30 PM", "Italian restaurant downtown")
    add_event("Dentist Appointment", (datetime.today() + timedelta(days=3)).strftime('%Y-%m-%d'), "11:00 AM", "Routine checkup")
    
    print("Database seeded with sample events.")

if __name__ == "__main__":
    print("=== CALENDAR DATABASE ===")
    
    # Initialize and seed data
    seed_sample_data()
    
    # Query all events
    print("\nAll Scheduled Events in Database:")
    all_events = get_all_events()
    for ev in all_events:
        print(f"ID: {ev['id']} | Date: {ev['event_date']} | Time: {ev['event_time']} | Title: {ev['title']} ({ev['description']})")
        
    # Query events for tomorrow
    tomorrow_str = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')
    print(f"\nQuerying events specifically for Tomorrow ({tomorrow_str}):")
    tomorrow_events = get_events_by_date(tomorrow_str)
    for ev in tomorrow_events:
        print(f"  - [{ev['event_time']}] {ev['title']} ({ev['description']})")
        
    print("\n=== Database check finished ===")
