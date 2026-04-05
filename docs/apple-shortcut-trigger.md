# Triggering from Apple Watch / iPhone Shortcut

This guide explains how to set up an Apple Shortcut that triggers the Ninova
File Notifier workflow via the GitHub Actions API.

## Prerequisites

1. A **GitHub Personal Access Token (PAT)** with `repo` and `actions` scopes.
   - Go to https://github.com/settings/tokens → Generate new token (classic).
   - Select scopes: `repo`, `workflow`.
   - Copy the token immediately — you won't see it again.

2. Know your **workflow file name**: `notify.yml`
3. Know your **repo**: `<your-username>/Ninova-File-notifier`

## API Call

The Shortcut will make a single HTTP POST request:

```
POST https://api.github.com/repos/{owner}/{repo}/actions/workflows/notify.yml/dispatches
```

### Headers

| Header          | Value                    |
|-----------------|--------------------------|
| Authorization   | Bearer {YOUR_PAT_TOKEN}  |
| Accept          | application/vnd.github+json |
| Content-Type    | application/json         |

### Body

```json
{
  "ref": "main",
  "inputs": {
    "debug": "false"
  }
}
```

## Apple Shortcut Setup (step by step)

1. Open the **Shortcuts** app on iPhone or Apple Watch.
2. Tap **+** to create a new shortcut.
3. Add action: **Get Contents of URL**.
4. Set **Method** to `POST`.
5. Set **URL** to:
   ```
   https://api.github.com/repos/YOUR_USERNAME/Ninova-File-notifier/actions/workflows/notify.yml/dispatches
   ```
6. Add **Headers**:
   - `Authorization` → `Bearer YOUR_PAT_HERE`
   - `Accept` → `application/vnd.github+json`
   - `Content-Type` → `application/json`
7. Set **Request Body** to JSON:
   ```json
   {"ref": "main", "inputs": {"debug": "false"}}
   ```
8. Save the shortcut with a name like "Check Ninova".
9. (Optional) Add it to Apple Watch face as a complication.

## Security Notes

- Store your PAT in the Shortcut itself — it is encrypted on-device and in
  iCloud Keychain.
- **Never** commit your PAT to this repository.
- The PAT only needs `repo` + `workflow` scopes. Use a fine-grained token
  limited to this single repository if possible.
- Rotate the token periodically.

## Testing

You can test the API call from a terminal:

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_PAT" \
  -H "Accept: application/vnd.github+json" \
  -d '{"ref":"main"}' \
  https://api.github.com/repos/YOUR_USERNAME/Ninova-File-notifier/actions/workflows/notify.yml/dispatches
```

A `204 No Content` response means the workflow was triggered successfully.
Check the Actions tab in your repository to see the run.
