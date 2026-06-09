#!/usr/bin/env bash
# Run the WikiGames-card dismiss/undo Maestro flow. The games card is generated
# locally (no network mocking needed); the rest of the feed loads live.
set -euo pipefail
cd "$(dirname "$0")/.."

PKG=org.wikipedia.dev

if [ "${SKIP_BUILD:-}" != "1" ]; then
  ./gradlew installDevDebug
fi

adb shell pm clear $PKG
.maestro/seed-prefs.sh '{
  "initialOnboardingEnabled": false,
  "exploreFeedUpdatePromptShown": true,
  "readingChallengeOnboardingShown": true,
  "otdEntryDialogShown": true,
  "readingListShareTooltipShown": true,
  "showReadingListsSyncPrompt": false,
  "showCustomizeToolbarTooltip": false,
  "isYearInReviewEnabled": false
}'
maestro test .maestro/wikigames-card-dismiss.yaml
