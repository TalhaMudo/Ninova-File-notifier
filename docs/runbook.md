# Runbook

Operational guide for the Ninova File Notifier.

## Running locally

```bash
# 1. Clone and install
git clone https://github.com/YOUR_USERNAME/Ninova-File-notifier.git
cd Ninova-File-notifier
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# 2. Configure
cp .env.example .env
# Edit .env with your actual credentials

# 3. Run
python -m src.main
```

## Running in GitHub Actions

The workflow triggers via `workflow_dispatch`. You can trigger it from:

- **GitHub UI**: Actions tab → Ninova File Notifier → Run workflow
- **Apple Shortcut**: See `docs/apple-shortcut-trigger.md`
- **curl**:
  ```bash
  curl -X POST \
    -H "Authorization: Bearer $PAT" \
    -H "Accept: application/vnd.github+json" \
    -d '{"ref":"main"}' \
    https://api.github.com/repos/OWNER/Ninova-File-notifier/actions/workflows/notify.yml/dispatches
  ```

## Common issues

### Login fails

- **Symptoms**: `RuntimeError: Could not locate username/password fields`
- **Cause**: ITU may have changed their SSO page layout.
- **Fix**: Check `debug_dumps/login_*.html` and `login_*.png` artifacts.
  Update selectors in `src/crawler/login.py`.

### No classes found

- **Symptoms**: `No class links found – page structure may have changed`
- **Cause**: Ninova dashboard layout changed or semester rolled over.
- **Fix**: Check `debug_dumps/no_class_links.*` artifacts. Update selectors
  in `src/crawler/files_page.py`.

### Bark notification not received

- **Symptoms**: Logs say "sent successfully" but no push arrives.
- **Cause**: Bark device key may be wrong or Bark server unreachable.
- **Fix**: Test Bark directly: `curl https://api.day.app/YOUR_KEY/test`

### Snapshot artifact missing

- **Symptoms**: Every run reports "No previous snapshot found (first run?)"
- **Cause**: Artifacts expire after 90 days, or the artifact name changed.
- **Fix**: This is normal for the first run. If persistent, check the
  `upload-artifact` / `download-artifact` step names match.

## Debug mode

Trigger with debug enabled to get screenshots and HTML dumps:

```bash
curl -X POST \
  -H "Authorization: Bearer $PAT" \
  -H "Accept: application/vnd.github+json" \
  -d '{"ref":"main","inputs":{"debug":"true"}}' \
  https://api.github.com/repos/OWNER/Ninova-File-notifier/actions/workflows/notify.yml/dispatches
```

Debug artifacts are uploaded and available in the workflow run's Artifacts section.
