#!/usr/bin/env python3
"""
Step 2 & 3: Create and Connect a Simple Database
This module manages the SQLite database using Python's built-in sqlite3 library.
It defines the database schema, seeds sample data, and provides functions 
to insert and query events.
"""

import sqlite3
import os
from datetime import datetime, timedelta

DB_FILE = "events.db"

def get_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    # Return rows as dictionaries instead of tuples for cleaner API usage
    conn.row_factory = sqlite3.Row
    return conn

def init_db(force_recreate=False):
    """
    Initializes the database by creating the events table if it doesn't exist.
    If force_recreate is True, it drops the existing table and starts fresh.
    """
    if force_recreate and os.path.exists(DB_FILE):
        try:
            os.remove(DB_FILE)
        except PermissionError:
            pass # DB might be locked/open, we'll try DROP TABLE in SQL
            
    conn = get_connection()
    cursor = conn.cursor()
    
    if force_recreate:
        cursor.execute("DROP TABLE IF EXISTS events")
        
    # Step 2: Design the events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    Demonstrates: Step 3 (INSERT query with parameterized values).
    """
    # Simple validation of date format YYYY-MM-DD
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Must be YYYY-MM-DD.")
        
    conn = get_connection()
    cursor = conn.cursor()
    
    # Use parameterized query (?) to protect against SQL Injection
    cursor.execute(
        "INSERT INTO events (title, event_date, event_time, description) VALUES (?, ?, ?, ?)",
        (title, date_str, time_str, description)
    )
    conn.commit()
    event_id = cursor.lastrowid
    conn.close()
    return event_id

def get_events_by_date(date_str):
    """
    Fetches all events scheduled for a specific date (YYYY-MM-DD).
    Demonstrates: Step 3 (SELECT query with WHERE clause and parameters).
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM events WHERE event_date = ? ORDER BY event_time ASC",
        (date_str,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    # Convert sqlite3.Row objects to standard python dicts
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
    cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    changes = conn.total_changes
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
    print("=== STEP 2 & 3: SQLITE DATABASE TUTORIAL ===")
    
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
        
    print("\n=== Database Tutorial Finished Successfully ===")
