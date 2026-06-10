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
# the fixture server, and make "en" a hybrid-search language via the dev seam
# (6240fa0d02 removed the remote-config hybridSearchLanguages override; the
# compiled-in list is now el+fr — see the fr-enabled scenario below).
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
  "hybridSearchSupportedLanguagesOverride": "en",
  "remote_config": "{\"androidv1\":{\"hybridSearchEnabled\":true}}"
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
  '"element_id":"learn_more"' \
  '"enrolled":"apps_hybridsearch"' \
  '"assigned":"lexicalsemantic"' \
  '"action":"show_hybrid_result"' \
  '"action":"search_impression"'
# b7745030f3: the onboarding Learn More button must log learn_more, never the
# old learn_button elementId.
if adb logcat -d | grep "TKEV" | grep -qF '"element_id":"learn_button"'; then
  echo "FAIL [onboarding]: obsolete learn_button event was emitted." >&2
  exit 1
fi
echo "OK [onboarding]: no obsolete learn_button event."

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
  '"assigned":"semanticlexical"' \
  '\"x_search_id\":\"maestro-search-id-123\"'

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

# Group C: a query with zero lexical results in the title-only screen must show
# the pinned "Search for:" bar (not the "No results" empty state), and tapping
# it runs the semantic search (Android 9512546822).
run_scenario '
  "ab_test_apps_hybridsearch": 2,
  "hybridSearchOnboardingShown": true,
  "hybridSearchEnabled": true
' .maestro/hybrid-search-empty-title-only.yaml
expect_events empty-title-only \
  '"action":"search_init"' \
  '"action":"show_hybrid_result"' \
  '"assigned":"semanticlexical"'

# Group C, two app languages (en + fr, only en hybrid-enabled): entering hybrid
# results hides the keyboard; switching to the FR tab shows the standard
# "No results" state (keyboard stays down); switching back to EN re-renders the
# empty title-only state and must bring the soft keyboard back up
# (Android 4778ade23b). Keyboard visibility is asserted via dumpsys, since the
# IME is not part of the app's view hierarchy.
run_scenario '
  "ab_test_apps_hybridsearch": 2,
  "hybridSearchOnboardingShown": true,
  "hybridSearchEnabled": true,
  "languageApp": "en,fr"
' .maestro/hybrid-search-no-results-keyboard.yaml
if adb shell dumpsys input_method | grep -q "mInputShown=true"; then
  echo "OK [no-results-keyboard]: soft keyboard is shown after returning to the experiment language tab."
else
  echo "FAIL [no-results-keyboard]: soft keyboard not shown after returning to the experiment language tab." >&2
  exit 1
fi
expect_events no-results-keyboard \
  '"action":"search_init"' \
  '"element_id":"semantic_search_explicit"' \
  '"assigned":"semanticlexical"'

# French app language, NO languages override (the "" seed clears the BASE_SEED
# seam): onboarding must appear because "fr" is now in the compiled-in supported
# list (6240fa0d02). Asserts French chrome plus the translated onboarding title.
run_scenario '
  "ab_test_apps_hybridsearch": 1,
  "hybridSearchOnboardingShown": false,
  "hybridSearchEnabled": false,
  "hybridSearchSupportedLanguagesOverride": "",
  "languageApp": "fr"
' .maestro/hybrid-search-fr-enabled.yaml
expect_events fr-enabled \
  '"funnel_name":"hybrid_search_onboarding"' \
  '"assigned":"lexicalsemantic"'

# French strings (6d0b3e0c4e): same fr-enabled scenario, but the app's UI
# locale is also set to French (per-app locale, API 33+) so values-fr resources
# render. The flow asserts this commit's updated FR copy through onboarding,
# results header, turn-off menu, and the hybrid search hint. The locale is set
# AFTER the pm clear/seed (run_scenario) and reset afterwards so later
# scenarios keep the English chrome.
FR_SEED='
  "ab_test_apps_hybridsearch": 1,
  "hybridSearchOnboardingShown": false,
  "hybridSearchEnabled": false,
  "hybridSearchSupportedLanguagesOverride": "",
  "languageApp": "fr"
'
adb shell pm clear $PKG
.maestro/seed-prefs.sh "{ $BASE_SEED, $FR_SEED }"
adb logcat -c
adb shell cmd locale set-app-locales $PKG --locales fr-FR
trap 'adb shell cmd locale set-app-locales $PKG --locales ""; kill $SERVER_PID 2>/dev/null || true' EXIT
maestro test .maestro/hybrid-search-fr-strings.yaml
adb shell cmd locale set-app-locales $PKG --locales ""
trap 'kill $SERVER_PID 2>/dev/null || true' EXIT
expect_events fr-strings \
  '"funnel_name":"hybrid_search_onboarding"' \
  '"element_id":"onboarding_query"' \
  '"assigned":"lexicalsemantic"'

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
