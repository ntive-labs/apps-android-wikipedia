#!/usr/bin/env bash
# Run the dark-mode image-dimming Maestro flow twice (dim on / dim off) against
# the local fixture server, then verify the dimming coefficient quantitatively.
#
# The fixture search results use a deterministic pure-red (255,0,0) thumbnail
# served by the fixture server, so the dimmed value is directly measurable in
# the screenshots: DimImageTransformation draws a black overlay over native
# images in dark themes. With the mobile-web-matched coefficient (alpha 51/255,
# commit 2e336358d3) a red pixel dims to ~204; the previous coefficient
# (alpha 100/255) gave ~155. Dim off leaves it at ~255.
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

seed() { # seed <dimDarkModeImages>
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
    "matchSystemTheme": false,
    "colorTheme": 1,
    "dimDarkModeImages": '"$1"',
    "mediaWikiBaseUri": "http://10.0.2.2:'"$PORT"'",
    "mediaWikiBaseUriSupportsLangCode": false
  }'
}

adb shell pm clear $PKG
seed true
maestro test --env STATE=on .maestro/image-dimming.yaml

seed false
maestro test --env STATE=off .maestro/image-dimming.yaml

# Quantitative coefficient check: strongest red-dominant pixel in each search
# screenshot (red channel where green+blue are near zero — only the fixture
# thumbnail qualifies).
python3 - <<'EOF'
import subprocess, sys

def max_red(path):
    # txt: enumerate pixels via ImageMagick; avoids a Python imaging dependency.
    out = subprocess.run(["magick", path, "-depth", "8", "txt:-"],
                         capture_output=True, text=True, check=True).stdout
    best = 0
    for line in out.splitlines()[1:]:
        try:
            rgb = line.split("(", 1)[1].split(")", 1)[0].split(",")
            r, g, b = (int(v) for v in rgb[:3])
        except (IndexError, ValueError):
            continue
        if g < 60 and b < 60 and r > best:
            best = r
    return best

on = max_red(".maestro/screenshots/android-image-dimming-search-on.png")
off = max_red(".maestro/screenshots/android-image-dimming-search-off.png")
print(f"red thumbnail value: dim on = {on}, dim off = {off}")
ok = 190 <= on <= 215 and off >= 245
print("PASS: dimming coefficient matches mobile web (~20% black overlay)" if ok else
      f"FAIL: expected on in [190,215] (old coefficient gives ~155) and off >= 245")
sys.exit(0 if ok else 1)
EOF
