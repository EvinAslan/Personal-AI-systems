# Aether Calendar - Personal AI Calendar Assistant

A premium, interactive personal schedule and calendar assistant built step-by-step from Python/SQLite foundations to a modern web application with Gemini NLP integration and browser-native voice interactions.

---

## 📂 Project Structure

- `step1_basic_python.py`: Practical tutorial on variables, loops, lists, and python's `datetime` library.
- `database.py`: Core SQLite interface module. Initializes schema (`events` table), seeds sample data, and runs query transactions.
- `cli_assistant.py`: Terminal CLI interface with strict and relative keyword matching (e.g. today, tomorrow, weekday names).
- `ai_helper.py`: Natural language processing connector. Sends prompt to Google Gemini to retrieve structured JSON instructions; falls back to standard keyword regex if offline or missing API key.
- `app.py`: Flask-based backend server providing REST APIs for chat parsing, event updates, and template serving.
- `templates/index.html`: Fully responsive, semantic, custom-styled dashboard chat template.
- `static/style.css`: Modern premium dark-mode styling utilizing glassmorphism and neon glows.
- `static/main.js`: Asynchronous frontend controller, handling chat history flow, calendar re-rendering, Web Speech API (microphone recording + voice synthesis).
- `calendar_sync.py`: Conceptual module illustrating OAuth2 authorization and sync pipeline with Google Calendar API.

---

## 🚀 Setup and Run Guide

### Step 1: Install Dependencies
First, ensure you have Python 3 installed. Then, install the packages required for the web server and the Gemini integration:
```bash
pip install Flask google-generativeai
```

*(Optional dependencies for Google Calendar sync)*:
```bash
pip install google-auth-oauthlib google-api-python-client
```

---

### Step 2: Phase 1 & 2 CLI Executables

#### A. Run Python Tutorial
Walk through the variables, datetimes, and functions demonstration:
```bash
python step1_basic_python.py
```

#### B. Setup & Test SQLite Database
Initialize and seed the database (`events.db`) with test events:
```bash
python database.py
```

#### C. Run the Terminal-Based Assistant
Launch the command-line assistant:
```bash
python cli_assistant.py
```
*Try typing: `list`, `today`, `tomorrow`, `monday`, `delete 2`, or `add Study | 2026-08-28 | 03:00 PM | Math test prep`.*

---

### Step 3: Phase 2 & 3 Web Application

#### A. Running the Flask App
Start the web dashboard server:
```bash
python app.py
```
After launching, open your browser and navigate to:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

#### B. Utilizing Gemini AI Capabilities
To unlock true natural language query processing (e.g., *"What classes do I have tomorrow afternoon?"*):
1. Get a free API Key from [Google AI Studio](https://aistudio.google.com/).
2. You can either set it in your OS environment variables:
   - **Windows (CMD)**: `set GEMINI_API_KEY=your_api_key_here`
   - **Windows (PowerShell)**: `$env:GEMINI_API_KEY="your_api_key_here"`
   - **Mac/Linux**: `export GEMINI_API_KEY="your_api_key_here"`
3. **Or** simply paste it directly into the input box in the Web sidebar! It will be securely stored in your local browser storage.

#### C. Voice Capabilities
The application leverages the native **Web Speech API** built into modern browsers (Chrome, Edge, Safari):
- **Microphone (Speech-To-Text)**: Click the mic icon next to the chat bar, say a command (e.g., *"What do I have scheduled for today?"*), and it will automatically type and submit it.
- **Read Aloud (Text-To-Speech)**: The speaker icon toggle controls whether the assistant speaks its answers back to you. (Active by default, filtered to ignore markdown formatting).

---

### Step 4: Sync Google Calendar

1. Enable the Google Calendar API in your Google Cloud Console.
2. Download your OAuth Client ID file as `credentials.json` and place it in the project root.
3. Call the sync module:
```bash
python -c "import calendar_sync; calendar_sync.sync_events()"
```
This will open your browser to log in with Google, save `token.json` for caching, and import your calendar events directly into `events.db`.
