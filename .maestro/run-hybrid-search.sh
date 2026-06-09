#!/usr/bin/env bash
# Run the hybrid-search Maestro flows against the local fixture server.
# Each scenario gets its own seeded state (AB group, onboarding flags), so the
# flows run one at a time with a re-seed in between. See .maestro/MOCKING.md.
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

# Base seed: suppress first-run UI, point MediaWiki + semantic-search APIs at
# the fixture server, and pin remote config so "en" is a hybrid-search language.
BASE_SEED='
  "initialOnboardingEnabled": false,
  "exploreFeedUpdatePromptShown": true,
  "readingChallengeOnboardingShown": true,
  "otdEntryDialogShown": true,
  "readingListShareTooltipShown": true,
  "showReadingListsSyncPrompt": false,
  "showCustomizeToolbarTooltip": false,
  "isYearInReviewEnabled": false,
  "mediaWikiBaseUri": "http://10.0.2.2:'"$PORT"'",
  "mediaWikiBaseUriSupportsLangCode": false,
  "semanticSearchBaseUri": "http://10.0.2.2:'"$PORT"'",
  "remote_config": "{\"androidv1\":{\"hybridSearchEnabled\":true,\"hybridSearchLanguages\":[\"en\"]}}"
'

run_scenario() {
  local extra_seed=$1 flow=$2
  adb shell pm clear $PKG
  .maestro/seed-prefs.sh "{ $BASE_SEED, $extra_seed }"
  maestro test "$flow"
}

# Group B (lexicalSemantic): first search visit shows onboarding; example query
# kicks off a hybrid search.
run_scenario '
  "ab_test_hybridSearch": 1,
  "hybridSearchOnboardingShown": false,
  "hybridSearchEnabled": false
' .maestro/hybrid-search-onboarding.yaml

# Group C (semanticLexical): onboarding already done; manual query shows
# title-only suggestions, then semantic-first results with rating buttons.
run_scenario '
  "ab_test_hybridSearch": 2,
  "hybridSearchOnboardingShown": true,
  "hybridSearchEnabled": true
' .maestro/hybrid-search-results.yaml

# Control group: no onboarding, standard search experience.
run_scenario '
  "ab_test_hybridSearch": 0,
  "hybridSearchOnboardingShown": false,
  "hybridSearchEnabled": false
' .maestro/hybrid-search-control.yaml

echo "All hybrid-search flows passed."
