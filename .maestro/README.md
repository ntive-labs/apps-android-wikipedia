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
- A **debug** build installed. The launch-argument seam that points the app at a mock backend and
  seeds local activity data (`org.wikipedia.settings.AppConfig`) is hard-gated on
  `BuildConfig.DEBUG`:

  ```
  ./gradlew assembleDevDebug
  adb install -r app/build/outputs/apk/dev/debug/app-dev-debug.apk
  ```

- `maestro` on `PATH`.

## Running

```
./.maestro/run-tc-5.sh
```

or, driving the flow by hand:

```
MOCK_USERNAME=maestro-user MOCK_PASSWORD=correct-horse-battery \
  python3 .maestro/mock/activity_tab_server.py &
maestro test .maestro/tc-5-activity-tab-enabled-modules-set0.yaml
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
      mockActivityData: true
```

`10.0.2.2` is the emulator's alias for the host loopback; use the machine's LAN IP on a physical
device. This redirects the home wiki's Action API (`/w/api.php`), REST v1 (`/api/rest_v1/`) and
Core REST (`/w/rest.php/`) only — Commons, Wikidata, Meta and analytics still resolve to
production, and the Explore feed (which asks a *language-prefixed* host) shows its offline state.

`mock/activity_tab_server.py` serves what the Activity tab needs: login (`action=clientlogin`
answers `PASS` for `MOCK_USERNAME`/`MOCK_PASSWORD`), user info, the GrowthExperiments user-impact
payload behind the impact / editing-insights modules, and `list=usercontribs` for the edit half of
the timeline.

### `mockActivityData`

Some of the Activity tab's data never comes from an API — it lives on the device. The
`mockActivityData` launch argument seeds it (debug builds only, see `AppConfig.seedActivityData`):

| Seeded | Where it lands | What it drives |
| --- | --- | --- |
| One donation, 3 days old | `Prefs.donationResults` | the Donation History module and its customization row |
| Two read articles, 15 min each | `HistoryEntry` + `PageImage` rows | articles read this month, time spent reading, the reading half of the timeline |

## Test tags

Compose modules are addressed by stable test tag rather than by localized text. `ModuleType`
derives them (`ActivityTabModules.kt`):

| Tag | Element |
| --- | --- |
| `activity_tab_module_<module>` | that module's content on the Activity tab |
| `activity_tab_customize_switch_<module>` | that module's switch on the customization screen |
| `activity_tab_logged_out` | the logged-out call to action on the Activity tab |

`<module>` is the lowercased `ModuleType` name (`time_spent`, `reading_insights`,
`editing_insights`, `impact`, `games`, `donations`, `timeline`). The Compose roots opt the tags
into the view hierarchy with `Modifier.exposeTestTagsAsResourceIds()`.

## Gotchas

- **Don't use `hideKeyboard` on Android.** It presses Back, and when the emulator takes input from
  a hardware keyboard (no soft keyboard on screen, which is the default for the AVDs we use) the
  Back press reaches the Activity and closes the screen under test.
- Prefer `runFlow: when: visible:` guards over long chains of `optional: true` taps — an optional
  tap that matches nothing burns its full timeout, which adds minutes to a flow.
- `clearState: true` wipes app data but **not** the AccountManager account, so a device that ran a
  signing-in flow before is still signed in on the next run. Guard the login steps with
  `when: visible: activity_tab_logged_out` instead of assuming a logged-out start.
