# Maestro UI tests

End-to-end UI tests for the Android app, written as [Maestro](https://docs.maestro.dev) flows.

```
.maestro/
├── shared/     # reusable start-state flows, invoked with `runFlow` + `env`
├── mock/       # dependency-free mock HTTP backends used by flows that need fixed responses
├── scripts/    # JavaScript helpers for `runScript`, e.g. reading a mock's request log
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
| `shared/login-captcha-challenge.yaml` | an image CAPTCHA challenge displayed on the Login screen, `USERNAME`/`PASSWORD` already submitted. Starts *from* the Login screen, so it composes after `shared/login-screen-signed-out.yaml`, and needs a backend that demands a CAPTCHA (`mock/captcha_login_server.py`). |

## Mocking the backend

Debug builds accept two launch arguments (see `org.wikipedia.settings.AppConfig`), delivered
as `launchApp.arguments`:

| argument | meaning |
| --- | --- |
| `apiBaseUrl` | full base URL of a mock server, e.g. `http://10.0.2.2:8080`. Redirects the **home wiki's** Action API (`/w/api.php`), REST v1 (`/api/rest_v1/`) and core REST (`/w/rest.php/`). |
| `disableCertPinning` | informational on Android (no pinning is used; debug builds already allow cleartext). |

`10.0.2.2` is the emulator's alias for the host loopback. Commons, Wikidata, Meta and the
analytics intake are **not** redirected and still resolve to production.

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

## Test case 3 — A replacement CAPTCHA image can be requested during login

Flow: `tc-3-request-new-captcha.yaml` (parameter set wrapper: `tc-3-request-new-captcha-set0.yaml`).
Mock: `mock/captcha_login_server.py`. Helper: `scripts/read-captcha-mock-stats.js`.

```bash
./.maestro/run-tc-3.sh
```

or manually:

```bash
python3 .maestro/mock/captcha_login_server.py --port 8080 &
maestro test \
  -e MOCK_API_BASE_URL=http://10.0.2.2:8080 \
  -e MOCK_STATS_URL=http://localhost:8080/mock/stats \
  .maestro/tc-3-request-new-captcha-set0.yaml
```

The control that asks for a replacement is the CAPTCHA image itself — `CaptchaHandler` wires
`captchaImage.setOnClickListener { requestNewCaptcha() }`, and the layout tells the user so
("Tap CAPTCHA to reload"). Each `action=fancycaptchareload` makes the mock mint a **new**
captcha id whose image spells `--reload-answer` instead of `--answer`, so the app ends up
loading genuinely different bytes — just like MediaWiki's FancyCaptcha.

An `ImageView`'s pixels are opaque to Maestro, so "the image changed" is verified from the
server side: `GET /mock/stats` reports every `Special:Captcha/image` request with its
captcha id and the SHA-256 of the bytes served, plus how many reloads were asked for.
`scripts/read-captcha-mock-stats.js` flattens that into `output.*` values, and the flow
asserts that the image fetched after the tap differs from the original and that exactly one
replacement was requested. Note the two mock URLs are **not** interchangeable:
`MOCK_API_BASE_URL` is how the emulator reaches the mock (`10.0.2.2`), `MOCK_STATS_URL` is how
maestro itself reaches it (`localhost`).

The mock resets its per-attempt bookkeeping whenever a credentials-only `clientlogin` arrives,
so the flow's "exactly one" assertions hold on re-runs without restarting the server.
