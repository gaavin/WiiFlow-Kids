# WiiFlow Kids

A fork of [WiiFlow Lite](https://github.com/Fledge68/WiiFlow_Lite) with a
deliberately stripped-down interface, meant for a young child to use on their own.

## What is different

**One screen, all the games.** Wii and GameCube games are combined into a single
coverflow. Upstream keeps them in separate views that you switch between with a
button; here `m_current_view` is pinned to `COVERFLOW_WII | COVERFLOW_GAMECUBE`
(`KIDS_VIEW` in `source/types.h`). WiiFlow's game list loader is already a
bitmask, so both lists load together, and `_launch()` picks the right loader per
game from `hdr->type`.

**Two presses to play.** Point at a cover, press A, press PLAY. That is the
entire interface a child sees.

**Stripped from the main screen:** the view-switch button (Wii/GameCube/Channels/
Emulators/Homebrew), categories, favorites, settings, and the DVD boot button.
The source menu and sourceflow are gone entirely, including the B-held shortcut
that opened them. Only HOME and the page arrows remain.

**Stripped from the game screen:** favorites, categories, settings, delete, and
the banner toggle. Only PLAY and BACK remain, enlarged for small hands.

**Safety rails.** Because the buttons that toggle them are gone, favorites
filtering is forced off and category filters are cleared on boot — otherwise a
stale filter could leave the child looking at an empty screen with no way to fix
it. Hidden categories are deliberately *not* cleared, so a parent can still keep
particular titles out of sight.

## For the parent

The **HOME button still opens the full WiiFlow menu**, so settings, downloads and
per-game configuration all remain available. Whatever you change in there, the
child's screen always returns to the combined Wii + GameCube coverflow.

Channels, emulator plugins and homebrew are excluded from the child's coverflow.
They are not deleted — they are simply not part of `KIDS_VIEW`.

## Building

Needs devkitPPC + libogc, same as upstream. `make` from the repository root.

---

# WiiFlow Lite
My mod of the Wii USB Loader WiiFlow

## Description
WiiFlow Lite is a wii homebrew app used to display and launch your games and apps stored on a USB device or SD card plugged into a Wii or Wii U in Wii mode. The games and apps are displayed in cover flow style display.

## Installing
As of v5.2.0 WiiFlow Lite will simply be a replacement for WiiFlow. Put it in apps/wiiflow and use wiiflow forwarder's to launch it via the wii system menu. forwarders can be found on wiiflowiki4. for previous wiiflow lite users, sorry but you must uninstall your wiiflow lite forwarder and replace it with a wiiflow forwarder.

Simply download the latest release and extract it to your apps/wiiflow folder on SD or USB HDD. SD is recommended. Your device should be formatted to FAT32.

## Booting
To start WiiFlow Lite you will need the Homebrew Channel or a WiiFlow forwarder channel installed on your Wii or vWii system menu.

## Themes
Currently only Rhapsodii and Rhapsodii Shima themes are compatible with WiiFlow Lite. Other older wiiflow themes need to be updated to work properly with WFL.

Rhapsodii made by Hakaisha is a new theme designed for wiiflow lite. find it here - (https://gbatemp.net/threads/wiiflow-lite-theme-rhapsodii.511833/)

Other wiiflow lite themes can be found on the wiki linked below. but they need to be updated to properly work with wiiflow lite.

## Useful Links
[WiiFlow Lite GBATemp thread](https://gbatemp.net/threads/wiiflow-lite.422685/)

[WiiFlow Wiki](https://web.archive.org/web/20220414124727/https://sites.google.com/site/wiiflowiki4/)

[Newer Wiki WIP](https://sites.google.com/view/wiiflow-wiki/welcome)

[Github Wiki](https://github.com/Fledge68/WiiFlow_Lite/wiki)

[Old Sourceforge Project Repository](https://sourceforge.net/projects/wiiflow-lite/)
