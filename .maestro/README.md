# Maestro UI tests

End-to-end UI tests for the Android app, written as [Maestro](https://docs.maestro.dev) flows.

```
.maestro/
├── shared/     # reusable start-state flows, invoked with `runFlow` + `env`
├── mock/       # dependency-free mock HTTP backends used by flows that need fixed responses
├── run-tc-*.sh # convenience runners (start the mock, run the flow, stop the mock)
└── tc-*.yaml   # one test case per file; `tc-N-...-setS.yaml` wraps a parameter set
```

## Prerequisites

- A booted Android emulator (or device) with the **dev debug** build installed:
  `./gradlew installDevDebug` (package `org.wikipedia.dev`).
- `maestro` on `PATH`, and `python3` for flows that use a mock backend.

## Shared flows

Setup that more than one test needs lives in `shared/`, one file per start state, flat, and
parameterized through `env`. Every shared flow begins with a header comment block naming the
start state it reaches, its `env` surface, its assumptions and the branch that introduced it.

| flow | start state |
| --- | --- |
| `shared/login-screen-signed-out.yaml` | signed out, first-run onboarding completed, sitting on the Login screen. `MOCK_API_BASE_URL` (optional) points the app's home wiki at a mock server. |
| `shared/activity-tab-signed-in.yaml` | signed in and parked on the Activity tab, its one-time onboarding dismissed. `MOCK_API_BASE_URL`, `USERNAME`, `PASSWORD`, `SEED_ACTIVITY_DATA` are all required. |

## Mocking the backend

Debug builds accept these launch arguments (see `org.wikipedia.settings.AppConfig`), delivered
as `launchApp.arguments`:

| argument | meaning |
| --- | --- |
| `apiBaseUrl` | full base URL of a mock server, e.g. `http://10.0.2.2:8080`. Redirects the **home wiki's** Action API (`/w/api.php`), REST v1 (`/api/rest_v1/`) and core REST (`/w/rest.php/`). |
| `disableCertPinning` | informational on Android (no pinning is used; debug builds already allow cleartext). |
| `seedActivityData` | seeds the **local** activity data no HTTP mock can reach: one stored donation in `Prefs.donationResults` and three reading-history rows (with time spent) in the Room database. |
| `seedDonationDaysAgo` | how long ago the seeded donation happened; the Activity tab renders it as a relative time. Defaults to `5`. |

`10.0.2.2` is the emulator's alias for the host loopback. Commons, Wikidata, Meta and the
analytics intake are **not** redirected and still resolve to production.

## Addressing Compose UI by id

Compose screens have no `android:id`. The Activity tab and its customization screen apply
`Modifier.exposeTestTagsAsResourceIds()` (in `compose/extensions/Modifier.kt`) at their root,
which publishes every `Modifier.testTag` beneath as an Android resource id that `id:` selectors
can match. The Activity tab's tags are derived from `ModuleType`:

| tag | element |
| --- | --- |
| `activity_tab_customize_switch_<module>` | a switch on the customization screen |
| `activity_tab_module_<module>` | that module's content on the Activity tab |
| `activity_tab_logged_out` | the logged-out call to action |

`<module>` is the lowercased `ModuleType` name (`impact`, `reading_insights`, `timeline`,
`donations`, …).

## Test case 2 — Login completes after answering a CAPTCHA challenge

Flow: `tc-2-login-with-captcha.yaml` (parameter set wrapper: `tc-2-login-with-captcha-set0.yaml`).
Mock: `mock/captcha_login_server.py`.

```bash
./.maestro/run-tc-2.sh
```

or manually:

```bash
python3 .maestro/mock/captcha_login_server.py --port 8080 --answer AMBERTIDE &
maestro test .maestro/tc-2-login-with-captcha-set0.yaml
```

`takeScreenshot` writes relative to the working directory maestro is started from, so the
`tc-2-set0-*.png` files land next to wherever you ran the command. They are test output —
do not commit them.

The mock answers the first `action=clientlogin` POST with `FAIL`, then advertises a
FancyCaptcha `captchaId` through `action=query&meta=authmanagerinfo&amirequestsfor=login` —
which is what makes `LoginClient` surface the image-captcha widget — and serves the matching
CAPTCHA image at `/w/index.php?title=Special:Captcha/image`. The second `clientlogin` POST,
the one carrying `captchaId` + `captchaWord`, returns `PASS` only when the posted word matches
`--answer`.

## Test case 5 — Enabled Activity tab modules are shown

Flow: `tc-5-activity-tab-enabled-modules.yaml` (parameter set wrapper:
`tc-5-activity-tab-enabled-modules-set0.yaml`). Mock: `mock/activity_tab_server.py`.

```bash
./.maestro/run-tc-5.sh
```

or manually:

```bash
MOCK_USERNAME=maestro-user MOCK_PASSWORD=correct-horse-battery \
  python3 .maestro/mock/activity_tab_server.py &
./gradlew installDevDebug
maestro test .maestro/tc-5-activity-tab-enabled-modules-set0.yaml
```

The Activity tab reads its data from two places, so the flow uses two seams. Edit activity
(All time impact, Editing insights, Timeline) comes over HTTP from the mock backend through
`apiBaseUrl`. The stored donation and the reading history are never fetched over the network —
they live in `SharedPreferences` and the Room database — so `seedActivityData` writes them at
launch.

The flow then enables the Donations module and disables All time impact and Timeline on the
customization screen, re-opens the Activity tab, and asserts the donation card is rendered
while neither disabled module appears anywhere in the tab's scroll range. Both disabled
modules are proven to render *before* they are switched off, so the absence assertions cannot
pass vacuously.

Note that `clearState` does not remove the Wikipedia account from Android's `AccountManager`,
so on a device that has run this flow before the sign-in step is skipped (the signed-in state
is still asserted). `FRESH_INSTALL=1 ./.maestro/run-tc-5.sh` uninstalls first to exercise the
full login path.
