WiiFlow Kids
============

A fork of WiiFlow Lite stripped down to one screen a young child can use on
their own. Every Wii and GameCube game appears together in a single coverflow.
Point at a game, press A, then press PLAY. That is the whole interface.

This is an opinionated build. It ships with the settings and artwork it was
designed around rather than with WiiFlow's defaults, and there is no settings
UI to wander into.


Installing
----------

1. Copy the "apps" and "wiiflow" folders to the root of your SD card. If you
   already run WiiFlow, back up your existing sd:/wiiflow first — the theme
   files in here will replace yours.

2. Put your games in:

       sd:/wbfs/<Title> [ID6]/<ID6>.wbfs      Wii
       sd:/games/<Title> [ID6]/game.ciso      GameCube

   Split Wii games (.wbfs + .wbf1) are fine. GameCube titles are launched
   through Nintendont, which you need to install separately.

3. Cover art is optional but this is what it is built for:

       sd:/wiiflow/covers/<ID6>.png       flat cover,  160x224
       sd:/wiiflow/boxcovers/<ID6>.png    full box,   1024x680

   Both are on GameTDB, under the "wii" path for GameCube discs too:

       https://art.gametdb.com/wii/cover/US/<ID6>.png
       https://art.gametdb.com/wii/coverfullHQ/US/<ID6>.png

4. Launch it from the Homebrew Channel, or install wad/WiiFlow_Kids_Channel.wad
   with a WAD manager to get a Wii Menu channel. The channel is a forwarder: it
   boots sd:/apps/wiiflow/boot.dol, so updating this build later is just a
   matter of replacing that file. You do not have to reinstall the channel.


What is opinionated about it
----------------------------

- Games return to WiiFlow, not the Wii Menu. Pressing HOME in a game and
  choosing "Wii Menu" comes back here. This is the returnto setting, and it
  defaults to UP2E — the title ID of the channel in wad/. If you do not install
  the channel, set returnto= (empty) in wiiflow.ini or that exit will not find
  anything to return to.

- No menus. Source, settings, categories, favorites, delete, downloads, WAD
  manager, NAND emulation and disc dumping are removed from the build, not
  hidden. HOME exits.

- The theme is fixed: a 640x480 background, glass capsule buttons, round arrow
  buttons, deep navy type on the sky, and the boot splash. All of it is
  compiled into boot.dol, so the app looks right even if apps/wiiflow/imgs
  never makes it onto the card.

- Type is set a few points larger than stock WiiFlow throughout. It is meant to
  be read from a couch by a child, not from a desk.


Changing things
---------------

There is no settings screen; edit the ini files by hand.

  sd:/apps/wiiflow/wiiflow_lite.ini
      Main config. Written on exit, so edit it with WiiFlow closed.

  sd:/wiiflow/themes_lite/default.ini
      Text colours and font sizes.

  sd:/wiiflow/themes_lite/coverflows/default.ini
      Cover layout — positions, angles, spacing, and the six view modes the
      1 and 2 buttons cycle through.

Anything you put in those files overrides the copy compiled into the dol. Delete
a file and the built-in version takes over again, so you cannot lock yourself
out by breaking one.

USB is not configured out of the box. WiiFlow decides on first boot: with no USB
drive attached it runs SD-only, and with one attached it will look there too.


Credits
-------

WiiFlow Lite by Fledge68, which is itself built on WiiFlow by the original
authors. The channel forwarder is wyndchyme/wiiflow-forwarder (Apache-2.0),
retextured here. Cover art comes from GameTDB. The bundled typeface is Open
Sans (Apache-2.0).
