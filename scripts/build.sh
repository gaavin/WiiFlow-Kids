#!/usr/bin/env bash
# Build WiiFlow Kids. Usage: scripts/build.sh [make args...]
# Examples:
#   scripts/build.sh
#   scripts/build.sh -C . -f Makefile.main
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source "$ROOT/scripts/env.sh"
exec make -f Makefile "$@"
