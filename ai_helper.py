#!/usr/bin/env python3
"""
Step 6: Natural Language AI Helper
This module interfaces with the Google Gemini API to parse natural language queries
and map them into structured actions (query, add, delete) with dates, times, and titles.
If the API key is missing or the package is not installed, it falls back to keyword parsing.
"""

import os
import json
import re
from datetime import datetime, timedelta

# Try importing google-generativeai
try:
    import google.generativeai as genai
    HAS_GEMINI_SDK = True
except ImportError:
    HAS_GEMINI_SDK = False

# Fallback basic keyword parser in case Gemini is not available
def fallback_parser(user_query):
    """
    Regex/Rule-based parser that mimics AI intent extraction for basic keywords.
    """
    user_query = user_query.strip()
    lower_query = user_query.lower()
    today = datetime.today()
    
    # 1. Check for Add intent
    # Look for "add [title] on [date] at [time]" or similar
    # E.g. "add Dinner | 2026-08-27 | 07:30 PM | desc"
    if lower_query.startswith("add ") and "|" in user_query:
        parts = user_query[4:].split("|")
        title = parts[0].strip()
        date_str = parts[1].strip()
        time_str = parts[2].strip()
        desc = parts[3].strip() if len(parts) > 3 else ""
        return {
            "action": "add",
            "query_date": None,
            "event_details": {
                "title": title,
                "date": date_str,
                "time": time_str,
                "description": desc
            },
            "event_id": None,
            "explanation": f"Adding event '{title}' via keyword matching."
        }
    
    # 2. Check for Delete intent
    # Look for "delete 5" or "delete event 5"
    delete_match = re.search(r"delete\s+(?:event\s+)?(\d+)", lower_query)
    if delete_match:
        event_id = int(delete_match.group(1))
        return {
            "action": "delete",
            "query_date": None,
            "event_details": None,
            "event_id": event_id,
            "explanation": f"Deleting event with ID {event_id} via keyword matching."
        }
        
    # 3. Check for Query dates
    # Resolve relative dates
    target_date = None
    label = "today"
    
    if "tomorrow" in lower_query:
        target_date = today + timedelta(days=1)
        label = "tomorrow"
    elif "today" in lower_query:
        target_date = today
        label = "today"
    else:
        # Check weekdays
        weekdays = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, 
            "friday": 4, "saturday": 5, "sunday": 6
        }
        for day, code in weekdays.items():
            if day in lower_query:
                current_weekday = today.weekday()
                days_ahead = code - current_weekday
                if days_ahead < 0:
                    days_ahead += 7
                target_date = today + timedelta(days=days_ahead)
                label = day.capitalize()
                break
                
        # Check explicit YYYY-MM-DD
        if not target_date:
            date_match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", user_query)
            if date_match:
                date_str = date_match.group(0)
                return {
                    "action": "query",
                    "query_date": date_str,
                    "event_details": None,
                    "event_id": None,
                    "explanation": f"Querying events for date {date_str}."
                }

    if target_date:
        return {
            "action": "query",
            "query_date": target_date.strftime("%Y-%m-%d"),
            "event_details": None,
            "event_id": None,
            "explanation": f"Querying events for {label}."
        }
        
    # Default to query all or list
    if "list" in lower_query or "all" in lower_query or "show" in lower_query:
        return {
            "action": "list_all",
            "query_date": None,
            "event_details": None,
            "event_id": None,
            "explanation": "Listing all events."
        }
        
    return {
        "action": "unknown",
        "query_date": None,
        "event_details": None,
        "event_id": None,
        "explanation": "I didn't quite catch that. Try using keywords like 'today', 'tomorrow', 'monday', 'list', or format like: 'add Gym | 2026-08-28 | 05:00 PM'"
    }

def analyze_query(user_query, api_key=None):
    """
    Sends the user query to Gemini to parse intent.
    Falls back to `fallback_parser` if API key is missing, package not installed, or call fails.
    """
    # Look for API key: parameter first, then environment variable
    key = api_key or os.environ.get("GEMINI_API_KEY")
    
    if not HAS_GEMINI_SDK or not key:
        # Graceful fallback
        return fallback_parser(user_query)
        
    try:
        # Configure Gemini
        genai.configure(api_key=key)
        
        # We can use gemini-1.5-flash or gemini-2.5-flash
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Provide current context: date and weekday
        today = datetime.today()
        today_str = today.strftime("%Y-%m-%d")
        weekday_str = today.strftime("%A")
        
        system_prompt = f"""
You are the natural language parsing core of a Personal Calendar Assistant.
Today's date is {today_str} ({weekday_str}).

Your task is to analyze the user's sentence and return a JSON object ONLY. Do not include any markdown styling, code blocks, or extra text. Just raw valid JSON.

JSON Structure:
{{
  "action": "query" | "add" | "delete" | "list_all" | "unknown",
  "query_date": "YYYY-MM-DD" or null,
  "event_details": {{
    "title": "string or null",
    "date": "YYYY-MM-DD or null",
    "time": "HH:MM AM/PM or null (extract time or default to a sensible time if mentioned, e.g., 'morning' -> '09:00 AM', 'afternoon' -> '02:00 PM', 'evening' -> '07:00 PM')",
    "description": "string or null"
  }} or null,
  "event_id": integer or null,
  "explanation": "Brief, friendly conversational text explaining what you understood or what is missing."
}}

Guidelines for resolving dates:
- "today" -> {today_str}
- "tomorrow" -> {(today + timedelta(days=1)).strftime("%Y-%m-%d")}
- "day after tomorrow" -> {(today + timedelta(days=2)).strftime("%Y-%m-%d")}
- Next [Weekday] (e.g. "next Friday"): Calculate relative to today.
- If the user is listing/viewing events, set action to "query" and set query_date.
- If the user wants to see everything or has a general request to list calendar, set action to "list_all".
- If the user wants to add an event (e.g. "schedule a meeting tomorrow at 3 PM called Project Sync"), set action to "add", extract the details, and make sure date is resolved.
- If the user wants to delete (e.g. "delete event 4" or "remove appointment 1"), set action to "delete" and extract the numeric event_id.

User Query: "{user_query}"
JSON Output:
"""
        
        response = model.generate_content(
            system_prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        # Parse the JSON response
        parsed_response = json.loads(response.text.strip())
        return parsed_response
        
    except Exception as e:
        print(f"Gemini API call failed: {str(e)}. Using fallback parser.")
        # Fallback to local parsing
        result = fallback_parser(user_query)
        result["explanation"] = f"[AI Offline Fallback] {result['explanation']}"
        return result

if __name__ == "__main__":
    print("=== STEP 6: NATURAL LANGUAGE AI HELPER TEST ===")
    
    # Test cases
    test_queries = [
        "What do I have tomorrow?",
        "Do I have anything on next Monday?",
        "add dentist appointment | 2026-08-30 | 10:00 AM | Teeth cleaning",
        "delete 3",
        "Hello assistant, list everything"
    ]
    
    for q in test_queries:
        print(f"\nQuery: '{q}'")
        parsed = analyze_query(q)
        print("Parsed Output:")
        print(json.dumps(parsed, indent=2))
