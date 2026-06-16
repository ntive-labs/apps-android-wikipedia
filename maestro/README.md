# Maestro UI flows

[Maestro](https://docs.maestro.dev) flows for the personalized **"For you"** home
feed (`org.wikipedia.feed`).

## Flows

| File | What it does |
| --- | --- |
| `for-you-onboarding.yaml` | Cold start. Clears app state, walks the initial onboarding + personalization, selects interests, opts into the personalized feed, and screenshots the resulting "For you" feed. |
| `for-you-feed.yaml` | Already-onboarded happy path. Opens the "For you" tab and screenshots each module as it snaps into view. Run `for-you-onboarding.yaml` first (or use a device that has already finished onboarding). |

## Prerequisites

- A running Android emulator or connected device.
- The **dev** flavor installed (`appId: org.wikipedia.dev`):
  ```sh
  ./gradlew installDevDebug
  ```

## Running

From the repository root (screenshot paths are relative to the working directory):

```sh
# Cold-start onboarding path
maestro test maestro/for-you-onboarding.yaml

# Already-onboarded feed walkthrough
maestro test maestro/for-you-feed.yaml
```

Screenshots are written to `maestro/screenshots/`.

## Notes on stability

- The feed is personalized, so article titles/images vary per run. Assertions
  target only stable structural text ("For you", "Because of your interest:", …),
  never specific article content.
- The flows deny location permission, so the **Places of interest** module shows
  its "Stories from places you love" location prompt instead of (variable)
  nearby articles.
- `for-you-feed.yaml` dismisses launch-time interstitials (e.g. seasonal promos)
  and the one-time "Swipe to explore" coach mark if they appear.
- The "For you" feed is a vertically snapping pager — one module per screen,
  swipe up to advance. Module order is fixed by `ForYouModuleType`: Based on
  interest → Because you read → Continue reading → Places of interest → Random.
  Empty modules (e.g. Because you read / Continue reading with no history) are
  skipped, so the exact set of screens varies.
