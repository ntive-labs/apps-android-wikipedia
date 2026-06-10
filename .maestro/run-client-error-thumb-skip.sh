#!/usr/bin/env bash
# 320px-thumbnail client-error skip flow (Android 763158c976): HTTP failures
# (404) from requests whose URL contains "/320px-" must NOT be reported to the
# mediawiki.client.error logging-intake stream (known Commons rate-limit noise
# from old saved articles), while other HTTP failures must still be reported.
#
# The REST feed API is pointed at the local fixture server serving
# onthisday_events_thumb404.json: every On This Day event page has a thumbnail
# URL that 404s (fixture "errortrigger" rule) — 5 contain /320px- (must be
# skipped) and 4 control URLs contain /330px- (must be logged). The flow plays
# the full Which Came First game so every event card requests its thumbnail
# through the shared OkHttp client -> UnsuccessfulResponseInterceptor.
#
# Dev builds log every EventPlatformClient.submit()ed event to logcat as an
# "EPEV {json}" line (see .maestro/MOCKING.md); after the flow we assert the
# control client-error events are present and no /320px- event exists.
set -euo pipefail
cd "$(dirname "$0")/.."

PKG=org.wikipedia.dev
PORT=8081

if [ "${SKIP_BUILD:-}" != "1" ]; then
  ./gradlew installDevDebug
fi

ONTHISDAY_FIXTURE=onthisday_events_thumb404.json \
  python3 .maestro/fixtures/server.py "$PORT" &
SERVER_PID=$!
trap 'kill $SERVER_PID 2>/dev/null || true' EXIT

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
  "mediaWikiBaseUriSupportsLangCode": false,
  "RESTBaseUriFormat": "http://%2$s/api/rest_v1/"
}'
adb logcat -c

maestro test .maestro/client-error-thumb-skip.yaml

# Positive control: the /330px- thumbnail 404s MUST be reported as client errors.
expect_event() {
  local pattern=$1
  local deadline=$((SECONDS + 20))
  while [ $SECONDS -lt $deadline ]; do
    if adb logcat -d | grep "EPEV" | grep '/mediawiki/client/error/2.0.0' | grep -qF "$pattern"; then
      echo "OK: found client-error event with $pattern"
      return 0
    fi
    sleep 2
  done
  echo "FAIL: missing expected client-error event fragment: $pattern" >&2
  echo "--- EPEV lines seen: ---" >&2
  adb logcat -d | grep "EPEV" >&2 || true
  exit 1
}

expect_event '330px-errortrigger-log'
expect_event '"status_code":404'

# The fix under test: NO client-error event may reference a /320px- URL.
if adb logcat -d | grep "EPEV" | grep '/mediawiki/client/error/2.0.0' | grep -qF '320px-errortrigger-skip'; then
  echo 'FAIL: a /320px- thumbnail HTTP failure was reported to mediawiki.client.error.' >&2
  echo "--- offending EPEV lines: ---" >&2
  adb logcat -d | grep "EPEV" | grep '/mediawiki/client/error/2.0.0' | grep '320px-errortrigger-skip' >&2 || true
  exit 1
fi
echo "OK: no client-error event for /320px- thumbnails."

echo "Client-error 320px-thumbnail skip flow passed."
