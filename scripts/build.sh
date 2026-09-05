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

# data/theme is the copy bin2s compiles into the dol. Refresh it from the
# canonical files first so the built-in fallbacks can never drift from what
# the release actually ships.
cp "$ROOT/wii/wiiflow/themes_lite/default.ini"            "$ROOT/data/theme/kids_theme.ini"
cp "$ROOT/wii/wiiflow/themes_lite/coverflows/default.ini" "$ROOT/data/theme/kids_coverflow.ini"
cp "$ROOT/out/imgs/font.ttf"                              "$ROOT/data/theme/font.ttf"
for f in background butleft butcenter butright butsleft butscenter butsright \
         btnprev btnnext btnprevs btnnexts; do
	cp "$ROOT/out/imgs/$f.png" "$ROOT/data/theme/$f.png"
done

exec make -f Makefile "$@"
