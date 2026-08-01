#!/usr/bin/env bash
#
# Runs test case 5 ("Enabled Activity tab modules are shown").
#
# Brings up the mock MediaWiki backend, optionally builds and installs the dev debug APK, then
# runs the flow against a booted emulator.
#
#   .maestro/run-tc-5.sh                # build + install + run
#   SKIP_BUILD=1 .maestro/run-tc-5.sh   # run only (app already installed)
#
# Requires: a booted Android emulator (`adb devices`), `maestro`, python3, and - unless
# SKIP_BUILD=1 - a working Gradle setup.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

ADB="${ADB:-${ANDROID_HOME:-$HOME/Library/Android/sdk}/platform-tools/adb}"
APK="app/build/outputs/apk/dev/debug/app-dev-debug.apk"
MOCK_PORT="${MOCK_PORT:-8080}"
export MOCK_USERNAME="${MOCK_USERNAME:-maestro-user}"
export MOCK_PASSWORD="${MOCK_PASSWORD:-correct-horse-battery}"
export PORT="$MOCK_PORT"

mock_pid=""
cleanup() {
  if [[ -n "$mock_pid" ]] && kill -0 "$mock_pid" 2>/dev/null; then
    echo "==> Stopping mock backend (pid $mock_pid)"
    kill "$mock_pid" 2>/dev/null || true
  fi
}
trap cleanup EXIT

echo "==> Starting mock backend on port $MOCK_PORT (user: $MOCK_USERNAME)"
python3 .maestro/mock/activity_tab_server.py &
mock_pid=$!
sleep 2
curl -sf "http://127.0.0.1:${MOCK_PORT}/w/api.php?action=query&meta=tokens&type=login" >/dev/null \
  || { echo "Mock backend did not come up on port $MOCK_PORT"; exit 1; }

if [[ -z "${SKIP_BUILD:-}" ]]; then
  echo "==> Building the dev debug APK (the launch-arg seam is gated on BuildConfig.DEBUG)"
  ./gradlew assembleDevDebug
  echo "==> Installing $APK"
  "$ADB" install -r -d "$APK"
fi

mkdir -p .maestro/screenshots

# Maestro tears its on-device driver down after every run, which regularly leaves the adb server
# in a state where the next run reports "device offline" on its very first command. Bouncing the
# adb server first makes back-to-back runs reliable.
"$ADB" kill-server >/dev/null 2>&1 || true
sleep 2
"$ADB" start-server >/dev/null 2>&1 || true
"$ADB" wait-for-device shell 'while [ "$(getprop sys.boot_completed)" != "1" ]; do sleep 1; done'

maestro test .maestro/tc-5-activity-tab-enabled-modules-set0.yaml

echo "==> Done. Screenshots are in .maestro/screenshots/"
