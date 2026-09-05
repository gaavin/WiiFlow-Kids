#!/usr/bin/env python3
"""Kids UI 9-slice capsules and page arrows.

Highlight varies only with y so the 4px centre strip is identical to
column 47 of the left cap (and column 0 of the right cap).
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "out" / "imgs"
H = 48
CAP = 48
CENTRE_W = 4
R = 23  # capsule radius inside 48x48


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def row_rgb(y, top, bot, hi_rgb, hi_amt):
    t = y / (H - 1)
    base = lerp(top, bot, t)
    # glossy band near the top, y-only so every x matches
    peak = math.exp(-((t - 0.18) ** 2) / (2 * 0.07 ** 2))
    hi = hi_amt * peak
    return tuple(min(255, int(base[i] + (hi_rgb[i] - base[i]) * hi)) for i in range(3))


def draw_capsule(top, bot, hi_rgb, hi_amt, side: str) -> Image.Image:
    img = Image.new("RGBA", (CAP, H), (0, 0, 0, 0))
    px = img.load()
    cx = R if side == "left" else (CAP - 1 - R)
    for y in range(H):
        rgb = row_rgb(y, top, bot, hi_rgb, hi_amt)
        for x in range(CAP):
            if side == "left":
                inside = x >= cx or (x - cx) ** 2 + (y - (H - 1) / 2) ** 2 <= R * R
            else:
                inside = x <= cx or (x - cx) ** 2 + (y - (H - 1) / 2) ** 2 <= R * R
            if inside:
                # slight edge darken for a clean rim
                rim = 0.0
                if side == "left" and x < cx:
                    d = math.sqrt((x - cx) ** 2 + (y - (H - 1) / 2) ** 2)
                    if R - 1.6 <= d <= R:
                        rim = (d - (R - 1.6)) / 1.6
                if side == "right" and x > cx:
                    d = math.sqrt((x - cx) ** 2 + (y - (H - 1) / 2) ** 2)
                    if R - 1.6 <= d <= R:
                        rim = (d - (R - 1.6)) / 1.6
                shade = tuple(int(c * (1.0 - 0.22 * rim)) for c in rgb)
                px[x, y] = (*shade, 255)
    return img


def centre_from_left(left: Image.Image) -> Image.Image:
    col = left.crop((CAP - 1, 0, CAP, H))
    img = Image.new("RGBA", (CENTRE_W, H), (0, 0, 0, 0))
    for x in range(CENTRE_W):
        img.paste(col, (x, 0))
    return img


def assert_seam(left: Image.Image, centre: Image.Image, right: Image.Image):
    lp = left.load()
    cp = centre.load()
    rp = right.load()
    for y in range(H):
        assert lp[CAP - 1, y] == cp[0, y] == rp[0, y], f"seam mismatch y={y}"


def arrow(point_right: bool, fill, outline) -> Image.Image:
    img = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
    # supersample
    s = 4
    big = Image.new("RGBA", (80 * s, 80 * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    if point_right:
        tri = [(22 * s, 16 * s), (22 * s, 64 * s), (62 * s, 40 * s)]
    else:
        tri = [(58 * s, 16 * s), (58 * s, 64 * s), (18 * s, 40 * s)]
    d.polygon(tri, fill=fill + (255,), outline=outline + (255,))
    # thicker outline
    d.line(tri + [tri[0]], fill=outline + (255,), width=3 * s)
    return big.resize((80, 80), Image.Resampling.LANCZOS)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # richer sky blue — still light enough for navy text
    blue_top, blue_bot = (86, 196, 255), (32, 132, 214)
    # candy gold selected
    gold_top, gold_bot = (255, 224, 86), (242, 168, 24)
    hi = (255, 255, 255)

    left = draw_capsule(blue_top, blue_bot, hi, 0.45, "left")
    right = draw_capsule(blue_top, blue_bot, hi, 0.45, "right")
    centre = centre_from_left(left)
    assert_seam(left, centre, right)

    sleft = draw_capsule(gold_top, gold_bot, hi, 0.40, "left")
    sright = draw_capsule(gold_top, gold_bot, hi, 0.40, "right")
    scentre = centre_from_left(sleft)
    assert_seam(sleft, scentre, sright)

    left.save(OUT / "butleft.png", optimize=True)
    centre.save(OUT / "butcenter.png", optimize=True)
    right.save(OUT / "butright.png", optimize=True)
    sleft.save(OUT / "butsleft.png", optimize=True)
    scentre.save(OUT / "butscenter.png", optimize=True)
    sright.save(OUT / "butsright.png", optimize=True)

    cyan = (64, 210, 255)
    navy = (18, 32, 56)
    gold = (255, 210, 48)
    arrow(False, cyan, navy).save(OUT / "btnprev.png", optimize=True)
    arrow(True, cyan, navy).save(OUT / "btnnext.png", optimize=True)
    arrow(False, gold, navy).save(OUT / "btnprevs.png", optimize=True)
    arrow(True, gold, navy).save(OUT / "btnnexts.png", optimize=True)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
