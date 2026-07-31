#!/usr/bin/env bash
#
# Runs test case 2 ("Login completes after answering a CAPTCHA challenge") for every
# parameter set: starts the mock MediaWiki backend, runs the Maestro flow against a booted
# emulator, then shuts the mock down again.
#
#   ./.maestro/run-tc-2.sh
#
# Requires: a booted Android emulator with a *debug* build of the app installed (the
# launch-argument seam in AppConfig is gated on BuildConfig.DEBUG), maestro on PATH, python3.
#
#   ./gradlew assembleDevDebug
#   adb install -r app/build/outputs/apk/dev/debug/app-dev-debug.apk
#
set -euo pipefail

cd "$(dirname "$0")/.."
REPO_ROOT="$(pwd)"

PORT="${PORT:-8080}"
# Screenshots are written by the flow itself, relative to the repo root (and git-ignored).
SHOTS="$REPO_ROOT/.maestro/screenshots"
mkdir -p "$SHOTS"

# One entry per parameter set: "<index>|<username>|<password>|<captcha answer>"
PARAMETER_SETS=(
  "0|maestro-user|correct-horse-battery|WIKI42"
)

MOCK_PID=""
cleanup() {
  if [[ -n "$MOCK_PID" ]] && kill -0 "$MOCK_PID" 2>/dev/null; then
    kill "$MOCK_PID" 2>/dev/null || true
    wait "$MOCK_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

for entry in "${PARAMETER_SETS[@]}"; do
  IFS='|' read -r set_index username password captcha <<<"$entry"

  echo "==> parameter set $set_index: username=$username captcha=$captcha"

  cleanup
  MOCK_USERNAME="$username" \
  MOCK_PASSWORD="$password" \
  MOCK_CAPTCHA_ANSWER="$captcha" \
  PORT="$PORT" \
    python3 .maestro/mock/captcha_login_server.py >"/tmp/tc-2-mock-set$set_index.log" 2>&1 &
  MOCK_PID=$!

  # Wait for the mock to accept connections before launching the app.
  for _ in $(seq 1 30); do
    if curl -sf "http://127.0.0.1:$PORT/w/api.php?action=query&meta=tokens&type=login" >/dev/null; then
      break
    fi
    sleep 0.5
  done

  maestro test ".maestro/tc-2-login-with-captcha-set$set_index.yaml"
done

echo "==> screenshots written to $SHOTS"
