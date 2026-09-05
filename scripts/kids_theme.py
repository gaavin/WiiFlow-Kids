#!/usr/bin/env python3
"""Kids UI chrome: 9-slice glass capsules and coverflow - / + keys.

Rendered at twice the on-screen size. CButtonsMgr::_drawBtn lays the caps
out as squares of the button's height and stretches the centre strip
between them (gui.cpp), with UVs spanning the whole texture — so texture
resolution is free and a 2x source is simply downsampled by the GPU
instead of being magnified. Same reason the - / + keys are 160px for an
80px slot.

The seam invariant from the first pass still holds: every shading term is
a function of y alone, so the stretched centre strip cannot band against
the rounded caps. The centre is taken from the left cap's own last column
and asserted equal to the right cap's first column.
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parents[1] / "out" / "imgs"

H = 96          # 2x the 48px the button slot used to magnify
CAP = 96
CENTRE_W = 8
R = 46          # capsule radius inside the cap
AA = 4          # supersample for the rounded ends


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def row_rgb(t, top, bot, hi_amt):
    """Capsule shading for a normalised height t. Function of y only."""
    base = lerp(top, bot, t ** 1.08)

    # glass shelf: bright across the upper half, cut at the midline
    gloss = math.exp(-((t - 0.16) ** 2) / (2 * 0.115 ** 2))
    if t > 0.47:
        gloss *= max(0.0, 1.0 - (t - 0.47) / 0.06)
    col = lerp(base, (255, 255, 255), min(1.0, gloss * hi_amt))

    # bounce light along the bottom edge, the other half of the glass read
    bounce = math.exp(-((t - 0.88) ** 2) / (2 * 0.085 ** 2)) * 0.22
    col = lerp(col, (255, 255, 255), bounce)

    # slight darkening just under the shelf so the two halves separate
    shade = math.exp(-((t - 0.56) ** 2) / (2 * 0.10 ** 2)) * 0.13
    return lerp(col, (0, 0, 0), shade)


def cap(top, bot, hi_amt, side):
    """One rounded end, supersampled then reduced for clean edges."""
    n = AA
    big = Image.new("RGBA", (CAP * n, H * n), (0, 0, 0, 0))
    px = big.load()
    r = R * n
    cy = (H * n - 1) / 2
    cx = r if side == "left" else (CAP * n - 1 - r)
    for y in range(H * n):
        t = y / (H * n - 1)
        rgb = row_rgb(t, top, bot, hi_amt)
        for x in range(CAP * n):
            if side == "left":
                inside = x >= cx or (x - cx) ** 2 + (y - cy) ** 2 <= r * r
            else:
                inside = x <= cx or (x - cx) ** 2 + (y - cy) ** 2 <= r * r
            if not inside:
                continue
            col = rgb
            # rim light on the curved edge only; never reaches the seam column
            beyond = (side == "left" and x < cx) or (side == "right" and x > cx)
            if beyond:
                d = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                if d >= r - 2.2 * n:
                    k = (d - (r - 2.2 * n)) / (2.2 * n)
                    col = lerp(col, (255, 255, 255), 0.30 * k) if t < 0.5 else \
                        lerp(col, (0, 0, 0), 0.16 * k)
            px[x, y] = (int(col[0]), int(col[1]), int(col[2]), 255)
    return big.resize((CAP, H), Image.Resampling.LANCZOS)


def centre_from(left):
    col = left.crop((CAP - 1, 0, CAP, H))
    img = Image.new("RGBA", (CENTRE_W, H), (0, 0, 0, 0))
    for x in range(CENTRE_W):
        img.paste(col, (x, 0))
    return img


def assert_seam(left, centre, right):
    lp, cp, rp = left.load(), centre.load(), right.load()
    for y in range(H):
        assert lp[CAP - 1, y] == cp[0, y] == rp[0, y], f"seam mismatch at y={y}"


def wii_mark(is_plus, face, edge, size=160):
    """A round glass button with a minus or plus — the Wii Remote - / +."""
    n = 4
    big = Image.new("RGBA", (size * n, size * n), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    c = size * n / 2
    r = size * n * 0.44

    # drop shadow, then the glass disc
    d.ellipse([c - r, c - r + r * 0.08, c + r, c + r + r * 0.08], fill=(10, 40, 70, 70))
    for i in range(int(r), 0, -1):
        t = 1 - i / r
        col = lerp(face, edge, t ** 0.7)
        d.ellipse([c - i, c - i, c + i, c + i], fill=(*[int(v) for v in col], 255))
    d.ellipse([c - r, c - r, c + r, c + r], outline=(255, 255, 255, 235),
              width=int(r * 0.075))

    # upper glass shelf
    shelf = Image.new("RGBA", big.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(shelf)
    ds.ellipse([c - r * 0.86, c - r * 0.90, c + r * 0.86, c + r * 0.16],
               fill=(255, 255, 255, 120))
    mask = Image.new("L", big.size, 0)
    ImageDraw.Draw(mask).ellipse([c - r, c - r, c + r, c + r], fill=255)
    shelf.putalpha(Image.composite(shelf.getchannel("A"), Image.new("L", big.size, 0), mask))
    big.alpha_composite(shelf.filter(ImageFilter.GaussianBlur(r * 0.05)))

    # minus is a horizontal bar; plus adds the vertical. Fat rounded caps
    # so the mark still reads at 80px from a couch. Both navy outlines are
    # laid down first so the white fill can cover the crossing on a plus.
    bar_w = r * 0.72
    bar_h = r * 0.155
    inset = r * 0.038

    def rounded_bar(horizontal, fill, pad=0.0):
        if horizontal:
            box = [c - bar_w + pad, c - bar_h + pad,
                   c + bar_w - pad, c + bar_h - pad]
        else:
            box = [c - bar_h + pad, c - bar_w + pad,
                   c + bar_h - pad, c + bar_w - pad]
        d.rounded_rectangle(box, radius=max(1.0, bar_h - pad), fill=fill)

    navy, white = (20, 56, 92, 220), (255, 255, 255, 255)
    rounded_bar(True, navy)
    if is_plus:
        rounded_bar(False, navy)
    rounded_bar(True, white, inset)
    if is_plus:
        rounded_bar(False, white, inset)
    return big.resize((size, size), Image.Resampling.LANCZOS)


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    sky_top, sky_bot = (150, 226, 255), (22, 122, 208)
    gold_top, gold_bot = (255, 232, 128), (232, 150, 16)

    for name, (top, bot, hi) in {
        "": (sky_top, sky_bot, 0.62),
        "s": (gold_top, gold_bot, 0.55),
    }.items():
        left = cap(top, bot, hi, "left")
        right = cap(top, bot, hi, "right")
        centre = centre_from(left)
        assert_seam(left, centre, right)
        left.save(OUT / f"but{name}left.png", optimize=True)
        centre.save(OUT / f"but{name}center.png", optimize=True)
        right.save(OUT / f"but{name}right.png", optimize=True)

    wii_mark(False, (168, 234, 255), (28, 132, 214)).save(OUT / "btnprev.png", optimize=True)
    wii_mark(True, (168, 234, 255), (28, 132, 214)).save(OUT / "btnnext.png", optimize=True)
    wii_mark(False, (255, 238, 150), (236, 152, 20)).save(OUT / "btnprevs.png", optimize=True)
    wii_mark(True, (255, 238, 150), (236, 152, 20)).save(OUT / "btnnexts.png", optimize=True)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
