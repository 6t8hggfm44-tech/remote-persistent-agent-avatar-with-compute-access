#!/bin/sh
set -eu
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Presence needs Python 3.9 or newer. Ask Codex to help install it."
  exit 1
fi
echo "Presence will be available at http://127.0.0.1:8765"
echo "Keep this window open while using the app. Press Control-C to stop."
exec python3 -B -m app.server --port 8765
