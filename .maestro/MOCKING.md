# Mocking app state and network for Maestro tests

How we control app behavior for Maestro UI flows. Maestro drives the app as a
black box, so unlike Espresso it cannot inject dependencies — instead the app
exposes **dev-flavor-only runtime hooks**, and test scripts configure each
scenario before launching a flow. No rebuild is needed per scenario.

## Components

| Piece | Location | Purpose |
|---|---|---|
| `TestSetupReceiver` | `app/src/dev/java/org/wikipedia/dev/TestSetupReceiver.kt` | Broadcast receiver (dev flavor only) that writes SharedPreferences from a JSON payload |
| Receiver manifest | `app/src/dev/AndroidManifest.xml` | Registers the receiver; merged into dev builds only |
| Cleartext config | `app/src/dev/res/xml/network_security_config.xml` | Dev-only override permitting plain HTTP to `10.0.2.2` / `localhost` |
| `seed-prefs.sh` | `.maestro/seed-prefs.sh` | Sends the broadcast (with correct adb quoting) and force-stops the app |
| Fixture server | `.maestro/fixtures/server.py` | Local HTTP server returning canned MediaWiki API responses |
| Fixtures | `.maestro/fixtures/*.json` | Canned responses, routed by URL substring in `server.py` |
| Example | `.maestro/run-mock-search.sh` + `mock-search.yaml` | End-to-end mocked-search flow |

## The seeding contract

`TestSetupReceiver` accepts a `prefs` string extra containing a JSON object.
Keys are **SharedPreferences key strings** — the *values* in
`app/src/main/res/values/preference_keys.xml`, not the resource names.
Values are written with matching types (boolean / int / long / string).
The broadcast result code is the number of prefs written (`-1` = parse error,
`0` = payload didn't arrive — usually a quoting problem).

Always use `seed-prefs.sh`; it validates/compacts the JSON (adb extras cannot
contain newlines) and force-stops the app afterward so the next launch reads
the seeded state fresh:

```bash
adb shell pm clear org.wikipedia.dev      # optional: fully fresh state first
.maestro/seed-prefs.sh '{"initialOnboardingEnabled": false}'
maestro test .maestro/my-flow.yaml
```

**Important:** flows that rely on seeded state must NOT use
`launchApp: { clearState: true }` — that wipes the seeds. Use
`adb shell pm clear` *before* seeding instead (as `run-mock-search.sh` does).

## Canonical "clean launch" seed

Suppresses all first-run/promo UI so flows land directly on the main screen.
Mirrors the Espresso `DataInjector` defaults (`androidTest/.../base/BaseTest.kt`);
new promo screens get gated by new prefs over time, so when a flow is suddenly
blocked by an unexpected screen, find its pref in `Prefs.kt` and add it here
and to `BaseTest.DataInjector`.

```json
{
  "initialOnboardingEnabled": false,
  "exploreFeedUpdatePromptShown": true,
  "readingChallengeOnboardingShown": true,
  "otdEntryDialogShown": true,
  "readingListShareTooltipShown": true,
  "showReadingListsSyncPrompt": false,
  "showCustomizeToolbarTooltip": false,
  "isYearInReviewEnabled": false,
  "hybridSearchOnboardingShown": true,
  "hybridSearchEnabled": false
}
```

## Mocking the network

Point the app's API base URL at a local fixture server instead of live
Wikipedia. From the emulator, the host machine is `10.0.2.2`.

1. Start the server: `python3 .maestro/fixtures/server.py 8081 &`
2. Add to the seed JSON:
   ```json
   {
     "mediaWikiBaseUri": "http://10.0.2.2:8081",
     "mediaWikiBaseUriSupportsLangCode": false
   }
   ```
   (`...SupportsLangCode: false` stops the app prepending `en.` to the host —
   honored by `WikiSite.forLanguageCode`, which also preserves the `http`
   scheme. Both are existing developer settings, visible in the dev build's
   developer preferences.)
3. Add routes to `server.py`: each entry maps a URL substring to a fixture
   file. Unmatched requests return `{}`, which MediaWiki response models parse
   as empty results. The existing unit-test fixtures in `app/src/test/res/raw/`
   are valid response shapes to copy from.

The fixture server prints every request it receives — when a flow doesn't show
the data you expect, check that log first to see what the app actually asked for.

## Adding a new mock situation — checklist

1. **Is it already pref-controlled?** Most dialogs, onboarding, A/B buckets,
   and URL endpoints are. Find the key in `Prefs.kt` → `preference_keys.xml`,
   add it to your seed JSON. Done — no app code change.
2. **Is it an API response?** Add a route + fixture to `server.py`.
3. **Otherwise** add a hook: prefer a new pref read at the existing seam
   (following `Prefs.kt` patterns) over scattering `if (isDevRelease)` branches
   through feature code. Keep hooks runtime-controllable so one APK serves all
   scenarios, and gate anything new to the dev flavor.

## Gotchas

- **adb double-shell quoting**: extras pass through both the local and device
  shells. `seed-prefs.sh` handles this; if you broadcast manually and get
  result `0` or `-1`, your JSON arrived mangled (check
  `adb logcat -s TestSetupReceiver` and the `AndroidRuntime` crash buffer).
- **Force-stop after seeding** (`seed-prefs.sh` does it): prefs are read into
  memory at process start; seeding a running process has no effect on values
  already consumed (e.g. the base URL is applied in `WikipediaApp.onCreate`).
- **Thumbnails/images** in fixtures point at live `upload.wikimedia.org` URLs;
  they load over the real network (or fail gracefully). Don't assert on images
  in mocked flows.
- The dev build auto-enrolls in active experiments (e.g. hybrid search), which
  can add surprise onboarding screens — keep the clean-launch seed current.
