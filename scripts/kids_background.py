#!/usr/bin/env python3
"""Kids UI coverflow background: Frutiger Aero reef, sky and dolphins.

Rendered at 640x480 — the Wii's framebuffer — rather than the 200x148 the
stock theme shipped. The background is drawn as one full-screen quad with
0..1 UVs (menu.cpp _drawBg), so texture size is free and a native-res image
is simply sharper. Everything is composed 4x oversized and reduced with
LANCZOS: the downsample does the anti-aliasing, so edges stay crisp. Only
genuinely soft things (glows, clouds, haze, spray) get blurred.

Composition follows where the UI actually sits. The covers own the middle
of the screen and the Play/Back capsules the right, so the busy detail —
dolphins, rainbow, reef — lives left and along the bottom, and the centre
stays calm so covers read against it. Detail is kept clear of the outer
~4% for TV overscan. The rainbow is a short arc rising out of the left
edge, not a full arch across the middle.
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parents[1] / "out" / "imgs"
W, H = 640, 480
S = 4
SW, SH = W * S, H * S

HORIZON = 0.665  # waterline, as a fraction of height
SEABED = 0.930   # where the sand starts


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))


def vgrad(size, stops, mode="RGB"):
    """Vertical gradient from (position, colour) stops, built small and scaled up."""
    w, h = size
    strip = Image.new(mode, (1, 256))
    px = strip.load()
    for y in range(256):
        t = y / 255
        col = stops[-1][1]
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                k = 0 if p1 == p0 else (t - p0) / (p1 - p0)
                col = lerp(c0, c1, k)
                break
        px[0, y] = tuple(int(v) for v in col) if mode != "L" else int(col[0])
    return strip.resize((w, h), Image.Resampling.BICUBIC)


def soft(img, draw_fn, blur, scale=0.5):
    """Draw onto a reduced layer, blur there, composite back. Cheap and smooth."""
    lw, lh = int(SW * scale), int(SH * scale)
    layer = Image.new("RGBA", (lw, lh), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(layer), scale)
    if blur:
        layer = layer.filter(ImageFilter.GaussianBlur(blur * scale))
    img.alpha_composite(layer.resize((SW, SH), Image.Resampling.BICUBIC))


def soft_ellipse(img, cx, cy, rx, ry, colour, alpha, blur):
    def draw(d, k):
        d.ellipse([(cx - rx) * k, (cy - ry) * k, (cx + rx) * k, (cy + ry) * k],
                  fill=(*colour, alpha))
    soft(img, draw, blur)


def radial(img, cx, cy, r, colour, peak, steps=44, falloff=2.0):
    def draw(d, k):
        for i in range(steps, 0, -1):
            f = i / steps
            a = int(peak * (1 - f) ** falloff)
            rr = r * f * k
            d.ellipse([cx * k - rr, cy * k - rr, cx * k + rr, cy * k + rr], fill=(*colour, a))
    soft(img, draw, r * 0.05)


def catmull(points, closed=False, per_seg=14):
    """Catmull-Rom through control points — smooth outlines instead of facets."""
    pts = list(points)
    pts = ([pts[-1]] + pts + [pts[0], pts[1]]) if closed else ([pts[0]] + pts + [pts[-1]])
    out = []
    for i in range(len(pts) - 3):
        p0, p1, p2, p3 = pts[i:i + 4]
        for j in range(per_seg):
            t = j / per_seg
            t2, t3 = t * t, t * t * t
            out.append((
                0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
                       (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                       (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
                0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                       (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3),
            ))
    return out


# ---------------------------------------------------------------- sky


def sky():
    return vgrad((SW, SH), [
        (0.00, (22, 118, 206)),
        (0.26, (58, 168, 232)),
        (0.48, (120, 208, 244)),
        (HORIZON - 0.055, (196, 234, 248)),
        (HORIZON, (222, 244, 250)),
        (1.00, (222, 244, 250)),
    ]).convert("RGBA")


def sun(img):
    cx, cy = SW * 0.885, SH * 0.055
    radial(img, cx, cy, SH * 0.66, (255, 244, 200), 104, falloff=2.5)
    radial(img, cx, cy, SH * 0.22, (255, 252, 236), 200, falloff=1.5)
    radial(img, cx, cy, SH * 0.07, (255, 255, 252), 240, falloff=1.1)

    def rays(d, k):
        for ang, wid, a in [(203, 4.6, 30), (215, 2.6, 22), (229, 6.0, 26),
                            (243, 2.4, 18), (256, 4.0, 22)]:
            a0, a1 = math.radians(ang - wid), math.radians(ang + wid)
            L = SH * 1.6 * k
            d.polygon([(cx * k, cy * k),
                       (cx * k + L * math.cos(a0), cy * k + L * math.sin(a0)),
                       (cx * k + L * math.cos(a1), cy * k + L * math.sin(a1))],
                      fill=(255, 250, 224, a))
    soft(img, rays, SH * 0.055)


def cloud(img, cx, cy, w, alpha=240):
    """Fluffy cumulus: lobed mask filled with a white-to-blue-grey vertical wash."""
    puffs = [(-0.52, 0.20, 0.26), (-0.28, 0.02, 0.36), (-0.04, -0.12, 0.44),
             (0.22, -0.02, 0.36), (0.48, 0.16, 0.28), (0.10, 0.20, 0.34),
             (-0.16, 0.26, 0.30), (0.34, 0.26, 0.24)]
    pad = w * 0.9
    tw, th = int(w * 2.2), int(w * 1.5)
    tile = Image.new("L", (tw, th), 0)
    d = ImageDraw.Draw(tile)
    ox, oy = tw / 2, th * 0.56
    for dx, dy, r in puffs:
        rr = w * r
        x, y = ox + dx * w, oy + dy * w
        d.ellipse([x - rr, y - rr * 0.84, x + rr, y + rr * 0.84], fill=255)
    tile = tile.filter(ImageFilter.GaussianBlur(w * 0.045))
    wash = vgrad((tw, th), [(0.0, (255, 255, 255)), (0.52, (250, 253, 255)),
                            (0.80, (196, 220, 240)), (1.0, (170, 202, 230))])
    body = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    body.paste(wash, (0, 0))
    body.putalpha(tile.point(lambda v: int(v * alpha / 255)))
    img.alpha_composite(body, (int(cx - ox), int(cy - oy)))
    del pad


def rainbow(img):
    """A short arc rising out of the left edge, fading before it reaches centre."""
    layer = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = SW * 0.42, SH * 0.72
    rx, ry = SW * 0.40, SH * 0.64
    band = SH * 0.017
    for i, col in enumerate([(238, 104, 96), (246, 162, 74), (250, 218, 96),
                             (128, 210, 126), (88, 174, 234), (152, 124, 216)]):
        r = i * band
        d.arc([cx - rx + r, cy - ry + r, cx + rx - r, cy + ry - r],
              188, 268, fill=(*col, 200), width=int(band * 1.2))
    layer = layer.filter(ImageFilter.GaussianBlur(SH * 0.007))

    vfade = vgrad((SW, SH), [(0.0, (255,) * 3), (0.34, (215,) * 3),
                             (0.56, (0,) * 3), (1.0, (0,) * 3)]).convert("L")
    strip = Image.new("L", (256, 1))
    sp = strip.load()
    for x in range(256):
        sp[x, 0] = int(255 * max(0.0, min(1.0, 1.35 - (x / 255) * 3.1)))
    hfade = strip.resize((SW, SH), Image.Resampling.BICUBIC)
    layer.putalpha(ImageChops.multiply(ImageChops.multiply(layer.getchannel("A"), vfade), hfade))
    img.alpha_composite(layer)


def bubble(img, cx, cy, r, tint=(255, 255, 255), alpha=64):
    """Glass bubble: faint body, bright rim, hot spot up-left."""
    size = int(r * 2.6)
    if size < 6:
        return
    tile = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    c = size / 2
    d.ellipse([c - r, c - r, c + r, c + r], fill=(*tint, alpha))
    d.ellipse([c - r, c - r, c + r, c + r], outline=(255, 255, 255, min(255, alpha + 95)),
              width=max(2, int(r * 0.11)))
    hr = r * 0.32
    hx, hy = c - r * 0.34, c - r * 0.40
    d.ellipse([hx - hr, hy - hr * 0.76, hx + hr, hy + hr * 0.76],
              fill=(255, 255, 255, min(255, alpha + 135)))
    lr = r * 0.15
    lx, ly = c + r * 0.36, c + r * 0.40
    d.ellipse([lx - lr, ly - lr, lx + lr, ly + lr], fill=(255, 255, 255, min(255, alpha + 70)))
    img.alpha_composite(tile.filter(ImageFilter.GaussianBlur(max(0.8, r * 0.05))),
                        (int(cx - c), int(cy - c)))


def sparkle(img, cx, cy, r, alpha=240):
    size = int(r * 3.2)
    tile = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    c = size / 2
    d.polygon([(c, c - r), (c + r * 0.12, c), (c, c + r), (c - r * 0.12, c)],
              fill=(255, 255, 255, alpha))
    d.polygon([(c - r * 0.58, c), (c, c - r * 0.11), (c + r * 0.58, c), (c, c + r * 0.11)],
              fill=(255, 255, 255, alpha))
    d.ellipse([c - r * 0.15, c - r * 0.15, c + r * 0.15, c + r * 0.15], fill=(255, 255, 255, 255))
    img.alpha_composite(tile.filter(ImageFilter.GaussianBlur(r * 0.34)), (int(cx - c), int(cy - c)))
    img.alpha_composite(tile.filter(ImageFilter.GaussianBlur(r * 0.045)), (int(cx - c), int(cy - c)))


# ---------------------------------------------------------------- dolphins

# Local space: nose at +x, tail at -x, y positive downward, body ~2.2 long.
# The flukes are a separate sharp-cornered polygon: run through the spline
# with the body they just round off into a blob and stop reading as a tail.
BODY = [
    (1.06, 0.02), (1.00, -0.06), (0.86, -0.12), (0.70, -0.20), (0.48, -0.23),
    (0.20, -0.25), (-0.10, -0.23), (-0.42, -0.15), (-0.66, -0.06),
    (-0.74, 0.00), (-0.66, 0.05), (-0.38, 0.13), (-0.02, 0.20), (0.32, 0.21),
    (0.62, 0.18), (0.80, 0.14), (0.94, 0.12), (1.05, 0.07),
]
FLUKE = [
    (-0.60, -0.05), (-0.86, -0.22), (-1.16, -0.31), (-1.06, -0.13),
    (-0.88, -0.01), (-1.05, 0.13), (-1.15, 0.29), (-0.87, 0.18), (-0.60, 0.06),
]
DORSAL = [(0.24, -0.25), (0.12, -0.42), (-0.04, -0.54), (-0.12, -0.42), (-0.06, -0.25)]
PECTORAL = [(0.36, 0.12), (0.30, 0.32), (0.12, 0.46), (0.16, 0.28), (0.30, 0.16)]


def dolphin(img, cx, cy, size, angle_deg, alpha=255):
    """Built flat in local space with a body-length gradient, then rotated once."""
    pad = 1.5
    tw = int(size * 2.6 * pad)
    th = int(size * 2.0 * pad)
    ox, oy = tw / 2, th / 2

    def pts(poly):
        return [(ox + x * size, oy + y * size) for x, y in catmull(poly, closed=True)]

    mask = Image.new("L", (tw, th), 0)
    dm = ImageDraw.Draw(mask)
    dm.polygon(pts(BODY), fill=255)
    dm.polygon(pts(DORSAL), fill=255)

    # fins carry their own dark tone; the body gradient would bleach the
    # flukes white exactly where they cross the belly band
    fins = Image.new("L", (tw, th), 0)
    df = ImageDraw.Draw(fins)
    df.polygon(pts(PECTORAL), fill=255)
    df.polygon([(ox + x * size, oy + y * size) for x, y in FLUKE], fill=255)
    pec = fins

    # dorsal cape -> flank -> white belly, down the body's short axis
    wash = vgrad((tw, th), [
        (0.00, (26, 74, 116)), (0.30, (44, 104, 152)), (0.44, (86, 148, 190)),
        (0.56, (156, 200, 226)), (0.66, (226, 242, 248)), (0.78, (250, 253, 255)),
        (1.00, (214, 234, 242)),
    ])
    tile = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    tile.paste(wash, (0, 0))

    # fins sit under the body, in the cape's darker blue
    finwash = vgrad((tw, th), [(0.00, (30, 82, 126)), (0.50, (54, 116, 162)),
                               (1.00, (86, 148, 188))])
    pecl = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    pecl.paste(finwash, (0, 0))
    pecl.putalpha(pec.filter(ImageFilter.GaussianBlur(size * 0.008)))

    tile.putalpha(mask.filter(ImageFilter.GaussianBlur(size * 0.008)))
    body = Image.alpha_composite(pecl, tile)

    d = ImageDraw.Draw(body)
    # specular streak along the back and a soft crease under the beak
    d.line([(ox + x * size, oy + y * size) for x, y in
            catmull([(-0.55, -0.14), (-0.12, -0.26), (0.24, -0.28), (0.56, -0.24),
                     (0.82, -0.14)], closed=False)],
           fill=(255, 255, 255, 190), width=max(2, int(size * 0.030)), joint="curve")
    d.line([(ox + x * size, oy + y * size) for x, y in
            catmull([(0.94, 0.09), (0.82, 0.05), (0.74, -0.02)], closed=False)],
           fill=(30, 76, 116, 150), width=max(2, int(size * 0.016)), joint="curve")
    body = body.filter(ImageFilter.GaussianBlur(size * 0.010))
    body.putalpha(ImageChops.multiply(body.getchannel("A"),
                                      ImageChops.lighter(mask, pec)))

    # eye and smile, drawn crisp on top
    d2 = ImageDraw.Draw(body)
    ex, ey = ox + 0.70 * size, oy - 0.10 * size
    er = size * 0.030
    d2.ellipse([ex - er, ey - er, ex + er, ey + er], fill=(20, 32, 46, 255))
    d2.ellipse([ex - er * 0.34, ey - er * 0.50, ex + er * 0.22, ey + er * 0.02],
               fill=(255, 255, 255, 255))
    d2.arc([ex + er * 0.4, ey - er * 0.6, ex + er * 4.6, ey + er * 3.0],
           15, 78, fill=(28, 70, 108, 190), width=max(2, int(size * 0.015)))

    rot = body.rotate(-angle_deg, resample=Image.Resampling.BICUBIC, expand=True)
    if alpha < 255:
        rot.putalpha(rot.getchannel("A").point(lambda v: int(v * alpha / 255)))
    img.alpha_composite(rot, (int(cx - rot.width / 2), int(cy - rot.height / 2)))


def trail(img, cx, cy, size, angle_deg):
    """A few droplets flung off the flukes, so a leap reads as just-launched."""
    th = math.radians(angle_deg)

    def world(lx, ly):
        return (cx + (lx * math.cos(th) - ly * math.sin(th)) * size,
                cy + (lx * math.sin(th) + ly * math.cos(th)) * size)

    for lx, ly, r, a in [(-1.34, 0.06, 0.070, 215), (-1.52, 0.20, 0.055, 180),
                         (-1.70, 0.36, 0.042, 150), (-1.44, -0.16, 0.040, 165),
                         (-1.86, 0.16, 0.032, 120)]:
        x, y = world(lx, ly)
        soft_ellipse(img, x, y, size * r, size * r * 1.25, (255, 255, 255), a, size * r * 0.45)


# ---------------------------------------------------------------- sea


def sea(img):
    y0 = int(SH * HORIZON)
    depth = SH - y0
    water = vgrad((SW, depth), [
        (0.00, (120, 222, 232)),
        (0.10, (44, 178, 206)),
        (0.34, (20, 130, 180)),
        (0.70, (14, 92, 152)),
        (1.00, (12, 70, 128)),
    ]).convert("RGBA")
    # feather the top edge so the horizon has no hard seam to ring against
    edge = vgrad((SW, depth), [(0.0, (0,) * 3), (0.012, (255,) * 3), (1.0, (255,) * 3)]).convert("L")
    water.putalpha(edge)
    img.alpha_composite(water, (0, y0))

    def surf(d, k):
        d.rectangle([0, (y0 - SH * 0.004) * k, SW * k, (y0 + SH * 0.010) * k],
                    fill=(240, 253, 255, 205))
    soft(img, surf, SH * 0.010)

    def shafts(d, k):
        for x, wid, a in [(0.10, 0.028, 34), (0.27, 0.018, 26), (0.46, 0.034, 30),
                          (0.66, 0.020, 24), (0.85, 0.030, 28)]:
            top = SW * x
            d.polygon([((top - SW * wid) * k, y0 * k), ((top + SW * wid) * k, y0 * k),
                       ((top + SW * wid * 2.8) * k, SH * k),
                       ((top - SW * wid * 1.5) * k, SH * k)],
                      fill=(198, 246, 255, a))
    soft(img, shafts, SH * 0.032)

    # caustic ripples just under the surface
    def caustics(d, k):
        for i, (yy, amp, a) in enumerate([(0.030, 0.006, 96), (0.068, 0.009, 74),
                                          (0.115, 0.012, 56), (0.170, 0.010, 40),
                                          (0.230, 0.013, 30)]):
            pts = []
            for j in range(41):
                x = SW * j / 40
                y = y0 + SH * yy + math.sin(j * 0.55 + i * 1.7) * SH * amp
                pts.append((x * k, y * k))
            d.line(pts, fill=(214, 250, 255, a), width=max(2, int(SH * 0.005 * k)), joint="curve")
    soft(img, caustics, SH * 0.008)

    seabed(img)


def coral_branch(d, x, base, h, w, col, k):
    """Staghorn: a trunk with a couple of tapering arms."""
    for dx, lean, sc in [(0.0, 0.0, 1.0), (-0.55, -0.35, 0.62), (0.55, 0.32, 0.70)]:
        bx = x + dx * w
        tipx = bx + lean * w * 1.4
        tipy = base - h * sc
        arm = [(bx - w * 0.20 * sc, base), (bx - w * 0.13 * sc, base - h * 0.45 * sc),
               (tipx - w * 0.07 * sc, tipy + h * 0.10 * sc), (tipx, tipy),
               (tipx + w * 0.08 * sc, tipy + h * 0.10 * sc),
               (bx + w * 0.14 * sc, base - h * 0.45 * sc), (bx + w * 0.21 * sc, base)]
        d.polygon([(px * k, py * k) for px, py in catmull(arm, closed=True)], fill=(*col, 232))


def coral_fan(d, x, base, h, w, col, k):
    """Sea fan: a rounded blade on a short stem."""
    stem = [(x - w * 0.07, base), (x - w * 0.05, base - h * 0.35),
            (x + w * 0.05, base - h * 0.35), (x + w * 0.07, base)]
    d.polygon([(px * k, py * k) for px, py in stem], fill=(*col, 220))
    blade = [(x, base - h * 0.28), (x - w * 0.62, base - h * 0.58),
             (x - w * 0.44, base - h * 0.95), (x, base - h * 1.06),
             (x + w * 0.44, base - h * 0.95), (x + w * 0.62, base - h * 0.58)]
    d.polygon([(px * k, py * k) for px, py in catmull(blade, closed=True)], fill=(*col, 226))


def coral_brain(d, x, base, h, w, col, k):
    """Brain coral: a squat dome."""
    d.ellipse([(x - w * 0.72) * k, (base - h * 1.05) * k,
               (x + w * 0.72) * k, (base + h * 0.30) * k], fill=(*col, 230))


def coral_tubes(d, x, base, h, w, col, k):
    """Tube sponge: a clutch of vertical pipes of uneven height."""
    for i, (dx, sc) in enumerate([(-0.5, 0.72), (-0.16, 1.0), (0.2, 0.85), (0.52, 0.6)]):
        bx = x + dx * w
        r = w * 0.16
        top = base - h * sc
        d.rounded_rectangle([(bx - r) * k, top * k, (bx + r) * k, base * k],
                            radius=r * 0.9 * k, fill=(*col, 230))


def kelp(d, x, base, h, w, col, k):
    """Two or three ribbons of seaweed with a lazy S-curve."""
    for i, (dx, lean, sc) in enumerate([(-0.6, 0.5, 0.82), (0.0, -0.4, 1.0), (0.7, 0.6, 0.68)]):
        bx = x + dx * w
        spine = [(bx, base)]
        for j in range(1, 6):
            t = j / 5
            spine.append((bx + math.sin(t * 3.0 + i) * w * 0.9 + lean * w * t,
                          base - h * sc * t))
        half = w * 0.20
        left = [(px - half * (1 - n / len(spine)), py) for n, (px, py) in enumerate(spine)]
        right = [(px + half * (1 - n / len(spine)), py) for n, (px, py) in enumerate(spine)][::-1]
        d.polygon([(px * k, py * k) for px, py in catmull(left + right, closed=True)],
                  fill=(*col, 224))


def seabed(img):
    """A low reef silhouette hugging the bottom edge.

    Deliberately dark and low-contrast: the (A) Play hint renders in white
    around y=0.82, so the band above the reef stays deep and uncluttered.
    """
    y = SH * SEABED
    sand = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sand)
    pts = [(0, SH)]
    for i in range(25):
        x = SW * i / 24
        pts.append((x, y + math.sin(i * 0.7) * SH * 0.008 + math.sin(i * 1.9) * SH * 0.004))
    pts += [(SW, SH)]
    ds.polygon(pts, fill=(198, 186, 152, 240))
    img.alpha_composite(sand.filter(ImageFilter.GaussianBlur(SH * 0.004)))

    # clustered rather than evenly spaced, with bare seabed between groups
    reef = [
        (0.022, kelp, 0.115, 0.024, (26, 140, 118)),
        (0.062, coral_branch, 0.095, 0.036, (226, 74, 128)),
        (0.104, coral_tubes, 0.070, 0.030, (240, 132, 56)),
        (0.146, coral_brain, 0.030, 0.038, (52, 172, 162)),
        (0.256, coral_branch, 0.088, 0.036, (140, 82, 200)),
        (0.298, coral_tubes, 0.058, 0.026, (238, 108, 82)),
        (0.430, coral_branch, 0.100, 0.036, (48, 162, 200)),
        (0.470, kelp, 0.098, 0.022, (28, 146, 122)),
        (0.512, coral_fan, 0.062, 0.034, (232, 70, 116)),
        (0.640, coral_tubes, 0.074, 0.028, (226, 158, 54)),
        (0.684, coral_brain, 0.028, 0.036, (50, 168, 178)),
        (0.800, coral_branch, 0.092, 0.036, (150, 80, 204)),
        (0.844, coral_tubes, 0.062, 0.028, (232, 110, 70)),
        (0.950, coral_branch, 0.086, 0.034, (214, 66, 122)),
        (0.984, kelp, 0.092, 0.022, (26, 140, 118)),
    ]
    for x, fn, h, w, col in reef:
        base = SH * (SEABED + 0.045)

        soft_ellipse(img, SW * x, base, SW * w * 1.15, SH * 0.008,
                     (74, 96, 104), 120, SH * 0.006)

        def draw(d, k, x=x, fn=fn, h=h, w=w, col=col, base=base):
            fn(d, SW * x, base, SH * h, SW * w, col, k)
        soft(img, draw, SH * 0.0035, scale=1.0)

    # depth tint: sinks the reef back and keeps the hint band quiet
    def tint(d, k):
        d.rectangle([0, SH * 0.78 * k, SW * k, SH * k], fill=(12, 74, 132, 48))
    soft(img, tint, SH * 0.05)


def fish(img, cx, cy, size, colour, flip, stripe=None):
    body = [(1.0, 0.0), (0.44, -0.50), (-0.22, -0.44), (-0.60, -0.10),
            (-0.60, 0.10), (-0.22, 0.44), (0.44, 0.50)]
    tail = [(-0.52, 0.0), (-0.98, -0.46), (-0.80, 0.0), (-0.98, 0.46)]
    fin = [(0.02, -0.42), (-0.10, -0.66), (-0.26, -0.44)]
    sx = -1 if flip else 1
    pad = int(size * 2.6)
    tile = Image.new("RGBA", (pad, pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    o = pad / 2

    def P(poly, closed=True):
        return [(o + x * size * sx, o + y * size) for x, y in catmull(poly, closed=closed)]

    d.polygon(P(tail), fill=(*colour, 232))
    d.polygon(P(fin), fill=(*colour, 232))
    d.polygon(P(body), fill=(*colour, 245))
    if stripe:
        for sxx in (-0.16, 0.24):
            d.polygon([(o + (sxx - 0.08) * size * sx, o - 0.46 * size),
                       (o + (sxx + 0.06) * size * sx, o - 0.44 * size),
                       (o + (sxx + 0.10) * size * sx, o + 0.44 * size),
                       (o + (sxx - 0.04) * size * sx, o + 0.46 * size)],
                      fill=(*stripe, 235))
    er = size * 0.13
    ex, ey = o + 0.50 * size * sx, o - 0.11 * size
    d.ellipse([ex - er, ey - er, ex + er, ey + er], fill=(28, 40, 56, 245))
    d.ellipse([ex - er * 0.34, ey - er * 0.48, ex + er * 0.2, ey + er * 0.08],
              fill=(255, 255, 255, 245))
    img.alpha_composite(tile.filter(ImageFilter.GaussianBlur(size * 0.035)),
                        (int(cx - o), int(cy - o)))


# ---------------------------------------------------------------- scene


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    img = sky()
    sun(img)
    rainbow(img)

    # clouds kept off the rainbow (left) and away from the covers (centre)
    cloud(img, SW * 0.56, SH * 0.10, SW * 0.115)
    cloud(img, SW * 0.79, SH * 0.055, SW * 0.085, alpha=215)
    cloud(img, SW * 0.955, SH * 0.235, SW * 0.075, alpha=185)
    cloud(img, SW * 0.665, SH * 0.285, SW * 0.060, alpha=155)
    cloud(img, SW * 0.055, SH * 0.545, SW * 0.055, alpha=140)
    cloud(img, SW * 0.40, SH * 0.40, SW * 0.050, alpha=120)

    sea(img)

    # a pod of three: hero on the left, the others smaller and further off
    dolphin(img, SW * 0.112, SH * 0.298, SH * 0.072, -18, alpha=195)
    trail(img, SW * 0.112, SH * 0.298, SH * 0.072, -18)

    dolphin(img, SW * 0.270, SH * 0.402, SH * 0.208, -27)
    trail(img, SW * 0.270, SH * 0.402, SH * 0.208, -27)

    dolphin(img, SW * 0.500, SH * 0.553, SH * 0.104, -34, alpha=225)
    trail(img, SW * 0.500, SH * 0.553, SH * 0.104, -34)

    # tropical fish, varied heights and sizes, a couple paired up
    for x, y, s, col, flip, stripe in [
        (0.062, 0.756, 1.00, (255, 172, 44), False, (255, 255, 255)),
        (0.112, 0.716, 0.62, (255, 226, 84), True, None),
        (0.286, 0.782, 0.78, (255, 118, 88), False, (255, 240, 220)),
        (0.352, 0.724, 0.54, (250, 250, 255), True, (70, 150, 210)),
        (0.560, 0.762, 0.88, (255, 196, 60), False, (40, 60, 90)),
        (0.622, 0.806, 0.52, (140, 226, 244), True, None),
        (0.808, 0.734, 0.70, (246, 132, 176), False, None),
        (0.902, 0.784, 0.56, (255, 210, 70), True, (60, 90, 130)),
    ]:
        fish(img, SW * x, SH * y, SH * 0.030 * s, col, flip, stripe)

    # bubble trails rising off the reef
    for x, y, r in [(0.168, 0.900, 0.85), (0.178, 0.856, 0.60), (0.188, 0.818, 0.44),
                    (0.536, 0.910, 0.75), (0.546, 0.868, 0.52), (0.556, 0.834, 0.38),
                    (0.876, 0.898, 0.68), (0.886, 0.858, 0.46)]:
        bubble(img, SW * x, SH * y, SH * 0.012 * r * 2.2, alpha=76)

    # glass bubbles drifting up the sky, densest away from the covers
    for x, y, r, a in [(0.045, 0.255, 1.4, 62), (0.098, 0.405, 0.95, 58),
                       (0.030, 0.610, 0.66, 52), (0.905, 0.470, 1.15, 56),
                       (0.960, 0.285, 0.78, 52), (0.835, 0.360, 0.52, 44),
                       (0.700, 0.475, 0.62, 44), (0.480, 0.180, 0.58, 40)]:
        bubble(img, SW * x, SH * y, SH * 0.030 * r, alpha=a)

    for x, y, r in [(0.905, 0.100, 0.052), (0.820, 0.042, 0.028), (0.960, 0.190, 0.024),
                    (0.148, 0.230, 0.022), (0.062, 0.455, 0.018), (0.300, 0.560, 0.018),
                    (0.585, 0.690, 0.020), (0.245, 0.690, 0.018), (0.760, 0.700, 0.016)]:
        sparkle(img, SW * x, SH * y, SH * r)

    # gentle centre bloom lifts the covers off the background
    radial(img, SW * 0.52, SH * 0.44, SH * 0.60, (255, 255, 255), 30, falloff=1.5)

    final = img.convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    final = final.filter(ImageFilter.UnsharpMask(radius=1.0, percent=30, threshold=4))
    final.save(OUT / "background.png", optimize=True)
    print("wrote", OUT / "background.png", final.size)


if __name__ == "__main__":
    main()
