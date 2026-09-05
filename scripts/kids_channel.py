#!/usr/bin/env python3
"""Kids channel artwork: one Frutiger Aero scene, sliced into the existing panes.

The Wii Menu layout (brlyt/brlan) is not rewritten. The Sports-base ticker
and USB/SD leftovers go away because those textures become fully transparent
and the background pane is stretched to fill the banner. The 496x169 logo
pane carries the actual scene plus the WiiFlow KIDS wordmark.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "forwarder"
ART = OUT / "art"
FONT = ROOT / "out" / "imgs" / "font.ttf"

NAVY = (18, 44, 78)
GOLD = (255, 214, 64)
WHITE = (255, 255, 255)


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))


def cover(im: Image.Image, size) -> Image.Image:
    """Scale-and-crop to fill size, centre-weighted."""
    tw, th = size
    im = im.convert("RGBA")
    sw, sh = im.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(sw * scale + 0.5), int(sh * scale + 0.5)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (nw - tw) // 2
    y = max(0, (nh - th) // 2 - nh // 20)  # a touch toward the sky/dolphins
    return im.crop((x, y, x + tw, y + th))


def band(im: Image.Image, y0_frac, y1_frac, size) -> Image.Image:
    """Horizontal slice of a scene, scaled to size, opaque."""
    im = im.convert("RGBA")
    w, h = im.size
    y0, y1 = int(h * y0_frac), int(h * y1_frac)
    y1 = max(y1, y0 + 1)
    strip = im.crop((0, y0, w, y1))
    return strip.resize(size, Image.Resampling.LANCZOS)


def vstrip(im: Image.Image, size) -> Image.Image:
    """1-pixel-wide (then widened) vertical colour sample of a scene."""
    tw, th = size
    im = im.convert("RGB").resize((1, th), Image.Resampling.LANCZOS)
    return im.resize((tw, th), Image.Resampling.NEAREST).convert("RGBA")


def wordmark_on(scene: Image.Image, scale=0.28, y_frac=0.42):
    """Draw WiiFlow KIDS onto a scene. Text only — the scene is the art."""
    w, h = scene.size
    s = 4
    sw, sh = w * s, h * s
    big = scene.resize((sw, sh), Image.Resampling.LANCZOS)
    font = ImageFont.truetype(str(FONT), int(sh * scale))
    dprobe = ImageDraw.Draw(big)
    left, right = "WiiFlow", "KIDS"
    gap = sh * 0.06
    lw = dprobe.textlength(left, font=font)
    rw = dprobe.textlength(right, font=font)
    x = (sw - (lw + gap + rw)) / 2
    y = sh * y_frac

    shadow = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    ds = ImageDraw.Draw(shadow)
    sx = x
    for text, tw in ((left, lw), (right, rw)):
        ds.text((sx, y + sh * 0.02), text, font=font, fill=(*NAVY, 160), anchor="lm")
        sx += tw + gap
    big.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(sh * 0.016)))

    d = ImageDraw.Draw(big)
    for text, tw, fill in ((left, lw, WHITE), (right, rw, GOLD)):
        d.text((x, y), text, font=font, fill=(*fill, 255), anchor="lm")
        x += tw + gap
    return big.resize((w, h), Image.Resampling.LANCZOS)


def empty(size):
    return Image.new("RGBA", size, (0, 0, 0, 0))


def main():
    scene = Image.open(ART / "scene.jpg")

    banner_logo = wordmark_on(cover(scene, (496, 169)), scale=0.30, y_frac=0.38)
    icon_logo = wordmark_on(cover(scene, (120, 48)), scale=0.34, y_frac=0.50)

    assets = {
        "banner_logo.png": banner_logo,
        "menubnr_logo.png": icon_logo,
        # sky-to-water only — the coral at the bottom of the scene would
        # otherwise paint a pink band around the logo pane.
        "banner_BG.png": vstrip(scene.crop((0, 0, scene.size[0], int(scene.size[1] * 0.62))), (4, 347)),
        "menubnr_BG.png": vstrip(scene.crop((0, 0, scene.size[0], int(scene.size[1] * 0.62))), (2, 96)),
        # tickers used to be black bars of scrolling text. Fully transparent
        # so the stretched sky/ocean background shows through instead.
        "banner_sil_res.png": empty((614, 48)),
        "banner_sil_spo.png": empty((614, 48)),
        "menubnr_sil_res.png": empty((116, 32)),
        "menubnr_sil_spo.png": empty((120, 32)),
        # SD / Wii leftovers from the Sports-base forwarder
        "banner_Nintendo.png": empty((108, 40)),
        "banner_Dolby.png": empty((96, 40)),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    for name, img in assets.items():
        path = OUT / name
        img.save(path, optimize=True)
        print("wrote", path, img.size)


if __name__ == "__main__":
    main()
