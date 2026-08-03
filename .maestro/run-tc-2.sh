#!/usr/bin/env bash
# Run Maestro test case 2 ("Login completes after answering a CAPTCHA challenge") against a
# booted Android emulator, starting and stopping the mock MediaWiki backend around it.
#
#   ./.maestro/run-tc-2.sh                 # runs every parameter set
#   ./.maestro/run-tc-2.sh tc-2-login-with-captcha-set0.yaml
#
# Requires: maestro on PATH, python3, an emulator with the dev debug build installed
# (`./gradlew installDevDebug`). The emulator reaches the host at 10.0.2.2.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${MOCK_PORT:-8080}"
ANSWER="${CAPTCHA_ANSWER:-AMBERTIDE}"

python3 "$HERE/mock/captcha_login_server.py" --port "$PORT" --answer "$ANSWER" &
MOCK_PID=$!
trap 'kill "$MOCK_PID" 2>/dev/null || true' EXIT

# Give the mock a moment to bind the port.
for _ in $(seq 1 20); do
  if curl -sf "http://127.0.0.1:$PORT/mock/reset" >/dev/null; then break; fi
  sleep 0.25
done

FLOWS=("$@")
if [ ${#FLOWS[@]} -eq 0 ]; then
  FLOWS=(tc-2-login-with-captcha-set0.yaml)
fi

for flow in "${FLOWS[@]}"; do
  echo "==> $flow"
  maestro test \
    -e "MOCK_API_BASE_URL=http://10.0.2.2:$PORT" \
    -e "CAPTCHA_ANSWER=$ANSWER" \
    "$HERE/$flow"
done
