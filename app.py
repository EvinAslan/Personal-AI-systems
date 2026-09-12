#!/usr/bin/env python3
"""
Step 5 & 6: Flask Backend Web Application
This script serves the web assistant dashboard, processes chat queries via NLP (Gemini/fallback),
and exposes api endpoints for front-end visual components.
"""

import os
from flask import Flask, render_template, request, jsonify
import database
import ai_helper
from datetime import datetime

# Initialize Flask app
# We configure it to look for templates and static folders locally
app = Flask(__name__, 
            template_folder="templates", 
            static_folder="static")

# Ensure database is initialized and seeded with some basic data
database.init_db()

@app.route("/service-worker.js")
def service_worker():
    return app.send_static_file("service-worker.js")

@app.route("/")
def index():
    """Serves the main assistant dashboard interface."""
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Main chat endpoint. Receives user message, extracts intent via NLP,
    interacts with the database, and returns a response.
    """
    data = request.json or {}
    user_message = data.get("message", "").strip()
    api_key = data.get("api_key", "").strip() or None
    
    if not user_message:
        return jsonify({"error": "Empty message"}), 400
        
    # Step 6: Process the user message through Gemini / Local Fallback
    analysis = ai_helper.analyze_query(user_message, api_key=api_key)
    action = analysis.get("action", "unknown")
    explanation = analysis.get("explanation", "")
    
    response_text = explanation
    db_events = []
    current_date_focus = None
    
    try:
        # Execute query against SQLite database based on intent
        if action == "query":
            date_str = analysis.get("query_date")
            if date_str:
                db_events = database.get_events_by_date(date_str)
                current_date_focus = date_str
                # Build response detailing events
                if db_events:
                    event_list = []
                    for ev in db_events:
                        desc = f" ({ev['description']})" if ev['description'] else ""
                        event_list.append(f"• {ev['event_time']}: {ev['title']}{desc}")
                    events_formatted = "\n".join(event_list)
                    prefix = explanation if explanation else f"Här är ditt schema för {date_str}:"
                    response_text = f"{prefix}\n\n{events_formatted}"
                else:
                    response_text = f"Du har inga inplanerade lektioner för {date_str}."
            else:
                response_text = "Jag förstod att du ville se schema, men kunde inte identifiera datumet."
                
        elif action == "list_all":
            db_events = database.get_all_events()
            if db_events:
                event_list = []
                for ev in db_events:
                    desc = f" ({ev['description']})" if ev['description'] else ""
                    event_list.append(f"• {ev['event_date']} kl. {ev['event_time']}: {ev['title']}{desc}")
                events_formatted = "\n".join(event_list)
                prefix = explanation if explanation else "Här är dina inplanerade tider:"
                response_text = f"{prefix}\n\n{events_formatted}"
            else:
                response_text = "Ditt schema är tomt."
                
        elif action == "add":
            details = analysis.get("event_details") or {}
            title = details.get("title")
            date_str = details.get("date")
            time_str = details.get("time") or "12:00 PM"
            description = details.get("description") or ""
            
            if not title or not date_str:
                response_text = "I understood you wanted to add an event, but I'm missing the event title or date. Please specify both."
            else:
                event_id = database.add_event(title, date_str, time_str, description)
                response_text = f"Success! I've scheduled '{title}' on {date_str} at {time_str}."
                # Return updated list for that day so the UI updates
                db_events = database.get_events_by_date(date_str)
                current_date_focus = date_str
                
        elif action == "delete":
            event_id = analysis.get("event_id")
            if event_id is not None:
                success = database.delete_event(int(event_id))
                if success:
                    response_text = f"I've successfully deleted the event with ID {event_id}."
                else:
                    response_text = f"I couldn't find an event with ID {event_id} to delete."
            else:
                response_text = "I understood you wanted to delete an event, but I couldn't extract the event ID."
                
        elif action == "unknown":
            # If the parser couldn't figure it out, just echo Gemini's explanation
            pass
            
    except Exception as e:
        response_text = f"Sorry, I encountered an error while processing your request: {str(e)}"
        
    return jsonify({
        "response": response_text,
        "action": action,
        "events": db_events,
        "date_focus": current_date_focus,
        "raw_analysis": analysis
    })

@app.route("/api/events", methods=["GET"])
def get_events():
    """REST endpoint to fetch all events."""
    try:
        events = database.get_all_events()
        return jsonify({"events": events})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/events", methods=["POST"])
def add_event_direct():
    """REST endpoint to add an event directly."""
    data = request.json or {}
    title = data.get("title")
    date_str = data.get("event_date")
    time_str = data.get("event_time", "12:00 PM")
    description = data.get("description", "")
    
    if not title or not date_str:
        return jsonify({"error": "Missing title or event_date"}), 400
        
    try:
        event_id = database.add_event(title, date_str, time_str, description)
        return jsonify({"success": True, "event_id": event_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/events/<int:event_id>", methods=["DELETE"])
def delete_event_direct(event_id):
    """REST endpoint to delete an event directly by ID."""
    try:
        success = database.delete_event(event_id)
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Start web server local port 5000
    print("Starting Flask application. Open http://localhost:5000 in your browser.")
    app.run(debug=True, host="0.0.0.0", port=5000)
