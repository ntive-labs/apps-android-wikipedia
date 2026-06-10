#!/usr/bin/env bash
# Pronunciation User-Agent flow (6c43d3fe3c): the MediaPlayer-backed
# pronunciation audio request must carry the app User-Agent (WikipediaApp/...)
# instead of the platform default (stagefright/...).
#
# The fixture server logs every request's User-Agent; after the flow taps
# PLAY PRONUNCIATION on the fixture-served article, this runner asserts the
# test-pron.ogg request's UA. See .maestro/MOCKING.md.
#
# Env: SKIP_BUILD=1 to reuse the installed APK.
set -euo pipefail
cd "$(dirname "$0")/.."

PKG=org.wikipedia.dev
PORT=8081
SERVER_LOG=$(mktemp /tmp/pron-ua-fixture-log.XXXXXX)

if [ "${SKIP_BUILD:-}" != "1" ]; then
  ./gradlew installDevDebug
fi

python3 .maestro/fixtures/server.py "$PORT" 2>"$SERVER_LOG" &
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

maestro test .maestro/pronunciation-user-agent.yaml

# Server-side assertion: the audio request must arrive with the app UA.
deadline=$((SECONDS + 20))
while [ $SECONDS -lt $deadline ]; do
  if grep "test-pron" "$SERVER_LOG" | grep -q "UA=WikipediaApp/"; then
    echo "OK: pronunciation audio request sent the app User-Agent:"
    grep "test-pron" "$SERVER_LOG"
    exit 0
  fi
  sleep 2
done

echo "FAIL: no test-pron request with UA=WikipediaApp/ observed." >&2
echo "--- audio requests seen: ---" >&2
grep "test-pron" "$SERVER_LOG" >&2 || echo "(none)" >&2
echo "--- full fixture log: ---" >&2
cat "$SERVER_LOG" >&2
exit 1
