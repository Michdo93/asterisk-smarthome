#!/usr/bin/env python3
import requests
import subprocess
import sys
import os

# ── Koordinaten anpassen ──────────────────────────────────
LAT = 48.31
LON = 8.12
CITY = "Furtwangen im Schwarzwald"

# ── Wetter-Codes auf Deutsch ──────────────────────────────
WEATHER_CODES = {
    0:  "klarer Himmel",
    1:  "überwiegend klar",
    2:  "teilweise bewölkt",
    3:  "bedeckt",
    45: "neblig",
    48: "gefrierender Nebel",
    51: "leichter Nieselregen",
    53: "mäßiger Nieselregen",
    55: "starker Nieselregen",
    61: "leichter Regen",
    63: "mäßiger Regen",
    65: "starker Regen",
    71: "leichter Schneefall",
    73: "mäßiger Schneefall",
    75: "starker Schneefall",
    80: "leichte Regenschauer",
    81: "mäßige Regenschauer",
    82: "starke Regenschauer",
    85: "leichte Schneeschauer",
    86: "starke Schneeschauer",
    95: "Gewitter",
    96: "Gewitter mit Hagel",
    99: "starkes Gewitter mit Hagel",
}

def get_weather():
    r = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude":  LAT,
            "longitude": LON,
            "current":   "temperature_2m,weathercode,windspeed_10m,relativehumidity_2m",
            "daily":     "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
            "timezone":  "Europe/Berlin",
            "forecast_days": 1
        },
        timeout=10
    )
    r.raise_for_status()
    return r.json()

def build_text(data):
    cur  = data["current"]
    day  = data["daily"]

    temp      = round(cur["temperature_2m"])
    code      = cur["weathercode"]
    wind      = round(cur["windspeed_10m"])
    humidity  = round(cur["relativehumidity_2m"])
    condition = WEATHER_CODES.get(code, "unbekannte Wetterlage")

    temp_max  = round(day["temperature_2m_max"][0])
    temp_min  = round(day["temperature_2m_min"][0])
    rain      = round(day["precipitation_sum"][0], 1)

    text = (
        f"Guten Tag! Hier sind die aktuellen Wetterinformationen für {CITY}. "
        f"Aktuell: {condition}, {temp} Grad, "
        f"Windgeschwindigkeit {wind} Kilometer pro Stunde, "
        f"Luftfeuchtigkeit {humidity} Prozent. "
        f"Tagesvorschau: Höchsttemperatur {temp_max} Grad, "
        f"Tiefsttemperatur {temp_min} Grad, "
        f"Niederschlag {rain} Millimeter. "
        f"Einen schönen Tag!"
    )
    return text

def speak(text):
    raw_wav  = "/opt/smarthome/weather-raw.wav"
    final    = "/opt/smarthome/weather-output"

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
        data = get_weather()
        text = build_text(data)
        speak(text)
    except Exception as e:
        speak(f"Entschuldigung, die Wetterdaten konnten nicht abgerufen werden.")
    sys.exit(0)
