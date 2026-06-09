#!/usr/bin/env bash
# Build/install the dev-debug app, seed test state, and run the mocked-search
# Maestro flow against a local fixture server. See .maestro/MOCKING.md.
set -euo pipefail
cd "$(dirname "$0")/.."

PKG=org.wikipedia.dev
PORT=8081

./gradlew installDevDebug

python3 .maestro/fixtures/server.py "$PORT" &
SERVER_PID=$!
trap 'kill $SERVER_PID 2>/dev/null || true' EXIT

# Fresh state, then suppress all first-run UI (mirrors the Espresso DataInjector
# defaults) and point the app's API base URL at the fixture server.
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

maestro test .maestro/mock-search.yaml
