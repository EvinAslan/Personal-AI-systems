# Evin's Calendar

A small local calendar for classes, appointments, and the rest of the week. It uses SQLite for storage, and I can ask for events in English or Swedish. Gemini is optional; basic commands work without it.

## Run it

Use Python 3, install the project dependencies, and start the web app:

```sh
pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). Events are kept in `events.db` in the project folder.

For Gemini responses, add an API key in the app's sidebar. Without a key, try commands like `today`, `tomorrow`, `list`, or `add Study | 2026-10-05 | 03:00 PM | Exam prep`.

## Other scripts

- `cli_assistant.py` starts the terminal version.
- `import_schedule.py` reads a `TimeEdit.pdf` from the project folder and replaces the events in `events.db` with the events it finds. Back up the database first if you need to keep its current entries.
- `calendar_sync.py` imports upcoming Google Calendar events. It needs the Google Calendar API packages and an OAuth `credentials.json` file.
- `desktop_app.py` opens the app in a desktop window; install `pywebview` first with `pip install pywebview`.
- The microphone and read-aloud controls depend on browser support for Web Speech.