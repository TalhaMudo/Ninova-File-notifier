# Security Guide

This repository is designed to be **public-safe**. No secrets should ever be
committed to the codebase.

## Where secrets live

| Secret             | Location                          |
|--------------------|-----------------------------------|
| NINOVA_USERNAME    | GitHub Actions → Settings → Secrets |
| NINOVA_PASSWORD    | GitHub Actions → Settings → Secrets |
| BARK_DEVICE_KEY   | GitHub Actions → Settings → Secrets |
| BARK_BASE_URL     | GitHub Actions → Settings → Secrets |
| GitHub PAT         | Apple Shortcut (on-device only)   |

## Setting up GitHub Secrets

1. Go to your repository on GitHub.
2. Navigate to **Settings → Secrets and variables → Actions**.
3. Click **New repository secret** for each secret listed above.
4. Paste the value and save.

## Safety measures in code

- **Env-only config**: All secrets are loaded from environment variables via
  `pydantic-settings`. The app refuses to start if any required var is missing.

- **Log redaction**: The `SecretFilter` in `src/logging_setup.py` replaces
  known secret values with `***` before writing to stdout.

- **`.gitignore`**: The `.env` file, snapshot state, debug dumps, and
  screenshots are all git-ignored.

- **No hardcoded values**: Grep the codebase — there are zero hardcoded
  credentials, tokens, or device keys.

## What to do if a secret leaks

1. **Rotate immediately**: Change the password / regenerate the token.
2. Update the GitHub Actions secret with the new value.
3. Update your Apple Shortcut if the PAT changed.
4. Check git history: `git log --all --oneline -- .env` should return nothing.
