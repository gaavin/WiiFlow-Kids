# WiiFlow Kids

A fork of [WiiFlow Lite](https://github.com/Fledge68/WiiFlow_Lite) stripped down
to a single screen a young child can use on their own.

## The whole interface

Point at a game, press **A**, press **PLAY**. That is all of it.

Wii and GameCube games appear together in one coverflow. There is no source
menu, no view switching, no settings, no categories, no favorites, no delete.
Pressing HOME simply exits WiiFlow.

## What was removed

The old WiiFlow UI is gone from the build, not merely hidden. These files were
deleted outright:

    menu_about        menu_config_gc        menu_paths
    menu_categories   menu_config_gc_game   menu_plugin
    menu_cftheme      menu_config_hb        menu_sm_editor
    menu_cheat        menu_config_main      menu_source
    menu_code         menu_config_source    menu_wad
    menu_config_boot  menu_explorer         menu_wbfs
    menu_config_coverbnr  menu_gameinfo     menu_partitions
    menu_config_game  gc_disc_dump (GameCube disc dumping)

Three files were reduced to the non-UI helpers the child's screen still needs,
and renamed to match what they now are:

  - `menu_download.cpp` -> `menu_network.cpp` — network bring-up, plus the
    worker thread and progress bar shown while covers are cached on first boot
  - `menu_home.cpp` -> `menu_covercache.cpp` — cover PNG to `.wfc` conversion
  - `menu_nandemu.cpp` -> `menu_emunand.cpp` — locating the emuNAND partition
    and checking for saves, which booting a game still needs

Also removed: 179 dead method declarations and 102 dead widget members from
`menu.hpp`.

## How the combined list works

`m_current_view` is a bitmask, so pinning it to
`KIDS_VIEW = COVERFLOW_WII | COVERFLOW_GAMECUBE` (see `source/types.h`) makes
`_loadGameList()` load both lists into one coverflow. `_launch()` re-derives the
storage partition from each game's own `hdr->type` before booting, so a mixed
list boots correctly — the same mechanism upstream's `directlaunch()` relies on.

## Safety rails

Favorites filtering is forced off and category filters are cleared on boot.
The buttons that toggle them no longer exist, so a stale filter would otherwise
strand the child on an empty coverflow with no way to recover. Hidden categories
are deliberately left intact, so a parent can still keep titles out of sight.

## Configuring it

There is no settings UI. Edit `wiiflow.ini` on the SD card by hand, or run a
stock WiiFlow build once to set things up.

## Building

Built by GitHub Actions on every push (`.github/workflows/build.yml`) using the
`devkitpro/devkitppc` image; download `boot.dol` or the ready-to-copy
`apps/wiiflow` folder from the run's artifacts.

Locally: devkitPPC + libogc, then `make` from the repository root. Everything
else (libpng, freetype, wolfSSL, custom fat/ntfs/ext2) is vendored in `portlibs/`
and `source/libwolfssl/`; only `libmad` comes from devkitPro's package repo.

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
