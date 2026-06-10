#!/usr/bin/env bash
# Run the hybrid-search Maestro flows against the local fixture server.
# Each scenario gets its own seeded state (AB group, onboarding flags), so the
# flows run one at a time with a re-seed in between. See .maestro/MOCKING.md.
#
# As of commit 517351d4cd (hybrid search instrumentation) each scenario also
# asserts that the expected TestKitchen events were submitted. Dev builds log
# every submitted event to logcat as a "TKEV {json}" line (queue-time seam in
# TestKitchenClient), so after each flow we grep the log for expected
# action/element/experiment markers.
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

expect_events() {
  # expect_events <scenario-name> <pattern>...
  # Each pattern must appear in some TKEV logcat line within the timeout.
  local scenario=$1; shift
  local deadline=$((SECONDS + 20))
  local missing=("$@")
  while [ ${#missing[@]} -gt 0 ] && [ $SECONDS -lt $deadline ]; do
    local log
    log=$(adb logcat -d | grep "TKEV" || true)
    local still=()
    for pattern in "${missing[@]}"; do
      if ! grep -qF "$pattern" <<<"$log"; then
        still+=("$pattern")
      fi
    done
    missing=("${still[@]+"${still[@]}"}")
    [ ${#missing[@]} -gt 0 ] && sleep 2
  done
  if [ ${#missing[@]} -gt 0 ]; then
    echo "FAIL [$scenario]: missing expected TestKitchen events:" >&2
    printf '  %s\n' "${missing[@]}" >&2
    exit 1
  fi
  echo "OK [$scenario]: all expected TestKitchen events observed."
}

run_scenario() {
  local extra_seed=$1 flow=$2
  adb shell pm clear $PKG
  .maestro/seed-prefs.sh "{ $BASE_SEED, $extra_seed }"
  adb logcat -c
  maestro test "$flow"
}

# Group B (lexicalsemantic): first search visit shows onboarding; example query
# kicks off a hybrid search.
run_scenario '
  "ab_test_apps_hybridsearch": 1,
  "hybridSearchOnboardingShown": false,
  "hybridSearchEnabled": false
' .maestro/hybrid-search-onboarding.yaml
expect_events onboarding \
  '"funnel_name":"hybrid_search_onboarding"' \
  '"element_id":"onboarding_query"' \
  '"enrolled":"apps_hybridsearch"' \
  '"assigned":"lexicalsemantic"' \
  '"action":"show_hybrid_result"' \
  '"action":"search_impression"'

# Group C (semanticlexical): onboarding already done; manual query shows
# title-only suggestions, then semantic-first results with rating buttons.
run_scenario '
  "ab_test_apps_hybridsearch": 2,
  "hybridSearchOnboardingShown": true,
  "hybridSearchEnabled": true
' .maestro/hybrid-search-results.yaml
expect_events results \
  '"action":"search_impression"' \
  '"action":"search_init"' \
  '"action":"show_hybrid_result"' \
  '"element_id":"semantic_search_card"' \
  '"element_id":"thumb_up"' \
  '"assigned":"semanticlexical"'

# Group C again: close (X) button clears the query, keeps search active, and
# logs search_close; backing out logs search_back.
run_scenario '
  "ab_test_apps_hybridsearch": 2,
  "hybridSearchOnboardingShown": true,
  "hybridSearchEnabled": true
' .maestro/hybrid-search-close-button.yaml
expect_events close-button \
  '"element_id":"search_close"' \
  '"element_id":"search_back"'

# Control group: no onboarding, standard search experience; standard search
# events still flow with the control experiment group attached.
run_scenario '
  "ab_test_apps_hybridsearch": 0,
  "hybridSearchOnboardingShown": false,
  "hybridSearchEnabled": false
' .maestro/hybrid-search-control.yaml
expect_events control \
  '"action":"search_impression"' \
  '"action":"search_init"' \
  '"action":"show_search_result"' \
  '"assigned":"control"'

echo "All hybrid-search flows passed."
