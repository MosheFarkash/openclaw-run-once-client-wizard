#!/usr/bin/env python3
"""Verify a Google Drive service account can read/write a shared folder."""
import argparse
import io
import json
import re
import sys
from datetime import datetime, timezone

SCOPES = ["https://www.googleapis.com/auth/drive"]


def folder_id(value: str) -> str:
    patterns = [
        r"/folders/([a-zA-Z0-9_-]+)",
        r"[?&]id=([a-zA-Z0-9_-]+)",
    ]
    for pat in patterns:
        m = re.search(pat, value)
        if m:
            return m.group(1)
    return value.strip()


def main():
    ap = argparse.ArgumentParser(description="Verify Google Drive service-account folder access")
    ap.add_argument("--credentials", required=True, help="Path to service-account JSON key")
    ap.add_argument("--folder-url", required=True, help="Drive folder URL or raw folder ID")
    ap.add_argument("--write-test", action="store_true", help="Upload then delete a tiny test file")
    args = ap.parse_args()

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseUpload
    except Exception as e:
        print("Missing dependencies. Install with:")
        print("  python3 -m pip install google-api-python-client google-auth")
        print(f"Import error: {e}")
        return 2

    fid = folder_id(args.folder_url)

    try:
        with open(args.credentials, "r", encoding="utf-8") as f:
            info = json.load(f)
        email = info.get("client_email", "unknown")
        creds = service_account.Credentials.from_service_account_file(args.credentials, scopes=SCOPES)
        svc = build("drive", "v3", credentials=creds, cache_discovery=False)

        folder = svc.files().get(
            fileId=fid,
            fields="id,name,mimeType,capabilities(canAddChildren,canEdit),driveId",
            supportsAllDrives=True,
        ).execute()
        print(f"Service account: {email}")
        print(f"Folder: {folder.get('name')} ({folder.get('id')})")
        print(f"Can add children: {folder.get('capabilities', {}).get('canAddChildren')}")
        print(f"Can edit: {folder.get('capabilities', {}).get('canEdit')}")

        res = svc.files().list(
            q=f"'{fid}' in parents and trashed=false",
            fields="files(id,name,mimeType,modifiedTime)",
            pageSize=10,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
        ).execute()
        files = res.get("files", [])
        print(f"Read test: OK ({len(files)} visible item(s), showing up to 10)")
        for item in files:
            print(f"- {item.get('name')} [{item.get('mimeType')}]")

        if args.write_test:
            content = f"OpenClaw Drive write test {datetime.now(timezone.utc).isoformat()}\n".encode("utf-8")
            media = MediaIoBaseUpload(io.BytesIO(content), mimetype="text/plain", resumable=False)
            meta = {"name": "openclaw-drive-write-test.txt", "parents": [fid]}
            created = svc.files().create(
                body=meta,
                media_body=media,
                fields="id,name",
                supportsAllDrives=True,
            ).execute()
            print(f"Write test upload: OK ({created.get('name')} / {created.get('id')})")
            svc.files().delete(fileId=created["id"], supportsAllDrives=True).execute()
            print("Write test cleanup: OK")

        print("Result: SUCCESS")
        return 0
    except Exception as e:
        print(f"Result: FAILED: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
