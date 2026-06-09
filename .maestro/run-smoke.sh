#!/usr/bin/env bash
# Build and install the dev-debug app on the connected emulator,
# then run the Maestro launch smoke test against it.
set -euo pipefail
cd "$(dirname "$0")/.."

./gradlew installDevDebug
maestro test .maestro/smoke-launch.yaml
