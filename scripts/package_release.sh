#!/usr/bin/env bash
# Assemble a ready-to-extract SD card payload for the releases tab.
#
# The zip mirrors an SD card root: unzip it there, copy your games in, and
# WiiFlow Kids runs with the shipped look and settings. The dol also carries
# its theme, coverflow layout, typeface and chrome internally, so it still
# renders correctly if only apps/wiiflow/boot.dol survives the copy — the
# files below are what make it themeable, not what make it work.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VERSION="${1:-$(sed -n 's/.*APP_VERSION[[:space:]]*"\([^"]*\)".*/\1/p' source/defines.h | head -1)-kids}"
NAME="WiiFlow-Kids-${VERSION}"
STAGE="release/${NAME}"

[ -f out/boot.dol ] || { echo "package_release: out/boot.dol missing — run scripts/build.sh first" >&2; exit 1; }

rm -rf "$STAGE"
mkdir -p "$STAGE/apps/wiiflow" "$STAGE/wiiflow"

# --- homebrew app ----------------------------------------------------------
install -m644 out/boot.dol              "$STAGE/apps/wiiflow/boot.dol"
install -m644 wii/apps/wiiflow/meta.xml "$STAGE/apps/wiiflow/meta.xml"
install -m644 wii/apps/wiiflow/icon.png "$STAGE/apps/wiiflow/icon.png"
mkdir -p "$STAGE/apps/wiiflow/bins" "$STAGE/apps/wiiflow/imgs" "$STAGE/apps/wiiflow/wait_imgs"
install -m644 out/bins/*.bin            "$STAGE/apps/wiiflow/bins/"
install -m644 out/imgs/*                "$STAGE/apps/wiiflow/imgs/"
# only read when launched from the Homebrew Channel, which passes waitdir=;
# the forwarder channel uses the frames compiled into the dol
install -m644 data/images/wait_0*.png   "$STAGE/apps/wiiflow/wait_imgs/"

# --- SD data ---------------------------------------------------------------
mkdir -p "$STAGE/wiiflow/themes_lite/coverflows"
install -m644 wii/wiiflow/themes_lite/default.ini            "$STAGE/wiiflow/themes_lite/default.ini"
install -m644 wii/wiiflow/themes_lite/coverflows/default.ini "$STAGE/wiiflow/themes_lite/coverflows/default.ini"

mkdir -p "$STAGE/wiiflow/languages"
install -m644 wii/wiiflow/Languages/* "$STAGE/wiiflow/languages/" 2>/dev/null || true
for d in help settings; do
	if [ -d "wii/wiiflow/$d" ]; then
		mkdir -p "$STAGE/wiiflow/$d"
		find "wii/wiiflow/$d" -maxdepth 1 -type f -exec install -m644 {} "$STAGE/wiiflow/$d/" \;
	fi
done
# directories WiiFlow writes into; ship them so a fresh card has somewhere to go
for d in covers boxcovers cache snapshots screenshots music fanart; do
	mkdir -p "$STAGE/wiiflow/$d"
	: > "$STAGE/wiiflow/$d/.keep"
done
# where games go, matching the shipped wii_games_dir / gc_games_dir
mkdir -p "$STAGE/wbfs" "$STAGE/games"
: > "$STAGE/wbfs/.keep"
: > "$STAGE/games/.keep"

# --- channel ---------------------------------------------------------------
if [ -f forwarder/WiiFlow_Kids_Channel.wad ]; then
	mkdir -p "$STAGE/wad"
	install -m644 forwarder/WiiFlow_Kids_Channel.wad "$STAGE/wad/WiiFlow_Kids_Channel.wad"
fi

install -m644 docs/RELEASE_README.txt "$STAGE/README.txt"

rm -f "release/${NAME}.zip"
( cd release && zip -qr "${NAME}.zip" "${NAME}" )
echo "release/${NAME}.zip"
du -h "release/${NAME}.zip" | cut -f1
