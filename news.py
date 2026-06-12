#!/usr/bin/env python3
import feedparser
import subprocess
import sys
import re
from datetime import datetime

# ── Konfiguration ─────────────────────────────────────────
FEED_URL    = "https://www.tagesschau.de/xml/rss2/"
MAX_ITEMS   = 5   # Wie viele Nachrichten vorgelesen werden

def clean(text):
    """HTML-Tags und überflüssige Leerzeichen entfernen."""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def get_news():
    feed  = feedparser.parse(FEED_URL)
    items = []
    for entry in feed.entries[:MAX_ITEMS]:
        title   = clean(entry.get("title", ""))
        summary = clean(entry.get("summary", ""))
        if title:
            items.append((title, summary))
    return items

def build_text(items):
    now  = datetime.now()
    date = now.strftime("%-d. %-m. %Y")
    time = now.strftime("%H:%M")

    lines = [
        f"Guten Tag! Hier sind die aktuellen Nachrichten der Tagesschau "
        f"vom {date}, {time} Uhr.",
        ""
    ]

    for i, (title, summary) in enumerate(items, 1):
        lines.append(f"Meldung {i}: {title}.")
        if summary and summary != title:
            lines.append(summary)
        lines.append("")

    lines.append("Das waren die aktuellen Nachrichten. Auf Wiederhören.")
    return " ".join(lines)

def speak(text):
    raw_wav = "/opt/smarthome/news-raw.wav"
    final   = "/opt/smarthome/news-output"

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
        items = get_news()
        if not items:
            speak("Entschuldigung, die Nachrichten konnten nicht abgerufen werden.")
        else:
            text = build_text(items)
            speak(text)
    except Exception as e:
        speak("Entschuldigung, beim Abrufen der Nachrichten ist ein Fehler aufgetreten.")
    sys.exit(0)
