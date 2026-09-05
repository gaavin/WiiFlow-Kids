#!/usr/bin/env python3
"""Kids UI coverflow background: Frutiger Aero sky-and-grass.

Rendered at 4x supersample then blurred/downsampled to the native 200x148,
so the final PNG is inherently soft — it's stretched full-screen behind the
coverflow and must not compete with the covers (same brief as the original
indigo gradient this replaces).
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parents[1] / "out" / "imgs"
W, H = 200, 148
S = 4  # supersample factor
SW, SH = W * S, H * S


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))


def sky_gradient() -> Image.Image:
    img = Image.new("RGB", (SW, SH))
    px = img.load()
    top = (58, 168, 236)
    mid = (118, 206, 246)
    horizon = (214, 241, 236)
    for y in range(SH):
        t = y / (SH - 1)
        if t < 0.55:
            c = lerp(top, mid, t / 0.55)
        else:
            c = lerp(mid, horizon, (t - 0.55) / 0.45)
        for x in range(SW):
            px[x, y] = tuple(int(v) for v in c)
    return img


def add_radial_glow(img: Image.Image, cx, cy, r, color, peak_alpha):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    steps = 40
    for i in range(steps, 0, -1):
        frac = i / steps
        a = int(peak_alpha * (1 - frac) ** 2)
        rr = r * frac
        d.ellipse(
            [cx - rr, cy - rr, cx + rr, cy + rr],
            fill=(*color, a),
        )
    img.alpha_composite(layer)


def add_bubble(img: Image.Image, cx, cy, r, color, alpha, rim_alpha):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*color, alpha))
    # glassy highlight, upper-left of the bubble
    hr = r * 0.42
    hx, hy = cx - r * 0.32, cy - r * 0.38
    d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=(255, 255, 255, rim_alpha))
    img.alpha_composite(layer)


def add_sparkle(img: Image.Image, cx, cy, r, alpha=230):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # four-point flare: long thin diamond + short crossbar
    d.polygon(
        [(cx, cy - r), (cx + r * 0.16, cy), (cx, cy + r), (cx - r * 0.16, cy)],
        fill=(255, 255, 255, alpha),
    )
    d.polygon(
        [(cx - r * 0.42, cy), (cx, cy - r * 0.16), (cx + r * 0.42, cy), (cx, cy + r * 0.16)],
        fill=(255, 255, 255, alpha),
    )
    img.alpha_composite(layer)
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dg = ImageDraw.Draw(glow)
    dg.ellipse([cx - r * 0.9, cy - r * 0.9, cx + r * 0.9, cy + r * 0.9], fill=(255, 255, 255, alpha // 4))
    glow = glow.filter(ImageFilter.GaussianBlur(r * 0.3))
    img.alpha_composite(glow)


def rotate(p, angle, origin):
    ox, oy = origin
    px, py = p
    c, s = math.cos(angle), math.sin(angle)
    return (ox + c * (px - ox) - s * (py - oy), oy + s * (px - ox) + c * (py - oy))


DOLPHIN_BODY = [
    (1.00, -0.02), (0.93, -0.13), (0.65, -0.27), (0.25, -0.32),
    (-0.10, -0.27), (-0.35, -0.16), (-0.50, -0.08),
    (-0.60, -0.30), (-1.10, -0.34), (-0.62, 0.00), (-1.10, 0.38),
    (-0.60, 0.14), (-0.48, 0.16), (-0.30, 0.26), (0.05, 0.33),
    (0.40, 0.28), (0.68, 0.16), (0.90, 0.05),
]
DOLPHIN_BELLY = [
    (0.68, 0.10), (0.40, 0.24), (0.05, 0.29), (-0.28, 0.22),
    (-0.48, 0.12), (-0.20, 0.10), (0.25, 0.08),
]
DORSAL_FIN = [(0.32, -0.30), (0.06, -0.60), (-0.05, -0.45), (0.06, -0.30)]
PECTORAL_FIN = [(0.30, 0.20), (0.12, 0.46), (0.42, 0.28)]


def add_dolphin(img: Image.Image, cx, cy, size, angle_deg, back, belly, gloss):
    angle = math.radians(angle_deg)
    origin = (cx, cy)

    def xf(poly):
        return [rotate((cx + x * size, cy + y * size), angle, origin) for x, y in poly]

    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.polygon(xf(DOLPHIN_BODY), fill=(*back, 235))
    d.polygon(xf(DORSAL_FIN), fill=(*back, 235))
    d.polygon(xf(PECTORAL_FIN), fill=(*back, 210))
    d.polygon(xf(DOLPHIN_BELLY), fill=(*belly, 220))

    # glossy specular streak along the back
    back_line = [(-0.45, -0.10), (0.05, -0.28), (0.55, -0.20), (0.85, -0.10)]
    pts = xf(back_line)
    d.line(pts, fill=(*gloss, 200), width=max(1, int(size * 0.05)))

    # eye
    eye = rotate((cx + 0.78 * size, cy - 0.10 * size), angle, origin)
    er = size * 0.035
    d.ellipse([eye[0] - er, eye[1] - er, eye[0] + er, eye[1] + er], fill=(30, 40, 55, 230))

    img.alpha_composite(layer)


def add_splash(img: Image.Image, cx, cy):
    for dx, dy, r, a in [
        (-0.9, 0.15, 0.10, 90), (-0.5, 0.30, 0.16, 100), (0.1, 0.35, 0.13, 90),
        (0.6, 0.22, 0.09, 85), (-1.3, 0.05, 0.06, 80), (0.95, 0.1, 0.06, 80),
    ]:
        add_bubble(img, cx + dx * SH * 0.16, cy + dy * SH * 0.16, SH * r * 0.5,
                   (255, 255, 255), a, min(255, a + 60))


def grass_hill(img: Image.Image):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    base_y = SH * 0.90
    amp = SH * 0.045
    pts = [(0, SH)]
    steps = 24
    for i in range(steps + 1):
        x = SW * i / steps
        y = base_y + amp * math.sin(i / steps * math.pi * 1.6 + 0.6) - amp * 0.3
        pts.append((x, y))
    pts.append((SW, SH))
    top = (96, 196, 108)
    d.polygon(pts, fill=(*top, 235))
    img.alpha_composite(layer)

    # darker shadow band along the very bottom for depth
    layer2 = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d2 = ImageDraw.Draw(layer2)
    d2.rectangle([0, SH * 0.97, SW, SH], fill=(46, 138, 72, 160))
    img.alpha_composite(layer2)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    base = sky_gradient().convert("RGBA")

    # sun glow, upper-left — warm and soft
    add_radial_glow(base, SW * 0.20, SH * 0.16, SH * 0.55, (255, 250, 214), 120)
    # secondary cool glow, upper-right
    add_radial_glow(base, SW * 0.86, SH * 0.10, SH * 0.42, (200, 246, 255), 90)

    # floating glossy bubbles, Frutiger Aero style — a fuller rainbow, still soft/pastel
    add_bubble(base, SW * 0.14, SH * 0.66, SH * 0.16, (255, 255, 255), 70, 130)
    add_bubble(base, SW * 0.34, SH * 0.40, SH * 0.10, (150, 235, 255), 60, 120)
    add_bubble(base, SW * 0.62, SH * 0.28, SH * 0.13, (255, 255, 255), 55, 110)
    add_bubble(base, SW * 0.80, SH * 0.58, SH * 0.09, (170, 255, 200), 60, 120)
    add_bubble(base, SW * 0.92, SH * 0.34, SH * 0.06, (255, 255, 255), 65, 130)
    add_bubble(base, SW * 0.06, SH * 0.30, SH * 0.055, (255, 255, 255), 60, 120)
    add_bubble(base, SW * 0.46, SH * 0.14, SH * 0.075, (255, 200, 235), 55, 115)
    add_bubble(base, SW * 0.24, SH * 0.80, SH * 0.07, (255, 225, 150), 55, 115)
    add_bubble(base, SW * 0.70, SH * 0.78, SH * 0.055, (215, 180, 255), 55, 115)
    add_bubble(base, SW * 0.55, SH * 0.55, SH * 0.045, (255, 255, 255), 55, 110)
    add_bubble(base, SW * 0.03, SH * 0.55, SH * 0.04, (170, 255, 230), 55, 110)

    # aero sparkle glints
    add_sparkle(base, SW * 0.40, SH * 0.10, SH * 0.05)
    add_sparkle(base, SW * 0.90, SH * 0.48, SH * 0.045)
    add_sparkle(base, SW * 0.10, SH * 0.12, SH * 0.04)

    # leaping dolphin, breaching from the hill toward the upper-left
    add_splash(base, SW * 0.83, SH * 0.86)
    add_dolphin(
        base, SW * 0.72, SH * 0.58, SH * 0.48, -34,
        back=(84, 138, 176), belly=(220, 238, 240), gloss=(255, 255, 255),
    )

    grass_hill(base)

    base = base.convert("RGB")
    base = base.filter(ImageFilter.GaussianBlur(radius=S * 1.6))
    final = base.resize((W, H), Image.Resampling.LANCZOS)
    final.save(OUT / "background.png", optimize=True)
    print("wrote", OUT / "background.png")


if __name__ == "__main__":
    main()
