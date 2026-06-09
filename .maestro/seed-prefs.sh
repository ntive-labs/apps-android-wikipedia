#!/usr/bin/env bash
# Seed app SharedPreferences on the device via the dev-only TestSetupReceiver,
# then force-stop the app so the next launch reads them fresh.
# Usage: seed-prefs.sh '<json object>'   (keys = pref key strings, see MOCKING.md)
set -euo pipefail

PKG=org.wikipedia.dev

# Validate and compact to one line: am broadcast cannot carry newlines in extras.
JSON="$(printf '%s' "$1" | python3 -c 'import json,sys; print(json.dumps(json.loads(sys.stdin.read()), separators=(",", ":")))')"

# adb shell re-parses arguments on the device: wrap the JSON in single quotes
# so the device shell delivers it verbatim (JSON itself must not contain ').
adb shell am broadcast \
  -n "$PKG/org.wikipedia.dev.TestSetupReceiver" \
  --es prefs "'$JSON'"
adb shell am force-stop $PKG
