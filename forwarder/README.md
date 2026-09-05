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

`tools/` rebuilds the channel from the upstream release WAD. Only two RGBA8
textures and the IMET channel name change; `banner.brlyt`, `banner_Start.brlan`,
`banner_Loop.brlan`, `icon.brlyt`, `icon.brlan` and `sound.bin` are carried over
byte-for-byte, so nothing the System Menu parses structurally was authored here.

    u8.py         U8 archive reader
    lz.py         Nintendo LZ10 codec (round-trip asserted before use)
    tpl.py        TPL RGBA8 tiled codec
    build_wad.py  retexture -> recompress -> IMD5 -> U8 -> IMET
    pack.py       encrypt, fake-sign the TMD, pack, then verify its own output

Fetch `WiiFlow.Channel.Forwarder.wad` from the upstream releases page as
`base.wad`, then run `build_wad.py` followed by `pack.py`.

### Format notes worth keeping

Verified against the real file rather than taken from documentation:

- The **IMET MD5 covers `[0x00,0x600)`** with the 16-byte field at `0x5F0`
  zeroed - not the `[0x40,0x640)` range usually quoted. Using the documented
  range produces a wrong hash.
- The TPL codec was validated by re-encoding upstream's own source PNGs and
  getting **byte-identical** TPLs back, so the encoder matches whatever tool
  built the originals.
- The banner already ships **animation and sound**: `banner_Start.brlan`,
  `banner_Loop.brlan` and a 222,680-byte BNS `sound.bin`.

### Corrections to the community documentation

- Title ID is **`UP2E`** (`00010001-55503245`), **not `DWFA`**. It is in the
  homebrew-channel range so it is safe to install, but WiiFlow's
  `[GENERAL] returnto=DWFA` will not match this channel.
- It requires **IOS35**, not IOS58.
- Upstream's Chinese IMET name slot reads "Wii Sports + Resort", a leftover from
  the CustomizeMii base. All ten slots now read "WiiFlow Kids".
