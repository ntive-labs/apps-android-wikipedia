# Maestro UI tests

End-to-end UI flows driven by [Maestro](https://docs.maestro.dev).

## Layout

| Path | What it is |
| --- | --- |
| `tc-<n>-<name>.yaml` | The shared, parameterized flow for a test case. |
| `tc-<n>-<name>-set<S>.yaml` | One thin wrapper per parameter set; sets `env` and `runFlow`s the shared flow. |
| `run-tc-<n>.sh` | Starts any mock backend the case needs, runs every parameter set, tears the mock down. |
| `mock/` | Standalone mock HTTP backends (python3 stdlib only, no install step). |
| `screenshots/` | Flow output. Git-ignored. |

## Prerequisites

- A booted Android emulator (`adb devices`).
- A **debug** build installed. The launch-argument seam that points the app at a mock backend
  (`org.wikipedia.settings.AppConfig`) is hard-gated on `BuildConfig.DEBUG`:

  ```
  ./gradlew assembleDevDebug
  adb install -r app/build/outputs/apk/dev/debug/app-dev-debug.apk
  ```

- `maestro` on `PATH`.

## Running

```
./.maestro/run-tc-2.sh
```

or, driving a single parameter set by hand:

```
MOCK_USERNAME=maestro-user MOCK_PASSWORD=correct-horse-battery MOCK_CAPTCHA_ANSWER=WIKI42 \
  python3 .maestro/mock/captcha_login_server.py &
maestro test .maestro/tc-2-login-with-captcha-set0.yaml
```

## Mock backend

Flows that need deterministic API responses point the app's **home wiki** at a local mock through
the launcher-intent extras `apiBaseUrl` and `disableCertPinning`:

```yaml
- launchApp:
    clearState: true
    arguments:
      apiBaseUrl: "http://10.0.2.2:8080"
      disableCertPinning: true
```

`10.0.2.2` is the emulator's alias for the host loopback; use the machine's LAN IP on a physical
device. This redirects the home wiki's Action API (`/w/api.php`), REST v1 (`/api/rest_v1/`) and
Core REST (`/w/rest.php/`) only — Commons, Wikidata, Meta and analytics still resolve to
production.
