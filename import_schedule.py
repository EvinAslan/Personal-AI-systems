#!/usr/bin/env python3
"""
Script to parse 'TimeEdit.pdf' and import all schedule events into our SQLite database.
Supports Swedish character decoding and normalizes split words from PDF layouts.
"""

import os
import re
import sqlite3
import pypdf
from datetime import datetime

DB_FILE = "events.db"

# List of courses we know are in this schedule
COURSES = [
    "Data Science och maskininlärning",
    "Data Storage and Management Technologies",
    "Systemförvaltning och test av IT-system",
    "Gästföreläsning"
]

# Mapping of split moment names to normal Swedish words
MOMENT_CLEANUP = {
    r"Omdugg\s*a": "Omdugga",
    r"Föreläsni\s*ng": "Föreläsning",
    r"Seminari\s*um": "Seminarium",
    r"Laboratio\s*n": "Laboration",
    r"Redovisn\s*ing": "Redovisning",
    r"Gästförel\s*äsning": "Gästföreläsning",
    r"Tentame\s*n": "Tentamen"
}

def clean_text(text):
    """Clean extra spaces and normalization issues in extracted text."""
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_time_12h(time_str):
    """Convert HH:MM 24h format to HH:MM AM/PM format."""
    try:
        t = datetime.strptime(time_str.strip(), "%H:%M")
        return t.strftime("%I:%M %p")
    except ValueError:
        return time_str

def parse_pdf_schedule(pdf_path):
    reader = pypdf.PdfReader(pdf_path)
    events = []
    
    current_date_str = None
    
    # Regex to detect date headers in the PDF, e.g. "v 35 Tors 27/8" or "Tors 10/9"
    date_pattern = re.compile(r'(?:v\s+\d+\s+)?(?:Mån|Tis|Ons|Tors|Fre|Lör|Sön)\s+(\d+)/(\d+)')
    # Regex to detect time ranges, e.g. "10:00 - 11:00"
    time_pattern = re.compile(r'^(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})')
    
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check for Date indicator
            date_match = date_pattern.search(line)
            if date_match and not time_pattern.match(line):
                day_val = int(date_match.group(1))
                month_val = int(date_match.group(2))
                # Resolve year (August-December -> 2026, January-February -> 2027)
                year = 2026 if month_val >= 8 else 2027
                current_date_str = f"{year}-{month_val:02d}-{day_val:02d}"
                i += 1
                continue
                
            # Check for Time Range indicator (starts a schedule entry)
            time_match = time_pattern.match(line)
            if time_match and current_date_str:
                start_time_24 = time_match.group(1)
                end_time_24 = time_match.group(2)
                start_time_12 = parse_time_12h(start_time_24)
                
                # Gather all lines belonging to this event block until we hit the next time range, 
                # next date, or page boundary/footer.
                block_lines = []
                first_line_rest = line[time_match.end():].strip()
                if first_line_rest:
                    block_lines.append(first_line_rest)
                    
                i += 1
                while i < len(lines):
                    next_line = lines[i].strip()
                    if time_pattern.match(next_line) or date_pattern.search(next_line):
                        break
                    if next_line.startswith("TimeEdit") or next_line.startswith("Tid Programtillfälle"):
                        i += 1
                        continue
                    if next_line:
                        block_lines.append(next_line)
                    i += 1
                
                block_text = " ".join(block_lines)
                
                # Extract Course Title
                matched_title = "School Event"
                for course in COURSES:
                    if course.lower() in block_text.lower():
                        matched_title = course
                        break
                if "gästförel" in block_text.lower() and "hållbarhet" in block_text.lower():
                    matched_title = "Gästföreläsning: IT och hållbarhet"
                elif matched_title == "School Event":
                    if "systemf" in block_text.lower() or "systemförvalt" in block_text.lower():
                        matched_title = "Systemförvaltning och test av IT-system"
                    elif "data science" in block_text.lower():
                        matched_title = "Data Science och maskininlärning"
                    elif "data storage" in block_text.lower():
                        matched_title = "Data Storage and Management Technologies"
                
                # Extract Moment type
                matched_moment = ""
                for regex_pattern, clean_val in MOMENT_CLEANUP.items():
                    if re.search(regex_pattern, block_text, re.IGNORECASE):
                        matched_moment = clean_val
                        break
                if not matched_moment:
                    if "eget arbete" in block_text.lower():
                        matched_moment = "Eget arbete"
                    elif "frågestund" in block_text.lower() or "frågestu" in block_text.lower():
                        matched_moment = "Frågestund"
                    elif "seminar" in block_text.lower():
                        matched_moment = "Seminarium"
                    else:
                        matched_moment = "Föreläsning"
                        
                # Extract Location
                matched_location = "N/A"
                location_match = re.search(r'(Internet\.?\s*Samtal\d*\s*\(zoom\)|Internet\.?\s*Zoom|Borlänge\.?\s*[A-Z]\d{3}(?:\s*Datorsal|\s*Lärosal/etage|\s*Lärosal|\s*ALC)?)', block_text, re.IGNORECASE)
                if location_match:
                    matched_location = location_match.group(1)
                else:
                    if "zoom" in block_text.lower():
                        matched_location = "Internet (Zoom)"
                    elif "borlänge" in block_text.lower():
                        room_match = re.search(r'Borlänge\.?\s*([A-Z]\d{3})', block_text, re.IGNORECASE)
                        if room_match:
                            matched_location = f"Borlänge room {room_match.group(1)}"
                        else:
                            matched_location = "Borlänge Campus"
                
                description = f"Moment: {matched_moment} | Room: {matched_location}"
                
                events.append({
                    "title": matched_title,
                    "event_date": current_date_str,
                    "event_time": start_time_12,
                    "description": description
                })
                continue
                
            i += 1
            
    return events

def import_to_db(events):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events")
    
    count = 0
    for ev in events:
        cursor.execute(
            "INSERT INTO events (title, event_date, event_time, description) VALUES (?, ?, ?, ?)",
            (ev["title"], ev["event_date"], ev["event_time"], ev["description"])
        )
        count += 1
        
    conn.commit()
    conn.close()
    return count

if __name__ == "__main__":
    print("=== TIMEEDIT PDF PARSER & IMPORTER ===")
    pdf_file = "TimeEdit.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"Error: {pdf_file} not found!")
    else:
        print(f"Reading and parsing {pdf_file}...")
        parsed_events = parse_pdf_schedule(pdf_path=pdf_file)
        print(f"Successfully parsed {len(parsed_events)} events from PDF.")
        
        imported = import_to_db(parsed_events)
        print(f"Imported {imported} schedule events into '{DB_FILE}' database.")
        
        # Verify first few
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events ORDER BY event_date ASC, event_time ASC LIMIT 5")
        rows = cursor.fetchall()
        print("\nFirst 5 imported events:")
        for r in rows:
            print(f" - [{r['event_date']} {r['event_time']}] {r['title']} ({r['description']})")
        conn.close()
