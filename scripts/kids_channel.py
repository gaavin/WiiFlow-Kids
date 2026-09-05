#!/usr/bin/env python3
"""Kids channel artwork: Frutiger Aero sky, glass wordmark, kid-friendly lines.

Replaces the Sports-base / USB-loader textures in the Wii Menu forwarder
with the same glass-and-sky language as the in-app theme. Sizes are the
exact TPL dimensions the existing .brlyt panes expect — the layout and
animation files are never touched.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "forwarder"
FONT = ROOT / "out" / "imgs" / "font.ttf"

NAVY = (18, 44, 78)
GOLD = (255, 214, 64)
WHITE = (255, 255, 255)


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))


def vgrad(size, stops):
    w, h = size
    strip = Image.new("RGB", (1, 256))
    px = strip.load()
    for y in range(256):
        t = y / 255
        col = stops[-1][1]
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                col = lerp(c0, c1, 0 if p1 == p0 else (t - p0) / (p1 - p0))
                break
        px[0, y] = tuple(int(v) for v in col)
    return strip.resize((w, h), Image.Resampling.BICUBIC)


SKY = [
    (0.00, (210, 242, 255)),
    (0.28, (140, 214, 252)),
    (0.52, (64, 176, 236)),
    (0.72, (28, 142, 216)),
    (1.00, (18, 108, 186)),
]


def sky_strip(w, h):
    return vgrad((w, h), SKY).convert("RGBA")


def glass_capsule(img, box, radius):
    """Frutiger Aero pill: sky wash, upper shelf, white rim."""
    x0, y0, x1, y1 = box
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle(box, radius=radius, fill=255)
    wash = vgrad((w, h), [
        (0.00, (230, 248, 255)), (0.35, (160, 220, 250)),
        (0.52, (80, 180, 236)), (1.00, (36, 140, 214)),
    ])
    body = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    body.paste(wash, (0, 0))
    body.putalpha(mask)
    img.alpha_composite(body)
    shelf = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(shelf).rounded_rectangle(
        [x0 + h * 0.04, y0 + h * 0.05, x1 - h * 0.04, (y0 + y1) * 0.48],
        radius=radius * 0.7, fill=(255, 255, 255, 110))
    shelf.putalpha(Image.composite(shelf.getchannel("A"), Image.new("L", (w, h), 0), mask))
    img.alpha_composite(shelf.filter(ImageFilter.GaussianBlur(h * 0.012)))
    rim = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(rim).rounded_rectangle(box, radius=radius, outline=(255, 255, 255, 230),
                                          width=max(2, int(h * 0.025)))
    img.alpha_composite(rim)


def wordmark(size, left="WiiFlow", right="KIDS", scale=0.42, gap_frac=0.07, capsule=False):
    """Glass wordmark on a transparent field, authored oversized then reduced."""
    w, h = size
    s = 4
    sw, sh = w * s, h * s
    img = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    if capsule:
        pad_x, pad_y = sw * 0.04, sh * 0.10
        glass_capsule(img, (pad_x, pad_y, sw - pad_x, sh - pad_y), sh * 0.38)
    font = ImageFont.truetype(str(FONT), int(sh * scale))
    d = ImageDraw.Draw(img)
    gap = sh * gap_frac
    lw = d.textlength(left, font=font)
    rw = d.textlength(right, font=font)
    x = (sw - (lw + gap + rw)) / 2
    y = sh * 0.50

    # soft contact shadow so the type sits on the sky rather than floating
    shadow = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    ds = ImageDraw.Draw(shadow)
    sx = x
    for text, tw in ((left, lw), (right, rw)):
        ds.text((sx, y + sh * 0.03), text, font=font, fill=(*NAVY, 140), anchor="lm")
        sx += tw + gap
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(sh * 0.018)))

    d = ImageDraw.Draw(img)
    for text, tw, fill in ((left, lw, WHITE), (right, rw, GOLD)):
        d.text((x, y), text, font=font, fill=(*fill, 255), anchor="lm")
        x += tw + gap

    # glass sheen across the upper half of the letters
    shine = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    ImageDraw.Draw(shine).rectangle([0, sh * 0.22, sw, sh * 0.46], fill=(255, 255, 255, 50))
    alpha = img.getchannel("A")
    shine.putalpha(Image.composite(shine.getchannel("A"), Image.new("L", (sw, sh), 0), alpha))
    img.alpha_composite(shine.filter(ImageFilter.GaussianBlur(sh * 0.02)))
    return img.resize((w, h), Image.Resampling.LANCZOS)


def line_strip(size, text, scale=0.46):
    """White glyph, coverage in alpha — no dark fringe on the sky behind it."""
    w, h = size
    s = 4
    sw, sh = w * s, h * s
    ink = Image.new("L", (sw, sh), 0)
    font = ImageFont.truetype(str(FONT), int(sh * scale))
    ImageDraw.Draw(ink).text((sw / 2, sh / 2), text, font=font, fill=255, anchor="mm")
    ink = ink.resize((w, h), Image.Resampling.LANCZOS)
    img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    img.putalpha(ink)
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    assets = {
        "banner_logo.png": wordmark((496, 169), scale=0.36, capsule=True),
        "menubnr_logo.png": wordmark((120, 48), scale=0.40, gap_frac=0.06, capsule=True),
        "banner_BG.png": sky_strip(4, 347),
        "menubnr_BG.png": sky_strip(2, 96),
        "banner_sil_res.png": line_strip((614, 48), "Pick a game and play!"),
        "banner_sil_spo.png": line_strip((614, 48), "Have fun."),
        "menubnr_sil_res.png": line_strip((116, 32), "Let's play!", scale=0.50),
        "menubnr_sil_spo.png": Image.new("RGBA", (120, 32), (0, 0, 0, 0)),
    }
    for name, img in assets.items():
        path = OUT / name
        img.save(path, optimize=True)
        print("wrote", path, img.size)


if __name__ == "__main__":
    main()
