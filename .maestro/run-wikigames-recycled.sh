#!/usr/bin/env bash
# Run the WikiGames recycled-events Maestro flow (commit 4824d3a9f7).
# The REST feed API is pointed at the local fixture server, which serves a
# 3-event On This Day response (onthisday_events_three.json). With only 3
# events the pairing loop must recycle events from the pool copy to build all
# 5 questions; pre-fix it crashed into the stuck error page after question 2.
# RESTBaseUriFormat must also be seeded because the default format string
# hardcodes the https scheme regardless of mediaWikiBaseUri.
set -euo pipefail
cd "$(dirname "$0")/.."

PKG=org.wikipedia.dev
PORT=8081

if [ "${SKIP_BUILD:-}" != "1" ]; then
  ./gradlew installDevDebug
fi

ONTHISDAY_FIXTURE=onthisday_events_three.json \
  python3 .maestro/fixtures/server.py $PORT &
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
maestro test .maestro/wikigames-recycled-events.yaml
