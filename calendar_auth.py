#!/usr/bin/env python3
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os

SCOPES      = ["https://www.googleapis.com/auth/calendar.readonly"]
CREDS_FILE  = "/opt/smarthome/credentials.json"
TOKEN_FILE  = "/opt/smarthome/token.json"

def authenticate():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds

if __name__ == "__main__":
    creds = authenticate()
    print("Authentifizierung erfolgreich. Token gespeichert.")
