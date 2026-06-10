#!/usr/bin/env bash
# Run the system-dark-theme Maestro flow (Android commit 8b7b08008f): when the
# app follows the system theme and the system switches to dark mode (and the
# previously used theme was not dark), the app must default to the DARK theme,
# not BLACK.
#
# Three scenarios:
#   light  — matchSystemTheme on, Light theme, system night OFF  (baseline)
#   dark   — night mode flipped ON between launches; ActivityLifecycleHandler
#            must pick Dark (paper #202122), pre-fix picked Black (#000000)
#   toggle — matchSystemTheme off + night ON; flipping the switch inside the
#            theme chooser must likewise pick Dark (ThemeChooserDialog hunk)
#
# The verdict is quantitative: the dominant (modal) pixel color of the dark
# Settings screenshot and of the post-toggle chooser screenshot must be the
# Dark paper color #202122. A pre-8b7b08008f build yields #000000 and FAILS.
set -euo pipefail
cd "$(dirname "$0")/.."

PKG=org.wikipedia.dev
PORT=8081

if [ "${SKIP_BUILD:-}" != "1" ]; then
  ./gradlew installDevDebug
fi

python3 .maestro/fixtures/server.py "$PORT" &
SERVER_PID=$!
trap 'kill $SERVER_PID 2>/dev/null || true; adb shell cmd uimode night no >/dev/null 2>&1 || true' EXIT

seed() { # seed <matchSystemTheme>
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
    "matchSystemTheme": '"$1"',
    "colorTheme": 0,
    "mediaWikiBaseUri": "http://10.0.2.2:'"$PORT"'",
    "mediaWikiBaseUriSupportsLangCode": false
  }'
}

# Scenario A: cold start in light system mode, then flip to night mode.
adb shell cmd uimode night no
adb shell pm clear $PKG
seed true
maestro test --env STATE=light .maestro/system-dark-theme.yaml

adb shell cmd uimode night yes
maestro test --env STATE=dark .maestro/system-dark-theme.yaml

# Scenario B: match-system off, night already on; toggle the switch in-dialog.
adb shell pm clear $PKG
seed false
maestro test --env STATE=toggle .maestro/system-dark-theme.yaml

adb shell cmd uimode night no

# Quantitative theme check: dominant pixel color (mode) of each screenshot.
python3 - <<'EOF'
import subprocess, sys

def mode_color(path):
    out = subprocess.run(
        ["magick", path, "-depth", "8", "-define", "histogram:unique-colors=true",
         "-format", "%c", "histogram:info:-"],
        capture_output=True, text=True, check=True).stdout
    best, best_n = None, -1
    for line in out.splitlines():
        line = line.strip()
        if not line or ":" not in line or "#" not in line:
            continue
        n = int(line.split(":", 1)[0])
        hexcol = line.split("#", 1)[1].split()[0][:6].upper()
        if n > best_n:
            best, best_n = hexcol, n
    return best

DARK, BLACK = "202122", "000000"
checks = [
    (".maestro/screenshots/android-system-dark-theme-settings-light.png", "FFFFFF", "light baseline settings"),
    (".maestro/screenshots/android-system-dark-theme-settings-dark.png", DARK, "system-dark settings (lifecycle handler)"),
    (".maestro/screenshots/android-system-dark-theme-chooser-toggled.png", DARK, "post-toggle chooser (ThemeChooserDialog)"),
]
ok = True
for path, want, label in checks:
    got = mode_color(path)
    good = got == want
    ok = ok and good
    print(f"{'PASS' if good else 'FAIL'}: {label}: dominant color #{got} (expected #{want})")
if not ok:
    print("FAIL: pre-8b7b08008f behavior resolves the system Dark default to Black (#000000)")
sys.exit(0 if ok else 1)
EOF
