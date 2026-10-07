# Evin's Calendar

A small local calendar for classes, appointments, and the rest of the week. It uses a hosted PostgreSQL database (such as Neon) for storage, and I can ask for events in English or Swedish. Gemini is optional; basic commands work without it.

## Run it

Use Python 3, install the project dependencies, and start the web app:

```sh
pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Database

The app reads the PostgreSQL connection string from the `DATABASE_URL` environment variable. Locally, create a `.env` file in the project folder (it is git-ignored):

```
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
```

When hosting, set `DATABASE_URL` as an environment variable on the host instead. To copy events from an old local `events.db`, run `python migrate_sqlite_to_postgres.py` once.

For Gemini responses, add an API key in the app's sidebar. Without a key, try commands like `today`, `tomorrow`, `list`, or `add Study | 2026-10-05 | 03:00 PM | Exam prep`.

## Other scripts

- `cli_assistant.py` starts the terminal version.
- `import_schedule.py` reads a `TimeEdit.pdf` from the project folder and adds the events it finds that are not already in the database. Use `--replace` to delete all existing events first (it asks you to type `YES`).
- `calendar_sync.py` imports upcoming Google Calendar events. It needs the Google Calendar API packages and an OAuth `credentials.json` file.
- `desktop_app.py` opens the app in a desktop window; install `pywebview` first with `pip install pywebview`.
- The microphone and read-aloud controls depend on browser support for Web Speech.