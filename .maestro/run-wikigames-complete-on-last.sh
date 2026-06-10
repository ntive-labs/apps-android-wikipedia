#!/usr/bin/env bash
# Run the WikiGames complete-on-last-answer Maestro flow (commit fe1486bbed).
# Answering the last question must persist GAME_COMPLETED immediately, so a
# kill/relaunch at the final reveal lands on the results screen. The REST feed
# API is pointed at the local fixture server (9-event On This Day fixture for a
# deterministic 5-question game). RESTBaseUriFormat must also be seeded because
# the default format string hardcodes the https scheme regardless of
# mediaWikiBaseUri.
set -euo pipefail
cd "$(dirname "$0")/.."

PKG=org.wikipedia.dev
PORT=8081

if [ "${SKIP_BUILD:-}" != "1" ]; then
  ./gradlew installDevDebug
fi

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
maestro test .maestro/wikigames-complete-on-last-answer.yaml
