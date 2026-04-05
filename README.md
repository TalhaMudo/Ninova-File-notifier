# Ninova File Notifier

Automatically detect new file uploads on ITU Ninova and get push notifications
via [Bark](https://github.com/Finb/Bark).

## How it works

1. **Trigger** — Tap a shortcut on Apple Watch → calls GitHub Actions API
2. **Crawl** — Playwright logs into Ninova, navigates classes, extracts file lists
3. **Compare** — Current file list is diffed against a persisted snapshot
4. **Notify** — New files trigger a Bark push notification to your device

```
Apple Watch → GitHub API → Actions Runner → Playwright → Ninova
                                                ↓
                                        Compare snapshots
                                                ↓
                                          Bark → iPhone
```

## Quick start

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/Ninova-File-notifier.git
cd Ninova-File-notifier

# Install
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# Configure
cp .env.example .env   # fill in your credentials

# Run
python -m src.main
```

## GitHub Actions setup

1. Add these **repository secrets** (Settings → Secrets → Actions):
   - `NINOVA_USERNAME`
   - `NINOVA_PASSWORD`
   - `BARK_DEVICE_KEY`
   - `BARK_ICON_URL` (optional, e.g. `https://day.app/assets/images/avatar.jpg`)

2. Optional: if you use a self-hosted Bark server, edit
   `.github/workflows/notify.yml` and change `BARK_BASE_URL`.

3. Trigger manually from the Actions tab, or set up an Apple Shortcut
   (see [docs/apple-shortcut-trigger.md](docs/apple-shortcut-trigger.md)).

## Project structure

```
src/
├── main.py              # Entry point
├── config.py            # Env-based settings (no hardcoded secrets)
├── models.py            # FileEntry and Snapshot data models
├── logging_setup.py     # Logger with secret redaction
├── browser/
│   └── session.py       # Playwright browser context manager
├── crawler/
│   ├── login.py         # ITU SSO login automation
│   ├── files_page.py    # Class navigation and file collection
│   └── extractors.py    # File metadata extraction strategies
├── state/
│   ├── store.py         # Snapshot load/save (JSON file)
│   └── compare.py       # Diff logic to find new files
├── notify/
│   ├── bark.py          # Bark API client
│   └── message_builder.py  # Notification formatting
└── utils/
    ├── debug.py         # Screenshot and HTML dump on failure
    ├── retry.py         # Async retry decorator with backoff
    ├── timeouts.py      # Playwright timeout helpers
    └── dom_waits.py     # DOM readiness utilities
```

## Documentation

- [Apple Shortcut trigger setup](docs/apple-shortcut-trigger.md)
- [Security guide](docs/security.md)
- [Runbook](docs/runbook.md)

## License

MIT
