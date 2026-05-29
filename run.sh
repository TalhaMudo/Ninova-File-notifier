#!/bin/zsh
# Pulls the latest code from GitHub, then runs the Ninova checker.
# Called by the "Ninova Update" Apple Shortcut via "Run Shell Script".
#
# Usage from Shortcuts:
#   Shell: /bin/zsh
#   Script: /Users/talhamuderrisoglu/Documents/GitHub/Ninova-File-notifier/run.sh

set -euo pipefail

# Apple Shortcuts has a minimal PATH; ensure Homebrew binaries are reachable.
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

REPO="$( cd "$(dirname "$0")" && pwd )"
cd "$REPO"

# Pull the latest code — .env and state/ are git-ignored, so they are never overwritten.
git pull --ff-only

# Install/update Python dependencies (no-op when requirements.txt hasn't changed).
pip3 install -q -r requirements.txt

# Run the notifier.
python3 -m src.main
