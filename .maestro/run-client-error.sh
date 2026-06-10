#!/usr/bin/env bash
# Client-error logging flow (Android 2d908c3384): an HTTP failure (404) from
# any API request must be submitted to the Event Platform as a
# /mediawiki/client/error/2.0.0 event on the mediawiki.client.error stream.
#
# Dev builds log every EventPlatformClient.submit()ed event to logcat as an
# "EPEV {json}" line (submit-time seam mirroring the TKEV seam); after the flow
# we assert the client-error event's exact serialized fields.
# See .maestro/MOCKING.md.
set -euo pipefail
cd "$(dirname "$0")/.."

PKG=org.wikipedia.dev
PORT=8081

if [ "${SKIP_BUILD:-}" != "1" ]; then
  ./gradlew installDevDebug
fi

python3 .maestro/fixtures/server.py "$PORT" &
SERVER_PID=$!
trap 'kill $SERVER_PID 2>/dev/null || true' EXIT

# Fresh state, suppress first-run UI, point the API base URL at the fixture
# server (which 404s any request mentioning "errortrigger").
adb shell pm clear $PKG
.maestro/seed-prefs.sh '{
  "initialOnboardingEnabled": false,
  "exploreFeedUpdatePromptShown": true,
  "readingChallengeOnboardingShown": true,
  "otdEntryDialogShown": true,
  "readingListShareTooltipShown": true,
  "showReadingListsSyncPrompt": false,
  "showCustomizeToolbarTooltip": false,
  "isYearInReviewEnabled": false,
  "hybridSearchOnboardingShown": true,
  "hybridSearchEnabled": false,
  "mediaWikiBaseUri": "http://10.0.2.2:'"$PORT"'",
  "mediaWikiBaseUriSupportsLangCode": false
}'
adb logcat -c

maestro test .maestro/client-error-logging.yaml

# Assert the ClientErrorEvent was submitted with the expected serialized shape.
expect_event() {
  local pattern=$1
  local deadline=$((SECONDS + 20))
  while [ $SECONDS -lt $deadline ]; do
    if adb logcat -d | grep "EPEV" | grep -qF "$pattern"; then
      echo "OK: found $pattern"
      return 0
    fi
    sleep 2
  done
  echo "FAIL: missing expected client-error event fragment: $pattern" >&2
  echo "--- EPEV lines seen: ---" >&2
  adb logcat -d | grep "EPEV" >&2 || true
  exit 1
}

expect_event '"$schema":"/mediawiki/client/error/2.0.0"'
expect_event '"stream":"mediawiki.client.error"'
expect_event '"error_class":"ClientErrorEvent"'
expect_event '"status_code":404'
expect_event '"method":"GET"'
expect_event 'errortrigger'

# The client-error event must NOT carry a top-level dt (intake sets meta.dt).
if adb logcat -d | grep "EPEV" | grep '/mediawiki/client/error/2.0.0' | grep -qF '"dt"'; then
  echo 'FAIL: client-error event unexpectedly contains a "dt" field.' >&2
  exit 1
fi
echo "OK: client-error event carries no dt field."

echo "Client-error logging flow passed."
