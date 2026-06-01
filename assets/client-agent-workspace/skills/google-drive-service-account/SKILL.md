---
name: google-drive-service-account
description: Guide a client or operator through creating, installing, and verifying a Google Drive service account for OpenClaw/agent access to shared Drive folders; use for Google Drive API setup, service account email/key creation, folder sharing, and upload/download verification.
---

# Google Drive Service Account Setup

Use this skill when a user wants to connect Google Drive folders to OpenClaw/agents using a Google Cloud service account.

## Goal

Create a narrow Drive integration where the agent can read/write only folders explicitly shared with a service account. Do **not** ask for the user's Google password. Avoid broad OAuth unless the user specifically needs access to their entire Drive.

## Recommended client-facing framing

Say this, in the user's language:

> We create a technical Google user for OpenClaw, then share only the specific Drive folder with that user. OpenClaw does not get your Google password and does not automatically get access to your entire Drive.

## Choose the path

1. **If a service account already exists**: give the client the service-account email and ask them to share the folder with **Editor** access.
2. **If no service account exists**: guide them through creating one in Google Cloud Console, then install the JSON key in OpenClaw.
3. **If the client is non-technical**: prefer a live guided flow. Do not dump all steps at once; give 1-2 steps, wait for confirmation/screenshots, then continue.

## Manual setup workflow

### 1) Create/choose Google Cloud project

Client goes to: `https://console.cloud.google.com/`

- Create project: `OpenClaw Drive Access` (or use an existing trusted project).
- Confirm the correct Google account/org is selected.

### 2) Enable Google Drive API

Path:

- APIs & Services → Library → search `Google Drive API` → Enable

### 3) Create service account

Path:

- IAM & Admin → Service Accounts → Create service account

Suggested values:

- Service account name: `openclaw-drive`
- Service account ID: `openclaw-drive`
- Description: `Service account for OpenClaw to access explicitly shared Google Drive folders`

No project-level role is usually required for Drive folder sharing. If Google asks for a role, skip/continue without granting broad roles.

### 4) Create JSON key

Path:

- Service account → Keys → Add key → Create new key → JSON

Security:

- Treat this JSON like a password.
- Do not paste it into chat unless the channel is explicitly approved for secrets.
- Prefer secure upload or placing it directly on the OpenClaw server.

### 5) Install key in OpenClaw

Preferred path on the OpenClaw host:

```bash
mkdir -p ~/.openclaw/secrets
chmod 700 ~/.openclaw/secrets
mv /path/to/downloaded-key.json ~/.openclaw/secrets/google-drive-service-account.json
chmod 600 ~/.openclaw/secrets/google-drive-service-account.json
```

If the agent is doing the install, ask for approval before handling secret files. Do not print JSON key contents.

### 6) Share the Drive folder

Client creates/selects a folder in Google Drive, clicks Share, and adds the service-account email, e.g.:

```text
openclaw-drive@PROJECT_ID.iam.gserviceaccount.com
```

Permission:

- **Viewer** = read/download only
- **Editor** = upload/edit/delete files in that folder

Ask for Editor only when uploads/edits are required.

### 7) Verify access

Use the bundled script when Python dependencies are available:

```bash
python3 skills/google-drive-service-account/scripts/verify_drive_access.py \
  --credentials ~/.openclaw/secrets/google-drive-service-account.json \
  --folder-url 'https://drive.google.com/drive/folders/FOLDER_ID' \
  --write-test
```

If only read access is expected, omit `--write-test`.

## Agent behavior

- Be calm and step-by-step. For non-technical clients, give one action at a time.
- If they share screenshots, tell them exactly what to click next.
- Never request broad Drive access when a shared folder is enough.
- Never tell the user to make `Anyone with the link can edit` unless it is temporary/non-sensitive and they understand the risk.
- Prefer service-account folder sharing over OAuth for this use case.
- If a command fails, diagnose before asking the user to redo setup.

## Common issues

- **403 / insufficient permissions**: Drive API disabled, folder not shared with the service-account email, or key belongs to a different project/account.
- **404 / file not found**: folder ID wrong, or service account cannot see it.
- **Can list but cannot upload**: folder shared as Viewer, not Editor.
- **Shared Drive/team drive**: service account may need explicit membership or shared-drive support in the API call.
- **Workspace admin restrictions**: client org may block external sharing or service accounts; ask admin to allow the service-account email.

## Client mini-script

Use this short version when Moshe/client needs instructions:

1. Open Google Cloud Console and create a project called `OpenClaw Drive Access`.
2. Enable `Google Drive API`.
3. Create a service account called `openclaw-drive`.
4. Create a JSON key for it and install it in OpenClaw.
5. Copy the service-account email.
6. Share the target Google Drive folder with that email as Editor.
7. Give OpenClaw the folder link and run a read/write test.
