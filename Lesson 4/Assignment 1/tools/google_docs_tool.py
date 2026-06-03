import os
import pickle
from langchain.tools import tool
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/documents.readonly",
]
TOKEN_PATH = "./token.pickle"


def _get_google_service(service_name: str, version: str):
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "./credentials.json")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "wb") as token:
            pickle.dump(creds, token)
    return build(service_name, version, credentials=creds)


@tool("search_google_docs")
def search_google_docs(query: str) -> str:
    """Search Presidio's Google Drive for internal documents: campaign reports, meeting notes, feedback, and company data."""
    try:
        drive_service = _get_google_service("drive", "v3")
        docs_service = _get_google_service("docs", "v1")

        escaped = query.replace("'", "\\'")
        response = drive_service.files().list(
            q=(
                f"(fullText contains '{escaped}' or name contains '{escaped}')"
                f" and mimeType='application/vnd.google-apps.document'"
                f" and trashed=false"
            ),
            pageSize=5,
            fields="files(id, name)",
        ).execute()

        files = response.get("files", [])

        # Fallback: list all available docs so the agent can pick the right one
        if not files:
            all_resp = drive_service.files().list(
                q="mimeType='application/vnd.google-apps.document' and trashed=false",
                pageSize=20,
                fields="files(id, name)",
            ).execute()
            all_files = all_resp.get("files", [])
            if not all_files:
                return f"No Google Docs found matching '{query}' and no documents exist in Google Drive."
            names = ", ".join(f["name"] for f in all_files)
            return (
                f"No documents directly matched '{query}'. "
                f"Available Google Docs in Drive: {names}. "
                f"Try calling this tool again with one of those exact document names."
            )

        doc = docs_service.documents().get(documentId=files[0]["id"]).execute()
        content = ""
        for element in doc.get("body", {}).get("content", []):
            if "paragraph" in element:
                for run in element["paragraph"].get("elements", []):
                    if "textRun" in run:
                        content += run["textRun"].get("content", "")

        return f"Document: {files[0]['name']}\n\n{content.strip()[:3000]}"
    except Exception as e:
        error_msg = str(e)
        if "accessNotConfigured" in error_msg or "has not been used" in error_msg or "disabled" in error_msg:
            return (
                "Google Docs API is not enabled for this GCP project. "
                "Enable it at: https://console.developers.google.com/apis/api/docs.googleapis.com/overview "
                "then retry."
            )
        return f"Google Docs API error: {error_msg}"
