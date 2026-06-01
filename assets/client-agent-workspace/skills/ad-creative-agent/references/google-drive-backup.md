# Google Drive Backup Handoff

Use this when the user wants generated creatives, prompts, manifests, or winner memory backed up to Google Drive.

## Rule

This skill should not teach Google Drive service-account setup from scratch. If Google Drive access is missing, broken, or confusing, hand off to the dedicated skill:

```text
skills/google-drive-service-account/
```

That skill handles:

- Creating a Google Cloud project.
- Enabling Google Drive API.
- Creating a service account.
- Creating/installing JSON credentials.
- Sharing the Drive folder with the service-account email.
- Verifying read/write access.
- Diagnosing 403/404/upload permission errors.

## When to Use the Handoff

Refer to `google-drive-service-account` when:

- No service account exists.
- The user does not know how to create one.
- The JSON key is missing.
- The Drive folder is not shared with the service account.
- Upload verification fails.
- There is a 403/404 Google Drive API error.
- The user needs a step-by-step guided setup.

## Backup Behavior

If Drive access is already configured:

1. Save everything locally first using `references/folder-structure.md`.
2. Upload/copy the same folder structure to the user's Drive folder.
3. Preserve paths where possible:

```text
Drive/[ad-creatives]/[client]/[product]/...
```

4. Never upload API keys or secret credential files.
5. Include manifests, prompt lineage, winners, images, and exported upload-ready files.

## If Drive Is Not Ready

Do not block creative generation just because Drive backup is unavailable.

Default behavior:

1. Generate and save locally.
2. Tell the user local output is ready.
3. Say Drive backup needs service-account setup/verification.
4. Use or recommend the `google-drive-service-account` skill to finish the Drive connection.

## Minimum User-Facing Explanation

Say:

```text
I can save everything locally now. For Google Drive backup, we need a Drive service account with Editor access to the target folder. I’ll use the google-drive-service-account skill to guide/verify that setup.
```
