# WiiFlow Kids channel forwarder artwork

Kids-themed replacements for the banner and icon of the
[wyndchyme/wiiflow-forwarder](https://github.com/wyndchyme/wiiflow-forwarder)
Wii Menu channel (Apache-2.0), title ID `UP2E`.

`scripts/kids_channel.py` paints a Frutiger Aero dolphin/rainbow scene into
the 496x169 logo pane (and the 120x48 icon pane), samples a sky-to-water
gradient for the background strip, and makes the old ticker / SD / Wii
textures fully transparent. `rebuild_channel.py` also stretches the banner
background pane to the full 608x456 so those tickers no longer sit on
black. Animation, sound and the DOL are never rewritten.

| file                   | size    | replaces                         |
|------------------------|---------|----------------------------------|
| `banner_logo.png`      | 496x169 | `banner/banner_logo.tpl`         |
| `menubnr_logo.png`     | 120x48  | `icon/menubnr_logo.tpl`          |
| `banner_BG.png`        | 4x347   | `banner/banner_BG.tpl`           |
| `menubnr_BG.png`       | 2x96    | `icon/menubnr_BG.tpl`            |
| `banner_sil_res.png`   | 614x48  | `banner/banner_sil_res.tpl`      |
| `banner_sil_spo.png`   | 614x48  | `banner/banner_sil_spo.tpl`      |
| `menubnr_sil_res.png`  | 116x32  | `icon/menubnr_sil_res.tpl`       |
| `menubnr_sil_spo.png`  | 120x32  | `icon/menubnr_sil_spo.tpl`       |

## Deliberately NOT changed

`banner.brlyt`, `banner_Start.brlan` and `banner_Loop.brlan` are untouched. The
Wii System Menu parses every installed channel's `opening.bnr` at boot, so a
malformed layout is a "banner brick" - it can stop the System Menu loading.
Retexturing is safe; rewriting the layout blind, with no way to test before it
reaches the console, is not.

## Not possible from this repo alone

- **Icon layout**: the upstream repo ships icon PNGs but no `icon.brlyt` /
  `.brlan`, so `icon.bin` cannot be rebuilt from source - it only exists inside
  the released WAD.
- **Sound**: the forwarder has no `sound.bin`; its banner is silent. Adding one
  means authoring a BNS stream and new U8/IMET structure.
- **Video**: Wii banners have no video track. Motion comes from the `.brlan`
  animations, which already exist here.
- **Build tooling**: upstream built the WAD with CustomizeMii Mod (Windows GUI)
  and the DOL with ModMii. There is no local pipeline in the repo.

The safe way to apply these is to swap the two textures inside the released WAD
and re-sign it, leaving every other structure as shipped.

## Rebuilding the Kids WAD

`tools/` rebuilds the channel from the WAD already in this directory. Run:

    python3 tools/make_art.py        # all eight banner/icon textures
    python3 tools/make_music.py      # sound.bin, an original BNS
    python3 tools/rebuild_channel.py # retexture, repack, re-sign, verify

    u8.py, lz.py, tpl.py   U8 / LZ10 / TPL codecs
    dspadpcm.py            DSP-ADPCM, verified by decoding its own output
    make_art.py            draws every texture
    make_music.py          composes the jingle and wraps it as BNS
    rebuild_channel.py     rebuilds the archives, packs and checks the WAD
    build_wad.py, pack.py  the original base.wad path, kept for reference

`banner.brlyt`, `banner_Start.brlan`, `banner_Loop.brlan`, `icon.brlyt` and
`icon.brlan` are carried through byte-for-byte and the rebuild asserts it, so
the System Menu only ever parses structures it has already booted. Nothing
here authors a layout.

### Why the channel looked like a cropped image

`banner_BG.tpl` shipped as **4x347** and `menubnr_BG.tpl` as **2x96** — single
columns of gradient stretched across panes that are 608x456 and 170x96. Only
the 496x169 logo carried any real picture, so it read as a rectangle pasted on
a flat wash. `rebuild_channel.py` rebuilds the inner U8 rather than patching
pixels in place, which is what allows a texture to change size; the
backgrounds are now 304x228 and 170x96, dithered before the RGB565 encode
because a 5-6-5 sky bands visibly on a TV.

### Where the animation was

It was never missing. `banner_Loop.brlan` scrolls `N_sil_tra_00` and
`N_sil_tra_01` across 2000 frames, and each carries three 614x48 strips laid
end to end at -614/0/+614 so a seamless band scrolls forever. Blanking those
strips to remove the black tickers left the motion running over nothing.
Drawing into them brings it back with no layout change at all.

The strips are IA8/IA4 — intensity and alpha only — and the layout tints them
per material: `P_sil_*_00` pale cyan (192,240,255), `P_sil_c_01/04/05` grey
(194,194,194). So the lower band carries bubbles, fish and dolphins underwater
and the upper band carries clouds, each matched to the tint it is given. Every
element is stamped at x-w, x and x+w so it tiles at the strip width.

### Format notes worth keeping

Verified against the real file rather than taken from documentation:

- The **IMET MD5 covers `[0x00,0x600)`** with the 16-byte field at `0x5F0`
  zeroed - not the `[0x40,0x640)` range usually quoted.
- The TPL codec was validated by re-encoding upstream's own source PNGs and
  getting **byte-identical** TPLs back.
- The BNS is codec 0 (DSP-ADPCM), stereo, 32kHz, channels stored
  **sequentially** rather than interleaved - chan1 begins at the offset in the
  channel table, not at every other frame. ADPCM info is 48 bytes per channel:
  16 Q11 coefficients then context.

### Corrections to the community documentation

- Title ID is **`UP2E`** (`00010001-55503245`), **not `DWFA`**. It is in the
  homebrew-channel range so it is safe to install, but WiiFlow's
  `[GENERAL] returnto=DWFA` will not match this channel.
- It requires **IOS35**, not IOS58.
- Upstream's Chinese IMET name slot reads "Wii Sports + Resort", a leftover
  from the CustomizeMii base. All ten slots now read "WiiFlow Kids".
