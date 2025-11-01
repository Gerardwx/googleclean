# src/googleclean/gmail_api.py
import os
import webbrowser
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://mail.google.com/"]

def get_service(account: str | None = None):
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            flow.redirect_uri = "http://localhost:8080/"
            auth_url, _ = flow.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
                login_hint=account or None,
                prompt="consent",
            )
            print(f"Opening browser for account {account or '(default)'}...")
            webbrowser.get("open -a 'Google Chrome' %s").open(auth_url)
            creds = flow.run_local_server(port=8080)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)

