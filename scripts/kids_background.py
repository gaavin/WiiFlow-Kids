#!/usr/bin/env python3
"""Kids UI coverflow background: Frutiger Aero rainbow-dolphins ocean.

Rendered at 4x supersample then blurred/downsampled to the native 200x148,
so the final PNG is inherently soft — it's stretched full-screen behind the
coverflow and must not compete with the covers (same brief as the original
indigo gradient this replaces). Leans hard into the classic "leaping
dolphins under a rainbow, coral reef below the waterline" Frutiger Aero
wallpaper look rather than a plain sky-and-hill.
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parents[1] / "out" / "imgs"
W, H = 200, 148
S = 4  # supersample factor
SW, SH = W * S, H * S
WATERLINE = SH * 0.80


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))


def sky_gradient() -> Image.Image:
    img = Image.new("RGB", (SW, SH))
    px = img.load()
    top = (18, 140, 224)
    mid = (72, 200, 244)
    horizon = (200, 246, 250)
    for y in range(int(WATERLINE)):
        t = y / WATERLINE
        if t < 0.55:
            c = lerp(top, mid, t / 0.55)
        else:
            c = lerp(mid, horizon, (t - 0.55) / 0.45)
        for x in range(SW):
            px[x, y] = tuple(int(v) for v in c)
    for y in range(int(WATERLINE), SH):
        for x in range(SW):
            px[x, y] = horizon
    return img


def add_radial_glow(img: Image.Image, cx, cy, r, color, peak_alpha):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    steps = 40
    for i in range(steps, 0, -1):
        frac = i / steps
        a = int(peak_alpha * (1 - frac) ** 2)
        rr = r * frac
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(*color, a))
    img.alpha_composite(layer)


def add_rainbow(img: Image.Image):
    cx, cy = SW * 0.5, SH * 1.02
    rx, ry = SW * 0.56, SH * 0.98
    band = SH * 0.028
    colors = [
        (237, 60, 60), (245, 145, 45), (250, 210, 60),
        (95, 200, 100), (60, 150, 235), (140, 100, 220),
    ]
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i, col in enumerate(colors):
        r = i * band
        bbox = [cx - rx + r, cy - ry + r, cx + rx - r, cy + ry - r]
        d.arc(bbox, 182, 358, fill=(*col, 150), width=int(band))
    layer = layer.filter(ImageFilter.GaussianBlur(SH * 0.01))
    img.alpha_composite(layer)


def add_bubble(img: Image.Image, cx, cy, r, color, alpha, rim_alpha):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*color, alpha))
    hr = r * 0.42
    hx, hy = cx - r * 0.32, cy - r * 0.38
    d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=(255, 255, 255, rim_alpha))
    img.alpha_composite(layer)


def add_sparkle(img: Image.Image, cx, cy, r, alpha=230):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.polygon([(cx, cy - r), (cx + r * 0.16, cy), (cx, cy + r), (cx - r * 0.16, cy)], fill=(255, 255, 255, alpha))
    d.polygon([(cx - r * 0.42, cy), (cx, cy - r * 0.16), (cx + r * 0.42, cy), (cx, cy + r * 0.16)], fill=(255, 255, 255, alpha))
    img.alpha_composite(layer)
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dg = ImageDraw.Draw(glow)
    dg.ellipse([cx - r * 0.9, cy - r * 0.9, cx + r * 0.9, cy + r * 0.9], fill=(255, 255, 255, alpha // 4))
    glow = glow.filter(ImageFilter.GaussianBlur(r * 0.3))
    img.alpha_composite(glow)


def add_heart(img: Image.Image, cx, cy, r, alpha=150):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    lr = r * 0.55
    d.ellipse([cx - lr * 1.9, cy - lr * 0.9, cx - lr * 0.1, cy + lr * 0.9], fill=(255, 255, 255, alpha))
    d.ellipse([cx + lr * 0.1, cy - lr * 0.9, cx + lr * 1.9, cy + lr * 0.9], fill=(255, 255, 255, alpha))
    d.polygon([(cx - lr * 1.7, cy + lr * 0.4), (cx + lr * 1.7, cy + lr * 0.4), (cx, cy + lr * 2.3)], fill=(255, 255, 255, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(r * 0.12))
    img.alpha_composite(layer)


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


def add_dolphin(img: Image.Image, cx, cy, size, angle_deg, back, belly, gloss, alpha=235):
    angle = math.radians(angle_deg)
    origin = (cx, cy)

    def xf(poly):
        return [rotate((cx + x * size, cy + y * size), angle, origin) for x, y in poly]

    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.polygon(xf(DOLPHIN_BODY), fill=(*back, alpha))
    d.polygon(xf(DORSAL_FIN), fill=(*back, alpha))
    d.polygon(xf(PECTORAL_FIN), fill=(*back, int(alpha * 0.9)))
    d.polygon(xf(DOLPHIN_BELLY), fill=(*belly, int(alpha * 0.93)))

    back_line = [(-0.45, -0.10), (0.05, -0.28), (0.55, -0.20), (0.85, -0.10)]
    d.line(xf(back_line), fill=(*gloss, int(alpha * 0.85)), width=max(1, int(size * 0.05)))

    eye = rotate((cx + 0.78 * size, cy - 0.10 * size), angle, origin)
    er = size * 0.035
    d.ellipse([eye[0] - er, eye[1] - er, eye[0] + er, eye[1] + er], fill=(30, 40, 55, alpha))

    img.alpha_composite(layer)


def add_splash(img: Image.Image, cx, cy, scale=1.0):
    for dx, dy, r, a in [
        (-0.9, 0.15, 0.10, 90), (-0.5, 0.30, 0.16, 100), (0.1, 0.35, 0.13, 90),
        (0.6, 0.22, 0.09, 85), (-1.3, 0.05, 0.06, 80), (0.95, 0.1, 0.06, 80),
    ]:
        add_bubble(img, cx + dx * SH * 0.16 * scale, cy + dy * SH * 0.16 * scale, SH * r * 0.5 * scale,
                   (255, 255, 255), a, min(255, a + 60))


def add_fish(img: Image.Image, cx, cy, size, angle_deg, color):
    angle = math.radians(angle_deg)
    origin = (cx, cy)

    def xf(poly):
        return [rotate((cx + x * size, cy + y * size), angle, origin) for x, y in poly]

    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    body = [(0.6, 0), (0.2, -0.35), (-0.6, -0.2), (-0.35, 0), (-0.6, 0.2), (0.2, 0.35)]
    tail = [(-0.55, 0), (-0.95, -0.28), (-0.95, 0.28)]
    d.polygon(xf(body), fill=(*color, 220))
    d.polygon(xf(tail), fill=(*color, 220))
    img.alpha_composite(layer)


def underwater(img: Image.Image):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    deep = (6, 60, 110)
    shallow = (10, 130, 150)
    for y in range(int(WATERLINE), SH):
        t = (y - WATERLINE) / (SH - WATERLINE)
        c = lerp(shallow, deep, t)
        d.line([(0, y), (SW, y)], fill=(int(c[0]), int(c[1]), int(c[2]), 235))
    img.alpha_composite(layer)

    # a bright glint right at the surface line
    glint = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dg = ImageDraw.Draw(glint)
    dg.rectangle([0, WATERLINE - SH * 0.006, SW, WATERLINE + SH * 0.01], fill=(220, 250, 255, 130))
    glint = glint.filter(ImageFilter.GaussianBlur(SH * 0.01))
    img.alpha_composite(glint)

    # coral silhouettes along the bottom
    layer2 = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d2 = ImageDraw.Draw(layer2)
    for cx, w, h, col in [
        (SW * 0.08, SW * 0.10, SH * 0.10, (230, 110, 140)),
        (SW * 0.22, SW * 0.07, SH * 0.07, (250, 170, 90)),
        (SW * 0.78, SW * 0.09, SH * 0.09, (200, 120, 210)),
        (SW * 0.92, SW * 0.06, SH * 0.065, (240, 150, 110)),
        (SW * 0.5, SW * 0.08, SH * 0.06, (110, 200, 170)),
    ]:
        d2.ellipse([cx - w / 2, SH - h, cx + w / 2, SH + h * 0.4], fill=(*col, 200))
    img.alpha_composite(layer2)

    # small tropical fish dabs
    add_fish(img, SW * 0.15, SH * 0.90, SH * 0.045, 8, (250, 170, 40))
    add_fish(img, SW * 0.30, SH * 0.94, SH * 0.03, -12, (255, 210, 60))
    add_fish(img, SW * 0.86, SH * 0.90, SH * 0.04, -10, (255, 120, 90))
    add_fish(img, SW * 0.65, SH * 0.95, SH * 0.028, 14, (255, 255, 255))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    base = sky_gradient().convert("RGBA")

    add_radial_glow(base, SW * 0.22, SH * 0.14, SH * 0.55, (255, 250, 214), 130)
    add_rainbow(base)

    # floating glossy bubbles — a fuller rainbow of colour, still soft/pastel
    add_bubble(base, SW * 0.14, SH * 0.60, SH * 0.14, (255, 255, 255), 70, 130)
    add_bubble(base, SW * 0.34, SH * 0.38, SH * 0.09, (150, 235, 255), 60, 120)
    add_bubble(base, SW * 0.06, SH * 0.28, SH * 0.05, (255, 255, 255), 60, 120)
    add_bubble(base, SW * 0.46, SH * 0.12, SH * 0.06, (255, 200, 235), 55, 115)
    add_bubble(base, SW * 0.24, SH * 0.72, SH * 0.06, (255, 225, 150), 55, 115)
    add_bubble(base, SW * 0.03, SH * 0.50, SH * 0.035, (170, 255, 230), 55, 110)

    # aero sparkle glints
    add_sparkle(base, SW * 0.40, SH * 0.09, SH * 0.05)
    add_sparkle(base, SW * 0.14, SH * 0.32, SH * 0.035)
    add_sparkle(base, SW * 0.94, SH * 0.20, SH * 0.04)

    # a leaping pod of dolphins, not just one
    add_splash(base, SW * 0.20, SH * 0.78, 0.55)
    add_dolphin(base, SW * 0.20, SH * 0.60, SH * 0.20, -40,
                back=(90, 145, 182), belly=(224, 240, 242), gloss=(255, 255, 255), alpha=200)

    add_heart(base, SW * 0.53, SH * 0.30, SH * 0.05)
    add_splash(base, SW * 0.86, SH * 0.72, 0.7)
    add_dolphin(base, SW * 0.72, SH * 0.48, SH * 0.46, -36,
                back=(70, 128, 168), belly=(224, 242, 244), gloss=(255, 255, 255))

    add_splash(base, SW * 0.46, SH * 0.68, 0.4)
    add_dolphin(base, SW * 0.44, SH * 0.58, SH * 0.16, -44,
                back=(100, 155, 190), belly=(228, 244, 246), gloss=(255, 255, 255), alpha=180)

    underwater(base)

    base = base.convert("RGB")
    base = base.filter(ImageFilter.GaussianBlur(radius=S * 1.5))
    final = base.resize((W, H), Image.Resampling.LANCZOS)
    final.save(OUT / "background.png", optimize=True)
    print("wrote", OUT / "background.png")


if __name__ == "__main__":
    main()
