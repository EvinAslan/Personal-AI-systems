#!/usr/bin/env python3
"""One-time script: copy all events from the old events.db (SQLite) into PostgreSQL."""

import os
import sqlite3

import database

SQLITE_FILE = "events.db"


def migrate():
    if not os.path.exists(SQLITE_FILE):
        print(f"Error: {SQLITE_FILE} not found.")
        return

    src = sqlite3.connect(SQLITE_FILE)
    src.row_factory = sqlite3.Row
    rows = src.execute(
        "SELECT title, event_date, event_time, description FROM events ORDER BY id"
    ).fetchall()
    src.close()

    database.init_db()
    conn = database.get_connection()
    cursor = conn.cursor()
    for row in rows:
        cursor.execute(
            "INSERT INTO events (title, event_date, event_time, description) VALUES (%s, %s, %s, %s)",
            (row["title"], row["event_date"], row["event_time"], row["description"]),
        )
    conn.commit()
    conn.close()
    print(f"Migrated {len(rows)} events to PostgreSQL.")


if __name__ == "__main__":
    migrate()
