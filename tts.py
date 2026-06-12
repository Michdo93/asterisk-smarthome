#!/usr/bin/env python3
import subprocess
import sys
import os

text = "Hallo! Dies ist ein Test meines Smart Home Sprachassistenten. Ich kann Texte vorlesen."

raw_wav   = "/opt/smarthome/tts-raw.wav"
final_wav = "/opt/smarthome/tts-output.wav"

# Piper: Text → WAV (22050 Hz)
subprocess.run([
    "/opt/smarthome/piper/piper",
    "--model", "/opt/smarthome/de_DE-thorsten-medium.onnx",
    "--output_file", raw_wav
], input=text.encode(), check=True)

# ffmpeg: 22050 Hz → 8000 Hz mono (Asterisk-Format)
subprocess.run([
    "ffmpeg", "-y",
    "-i", raw_wav,
    "-ar", "8000",
    "-ac", "1",
    "-f", "wav",
    final_wav
], check=True, capture_output=True)

sys.exit(0)
