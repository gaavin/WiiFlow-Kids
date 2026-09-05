#!/usr/bin/env python3
"""Kids UI boot splash: eight frames of the WiiFlow KIDS glass card.

CVideo::waitMessage draws the frame 1:1 in pixels, centred on a screen
that has just been cleared to black (widescreen only squeezes it to 0.75
width to survive the TV's stretch). So these are authored at their exact
on-screen size — 420x150 rather than the 200x80 they used to be — and
composed 4x oversized so the reduction anti-aliases them.

Frames are opaque on black: the wait quad blends with GX_BM_NONE, so
whatever is in the texture is written straight to the framebuffer.

The animation is a bubble drift plus a specular sweep across the card.
The wordmark itself never moves — a boot splash that jitters reads as a
fault, not as progress.
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "images"
FONT = ROOT / "out" / "imgs" / "font.ttf"

W, H = 420, 150
S = 4
SW, SH = W * S, H * S
FRAMES = 8

CARD = (SW * 0.045, SH * 0.13, SW * 0.955, SH * 0.87)
RADIUS = SH * 0.30


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


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


def card_mask():
    m = Image.new("L", (SW, SH), 0)
    ImageDraw.Draw(m).rounded_rectangle(CARD, radius=RADIUS, fill=255)
    return m


def glow(img):
    layer = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x0, y0, x1, y1 = CARD
    pad = SH * 0.10
    d.rounded_rectangle([x0 - pad, y0 - pad, x1 + pad, y1 + pad],
                        radius=RADIUS + pad, fill=(64, 190, 255, 130))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(SH * 0.075)))


def card(img):
    mask = card_mask()
    wash = vgrad((SW, SH), [(0.00, (196, 240, 255)), (0.30, (128, 214, 250)),
                            (0.52, (54, 166, 232)), (0.53, (36, 146, 220)),
                            (0.86, (26, 118, 200)), (1.00, (72, 168, 226))])
    body = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    body.paste(wash, (0, 0))
    body.putalpha(mask)
    img.alpha_composite(body)

    # upper glass shelf, cut at the midline
    shelf = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    ds = ImageDraw.Draw(shelf)
    x0, y0, x1, y1 = CARD
    ds.rounded_rectangle([x0 + SH * 0.03, y0 + SH * 0.03, x1 - SH * 0.03, (y0 + y1) / 2],
                         radius=RADIUS * 0.8, fill=(255, 255, 255, 105))
    shelf.putalpha(Image.composite(shelf.getchannel("A"), Image.new("L", (SW, SH), 0), mask))
    img.alpha_composite(shelf.filter(ImageFilter.GaussianBlur(SH * 0.012)))

    rim = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    ImageDraw.Draw(rim).rounded_rectangle(CARD, radius=RADIUS, outline=(255, 255, 255, 225),
                                          width=int(SH * 0.018))
    img.alpha_composite(rim)


def wordmark(img):
    big = ImageFont.truetype(str(FONT), int(SH * 0.30))
    d = ImageDraw.Draw(img)
    left, right = "WiiFlow", "KIDS"
    gap = SH * 0.055
    lw = d.textlength(left, font=big)
    rw = d.textlength(right, font=big)
    x = (SW - (lw + gap + rw)) / 2
    y = SH * 0.50

    for text, w, fill in ((left, lw, (255, 255, 255)), (right, rw, (255, 214, 64))):
        shadow = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).text((x, y + SH * 0.018), text, font=big,
                                    fill=(12, 58, 104, 170), anchor="lm")
        img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(SH * 0.012)))
        d.text((x, y), text, font=big, fill=(*fill, 255), anchor="lm")
        x += w + gap


def bubbles(img, phase):
    mask = card_mask()
    layer = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    spec = [(0.10, 0.055, 0.9), (0.24, 0.038, 1.4), (0.40, 0.030, 1.1),
            (0.58, 0.042, 0.8), (0.72, 0.032, 1.5), (0.88, 0.050, 1.0),
            (0.17, 0.026, 1.7), (0.66, 0.024, 1.25)]
    for i, (fx, fr, speed) in enumerate(spec):
        t = (phase * speed + i * 0.37) % 1.0
        cx = CARD[0] + (CARD[2] - CARD[0]) * fx + math.sin(t * 6.28 + i) * SH * 0.02
        cy = CARD[3] - (CARD[3] - CARD[1]) * t
        r = SH * fr
        a = int(150 * min(1.0, t * 4) * min(1.0, (1 - t) * 4))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, int(a * 0.45)))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255, a),
                  width=max(2, int(r * 0.16)))
        hr = r * 0.34
        d.ellipse([cx - r * 0.36 - hr, cy - r * 0.40 - hr,
                   cx - r * 0.36 + hr, cy - r * 0.40 + hr], fill=(255, 255, 255, a))
    layer.putalpha(Image.composite(layer.getchannel("A"), Image.new("L", (SW, SH), 0), mask))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(SH * 0.005)))


def sweep(img, phase):
    """A specular bar travelling across the card — the progress cue."""
    mask = card_mask()
    layer = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    span = (CARD[2] - CARD[0]) + SH * 1.2
    x = CARD[0] - SH * 0.6 + span * phase
    w = SH * 0.10
    skew = SH * 0.34
    d.polygon([(x, CARD[1] - SH * 0.1), (x + w, CARD[1] - SH * 0.1),
               (x + w - skew, CARD[3] + SH * 0.1), (x - skew, CARD[3] + SH * 0.1)],
              fill=(255, 255, 255, 96))
    d.polygon([(x + w * 1.5, CARD[1] - SH * 0.1), (x + w * 2.1, CARD[1] - SH * 0.1),
               (x + w * 2.1 - skew, CARD[3] + SH * 0.1), (x + w * 1.5 - skew, CARD[3] + SH * 0.1)],
              fill=(255, 255, 255, 58))
    layer.putalpha(Image.composite(layer.getchannel("A"), Image.new("L", (SW, SH), 0), mask))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(SH * 0.022)))


def frame(i):
    phase = i / FRAMES
    img = Image.new("RGBA", (SW, SH), (0, 0, 0, 255))
    glow(img)
    card(img)
    bubbles(img, phase)
    wordmark(img)
    sweep(img, phase)
    return img.convert("RGB").resize((W, H), Image.Resampling.LANCZOS)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for i in range(FRAMES):
        frame(i).save(OUT / f"wait_{i + 1:02d}.png", optimize=True)
    print(f"wrote {FRAMES} frames to {OUT} at {W}x{H}")


if __name__ == "__main__":
    main()
