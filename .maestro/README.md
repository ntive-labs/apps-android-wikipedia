# Maestro UI flows

Maestro flows for the Wikipedia Android app, plus the mock backends they need.

## Layout

```
.maestro/
├── mock/                                        mock HTTP backends
│   └── activity_tab_server.py                   MediaWiki stand-in for the Activity tab flows
├── screenshots/                                 flow output (git-ignored)
├── run-tc-4.sh                                  runner for test case 4
├── tc-4-activity-tab-module-visibility.yaml     shared, parameterised flow
└── tc-4-activity-tab-module-visibility-set*.yaml  one thin wrapper per parameter set
```

## Conventions

- **Parameterised cases** are one shared flow plus a thin `runFlow` wrapper per parameter set.
  The shared flow declares **no `env:` block of its own** — a flow's own `env` can shadow the
  values a caller passes, which would silently pin every set to the same parameters. Wrappers
  supply every variable.
- **Target elements by id.** Compose screens opt in with
  `Modifier.exposeTestTagsAsResourceIds()` (`org.wikipedia.compose.extensions`), which publishes
  `Modifier.testTag(...)` values as Android resource ids so Maestro can address them with `id:`
  instead of localizable text. Tags for the Activity tab live on `ActivityTabModules.ModuleType`
  (`switchTestTag` / `moduleTestTag`).
- **Screenshots** are named `tc-<case>-set<S>-start.png`,
  `tc-<case>-set<S>-when<W>-before.png` and `tc-<case>-set<S>-when<W>-after.png` so they sort
  and parse. They are written to `.maestro/screenshots/` and are not committed.

## Prerequisites

- A booted Android emulator (`adb devices`).
- `maestro` on `PATH`.
- A **debug** build of the app: the launch-argument seam that repoints the app at a mock backend
  is hard-gated on `BuildConfig.DEBUG` (see `org.wikipedia.settings.AppConfig`).

## Test case 4 — Activity tab module visibility switches persist

Toggling an Activity tab module off in Customize hides it on the Activity tab and the switch
stays off when customization is reopened. Runs for three modules: Impact, Reading history and
Timeline.

```bash
.maestro/run-tc-4.sh                # build + install + run all three parameter sets
SKIP_BUILD=1 .maestro/run-tc-4.sh   # app already installed
SETS="0" .maestro/run-tc-4.sh       # just one set
```

To drive a single set by hand:

```bash
MOCK_USERNAME=maestro-user MOCK_PASSWORD=correct-horse-battery \
  python3 .maestro/mock/activity_tab_server.py &
./gradlew assembleDevDebug
adb install -r app/build/outputs/apk/dev/debug/app-dev-debug.apk
maestro test .maestro/tc-4-activity-tab-module-visibility-set0.yaml
```

The flow points the app at the mock with the launcher-intent extras
`apiBaseUrl=http://10.0.2.2:8080` and `disableCertPinning=true` (`10.0.2.2` is the emulator's
alias for the host loopback; use the machine's LAN IP for a physical device).

### Gotchas worth knowing

- **`clearState` does not sign the user out.** The account lives in Android's `AccountManager`,
  which survives `pm clear`. The flow therefore logs in only when the logged-out call to action
  is actually on screen, and verifies the signed-in state either way. To force a genuinely
  logged-out device, uninstall the app (`adb uninstall org.wikipedia.dev`).
- **Bounce through Home before using the overflow menu.** Coming back from the Activity tab
  onboarding leaves `MainActivity`'s toolbar hidden until `onTabChanged` runs again, so the
  overflow menu that opens Customize is not on screen yet.
- **Restart the adb server between Maestro runs.** Maestro uninstalls its on-device driver after
  each run, which regularly leaves the next run failing its first command with "device offline".
  `run-tc-4.sh` does this automatically.
- **The mock only serves the home wiki.** `WikiSite.forLanguageCode()` prefixes a language
  subdomain (`en.10.0.2.2`), which does not resolve, so anything routed that way — the Explore
  feed, and the timeline's user-contributions source — still fails under the override. That is
  the documented limitation of the seam; the Activity tab modules this case covers use
  `WikipediaApp.wikiSite`, which the override does cover.
