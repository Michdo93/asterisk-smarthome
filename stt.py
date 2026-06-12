#!/usr/bin/env python3
import subprocess
import sys
import os
import whisper

wav_file    = "/var/spool/asterisk/stt-latest.wav"
tts_output  = "/opt/smarthome/stt-antwort"
raw_wav     = "/opt/smarthome/stt-raw.wav"

# Alte Antwort löschen damit nie eine veraltete Datei abgespielt wird
for f in [tts_output + ".wav", raw_wav]:
    if os.path.exists(f):
        os.remove(f)

# Whisper transkribieren
model = whisper.load_model("small")
result = model.transcribe(wav_file, language="de")
text = result["text"].strip()

# Piper: Text → WAV
antwort = f"Ich habe verstanden: {text}"
subprocess.run([
    "/opt/smarthome/piper/piper",
    "--model", "/opt/smarthome/de_DE-thorsten-medium.onnx",
    "--output_file", raw_wav
], input=antwort.encode(), check=True)

# ffmpeg: auf 8kHz für Asterisk konvertieren
subprocess.run([
    "ffmpeg", "-y",
    "-i", raw_wav,
    "-ar", "8000", "-ac", "1",
    "-f", "wav",
    tts_output + ".wav"
], check=True, capture_output=True)

sys.exit(0)
