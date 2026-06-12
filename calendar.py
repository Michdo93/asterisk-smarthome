#!/usr/bin/env python3
import subprocess
import sys
import os
from datetime import datetime, timezone, timedelta
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES     = ["https://www.googleapis.com/auth/calendar.readonly"]
TOKEN_FILE = "/opt/smarthome/token.json"
CREDS_FILE = "/opt/smarthome/credentials.json"

WEEKDAYS = {
    0: "Montag", 1: "Dienstag", 2: "Mittwoch",
    3: "Donnerstag", 4: "Freitag", 5: "Samstag", 6: "Sonntag"
}

MONTHS = {
    1: "Januar", 2: "Februar", 3: "März", 4: "April",
    5: "Mai", 6: "Juni", 7: "Juli", 8: "August",
    9: "September", 10: "Oktober", 11: "November", 12: "Dezember"
}

def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
    return creds

def get_events():
    creds   = get_credentials()
    service = build("calendar", "v3", credentials=creds)

    tz      = timezone(timedelta(hours=2))  # CEST — im Winter auf +1 ändern
    now     = datetime.now(tz)
    start   = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end     = now.replace(hour=23, minute=59, second=59, microsecond=0)

    result = service.events().list(
        calendarId="primary",
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        orderBy="startTime",
        maxResults=10
    ).execute()

    return result.get("items", []), now

def format_time(event):
    start = event["start"]
    if "dateTime" in start:
        dt = datetime.fromisoformat(start["dateTime"])
        return f"{dt.hour} Uhr {dt.minute:02d}" if dt.minute else f"{dt.hour} Uhr"
    return None  # Ganztägig

def build_text(events, now):
    weekday = WEEKDAYS[now.weekday()]
    day     = now.day
    month   = MONTHS[now.month]
    year    = now.year

    intro = (
        f"Guten Tag! Hier sind deine Termine für heute, "
        f"{weekday}, den {day}. {month} {year}. "
    )

    if not events:
        return intro + "Du hast heute keine Termine eingetragen. Einen entspannten Tag!"

    lines = [intro, f"Du hast {len(events)} Termin{'e' if len(events) != 1 else ''}. "]

    for i, event in enumerate(events, 1):
        title    = event.get("summary", "Ohne Titel")
        time_str = format_time(event)
        location = event.get("location", "")

        if time_str:
            line = f"Termin {i}: {title}, um {time_str}."
        else:
            line = f"Termin {i}: {title}, ganztägig."

        if location:
            line += f" Ort: {location}."

        lines.append(line)

    lines.append("Das waren alle deine heutigen Termine. Einen schönen Tag!")
    return " ".join(lines)

def speak(text):
    raw_wav = "/opt/smarthome/calendar-raw.wav"
    final   = "/opt/smarthome/calendar-output"

    for f in [raw_wav, final + ".wav"]:
        if os.path.exists(f):
            os.remove(f)

    subprocess.run([
        "/opt/smarthome/piper/piper",
        "--model", "/opt/smarthome/de_DE-thorsten-medium.onnx",
        "--output_file", raw_wav
    ], input=text.encode(), check=True, capture_output=True)

    subprocess.run([
        "ffmpeg", "-y",
        "-i", raw_wav,
        "-ar", "8000", "-ac", "1",
        "-f", "wav",
        final + ".wav"
    ], check=True, capture_output=True)

if __name__ == "__main__":
    try:
        events, now = get_events()
        text        = build_text(events, now)
        speak(text)
    except Exception as e:
        speak("Entschuldigung, der Kalender konnte nicht abgerufen werden.")
    sys.exit(0)
