# WiiFlow Kids channel forwarder artwork

Kids-themed replacements for the banner and icon logos of the
[wyndchyme/wiiflow-forwarder](https://github.com/wyndchyme/wiiflow-forwarder)
Wii Menu channel (Apache-2.0), title ID `DWFA`.

| file               | size    | replaces                    |
|--------------------|---------|-----------------------------|
| `banner_logo.png`  | 496x169 | `banner/banner_logo.png`    |
| `menubnr_logo.png` | 120x48  | `icon/menubnr_logo.png`     |

Both are composited onto the original artwork, so the WiiFlow wordmark is the
original pixels rather than a re-creation, and both keep the exact dimensions
the `.brlyt` layout expects.

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
