#!/usr/bin/env python3
"""Draw every texture the Kids channel banner and icon use.

The channel reads as a pasted rectangle because banner_BG.tpl is 4x347 and
menubnr_BG.tpl is 2x96 — single-column gradient strips stretched across
panes that are 608x456 and 170x96. Those get drawn at a real resolution
here, which is why the rebuild has to resize TPLs rather than patch pixels
in place.

The motion was already in the file. banner_Loop.brlan scrolls N_sil_tra_00
and N_sil_tra_01 over 2000 frames, each carrying three 614x48 strips laid
end to end at -614/0/+614, so a seamless band scrolls forever. Blanking
those strips to remove the black tickers is what made the channel look
static. Drawing dolphins and bubbles into them brings the animation back
without touching a single byte of brlyt or brlan.

The strips are IA8/IA4 — intensity and alpha only — and the layout tints
them per material: pale cyan (192,240,255) for the _res band and light
grey (194,194,194) for _spo. So they are shape, not colour, and every
element has to tile seamlessly at the strip width.

The dolphin outline is imported from the app's own background generator so
the channel and the loader draw the same animal.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(REPO / "scripts"))

from kids_background import catmull  # noqa: E402

# The app's dolphin outline is authored for 200px+ and does not survive the
# downscale to the ~44px a 48px band allows: the slim body, tall dorsal and
# low pectoral all read as a shark. This is the same animal redrawn for the
# size it is actually shown at — fatter body, blunt beak, small swept dorsal.
BAND_BODY = [
    (1.02, 0.10), (0.88, 0.01), (0.80, -0.11), (0.60, -0.25), (0.32, -0.31),
    (-0.02, -0.31), (-0.34, -0.22), (-0.56, -0.10), (-0.62, 0.00),
    (-0.56, 0.10), (-0.26, 0.20), (0.08, 0.28), (0.48, 0.26), (0.74, 0.19),
    (0.87, 0.16), (0.99, 0.15),
]
BAND_DORSAL = [(0.28, -0.29), (0.16, -0.56), (0.00, -0.62), (-0.05, -0.44), (0.02, -0.30)]
BAND_FLUKE = [(-0.52, -0.06), (-1.03, -0.31), (-0.78, 0.00), (-1.03, 0.31), (-0.52, 0.10)]
BAND_PEC = [(0.28, 0.21), (0.10, 0.40), (0.32, 0.25)]

FONT = REPO / "out" / "imgs" / "font.ttf"
S = 4  # supersample


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


def rot(p, ang, o):
    c, s = math.cos(ang), math.sin(ang)
    return (o[0] + c * (p[0] - o[0]) - s * (p[1] - o[1]),
            o[1] + s * (p[0] - o[0]) + c * (p[1] - o[1]))


def dolphin_mask(size, angle_deg, flip=False):
    """The app's dolphin as a solid alpha shape, for the tinted strips."""
    w = int(size * 2.8)
    h = int(size * 2.0)
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    ox, oy = w / 2, h / 2
    ang = math.radians(angle_deg)

    def pts(poly, smooth=True):
        seq = catmull(poly, closed=True) if smooth else poly
        out = []
        for x, y in seq:
            if flip:
                x = -x
            out.append(rot((ox + x * size, oy + y * size), ang, (ox, oy)))
        return out

    d.polygon(pts(BAND_BODY), fill=255)
    d.polygon(pts(BAND_DORSAL), fill=255)
    d.polygon(pts(BAND_PEC, smooth=False), fill=255)
    d.polygon(pts(BAND_FLUKE, smooth=False), fill=255)
    return m


def seamless_band(w, h, elements):
    """Draw elements onto a strip that tiles at width w.

    Everything is stamped three times (x-w, x, x+w) so a shape crossing an
    edge appears on both sides and the three strips the layout lays end to
    end meet without a seam.
    """
    big = Image.new("L", (w * S, h * S), 0)
    for fn, x, y in elements:
        for dx in (-w, 0, w):
            fn(big, (x + dx) * S, y * S)
    return big.resize((w, h), Image.Resampling.LANCZOS)


def bubble(size, ring=0.19):
    def draw(canvas, x, y):
        r = size * S / 2
        tile = Image.new("L", (int(r * 2.6), int(r * 2.6)), 0)
        d = ImageDraw.Draw(tile)
        c = tile.width / 2
        d.ellipse([c - r, c - r, c + r, c + r], fill=95)
        d.ellipse([c - r, c - r, c + r, c + r], outline=255, width=max(2, int(r * ring)))
        hr = r * 0.30
        d.ellipse([c - r * 0.34 - hr, c - r * 0.38 - hr,
                   c - r * 0.34 + hr, c - r * 0.38 + hr], fill=255)
        canvas.paste(tile, (int(x - c), int(y - c)), tile)
    return draw


def dolphin(size, angle, flip=False):
    def draw(canvas, x, y):
        m = dolphin_mask(size * S, angle, flip)
        canvas.paste(m, (int(x - m.width / 2), int(y - m.height / 2)), m)
    return draw


def cloud(size, flip=False):
    """Puffy cumulus for the sky band. The _spo material tints it
    (194,194,194), which is already cloud grey."""
    def draw(canvas, x, y):
        s_ = size * S
        tile = Image.new("L", (int(s_ * 3.2), int(s_ * 2.6)), 0)
        d = ImageDraw.Draw(tile)
        o, oy = tile.width / 2, tile.height * 0.60
        lobes = [(-0.64, 0.26, 0.30), (-0.26, -0.08, 0.47), (0.20, 0.08, 0.37),
                 (0.60, 0.28, 0.26)]
        for dx, dy, r in lobes:
            if flip:
                dx = -dx
            rr = s_ * r
            cx_, cy_ = o + dx * s_, oy + dy * s_
            d.ellipse([cx_ - rr, cy_ - rr * 0.84, cx_ + rr, cy_ + rr * 0.84], fill=255)
        d.rectangle([o - s_ * 0.64, oy + s_ * 0.22, o + s_ * 0.60, oy + s_ * 0.46], fill=255)
        tile = tile.filter(ImageFilter.GaussianBlur(s_ * 0.03))
        canvas.paste(tile, (int(x - o), int(y - oy)), tile)
    return draw


def fish(size, flip=False):
    def draw(canvas, x, y):
        s = size * S
        tile = Image.new("L", (int(s * 3), int(s * 3)), 0)
        d = ImageDraw.Draw(tile)
        o = tile.width / 2
        sx = -1 if flip else 1
        body = [(1.0, 0.0), (0.44, -0.50), (-0.22, -0.44), (-0.60, -0.10),
                (-0.60, 0.10), (-0.22, 0.44), (0.44, 0.50)]
        tail = [(-0.52, 0.0), (-0.98, -0.46), (-0.80, 0.0), (-0.98, 0.46)]
        for poly in (tail, body):
            d.polygon([(o + px * s * sx, o + py * s)
                       for px, py in catmull(poly, closed=True)], fill=255)
        canvas.paste(tile, (int(x - o), int(y - o)), tile)
    return draw


def ia_png(mask, path):
    """White pixels, shape in alpha — encode_ia8/ia4 read intensity and alpha."""
    img = Image.merge("RGBA", (Image.new("L", mask.size, 255),) * 3 + (mask,))
    img.save(path)
    print(f"  {path.name}: {mask.size[0]}x{mask.size[1]}")


# ---------------------------------------------------------------- scene


def scene(w, h):
    """The app's sky-and-reef composition, sized for the banner pane."""
    img = vgrad((w, h), [
        (0.00, (86, 188, 238)), (0.20, (92, 193, 240)), (0.34, (118, 208, 244)),
        (0.44, (176, 228, 248)), (0.485, (214, 242, 250)),
        (0.50, (96, 205, 224)), (0.56, (60, 186, 214)), (0.66, (52, 178, 208)),
        (0.78, (30, 146, 188)), (0.90, (18, 108, 162)), (1.00, (14, 84, 140)),
    ]).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")

    # sun glow, upper right
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for i in range(28, 0, -1):
        r = w * 0.30 * i / 28
        gd.ellipse([w * 0.88 - r, h * 0.06 - r, w * 0.88 + r, h * 0.06 + r],
                   fill=(255, 248, 214, int(7 * (1 - i / 28) ** 1.5) + 2))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(w * 0.02)))

    # rainbow arc out of the left edge, same restraint as the app
    rb = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rb)
    cx, cy, rx, ry = w * 0.40, h * 0.56, w * 0.42, h * 0.46
    band = h * 0.018
    for i, col in enumerate([(238, 104, 96), (246, 162, 74), (250, 218, 96),
                             (128, 210, 126), (88, 174, 234), (152, 124, 216)]):
        o = i * band
        rd.arc([cx - rx + o, cy - ry + o, cx + rx - o, cy + ry - o],
               190, 268, fill=(*col, 150), width=max(1, int(band * 1.2)))
    rb = rb.filter(ImageFilter.GaussianBlur(h * 0.008))
    fade = Image.new("L", (w, 1))
    fp = fade.load()
    for x in range(w):
        fp[x, 0] = int(255 * max(0.0, min(1.0, 1.35 - (x / w) * 3.0)))
    rb.putalpha(Image.eval(rb.getchannel("A"), lambda v: v))
    rb.putalpha(Image.composite(rb.getchannel("A"),
                                Image.new("L", (w, h), 0),
                                fade.resize((w, h), Image.Resampling.BICUBIC)))
    img.alpha_composite(rb)

    # clouds
    for cx_, cy_, cw in [(0.72, 0.22, 0.07), (0.20, 0.28, 0.05)]:
        cl = Image.new("L", (w, h), 0)
        cd = ImageDraw.Draw(cl)
        for dx, dy, rr in [(-0.5, 0.18, 0.26), (-0.25, 0.02, 0.36), (0.0, -0.10, 0.42),
                           (0.28, 0.02, 0.34), (0.5, 0.18, 0.26)]:
            r = w * cw * rr
            cd.ellipse([w * cx_ + dx * w * cw - r, h * cy_ + dy * h * 0.10 - r * 0.85,
                        w * cx_ + dx * w * cw + r, h * cy_ + dy * h * 0.10 + r * 0.85],
                       fill=235)
        cl = cl.filter(ImageFilter.GaussianBlur(w * cw * 0.05))
        white = Image.new("RGBA", (w, h), (255, 255, 255, 0))
        white.putalpha(cl)
        img.alpha_composite(white)

    # waterline glint
    gl = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(gl).rectangle([0, h * 0.495, w, h * 0.508], fill=(240, 253, 255, 200))
    img.alpha_composite(gl.filter(ImageFilter.GaussianBlur(h * 0.008)))

    # reef along the bottom
    sand = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sand)
    pts = [(0, h)]
    for i in range(21):
        pts.append((w * i / 20, h * 0.90 + math.sin(i * 0.8) * h * 0.012))
    pts.append((w, h))
    sd.polygon(pts, fill=(200, 188, 154, 240))
    img.alpha_composite(sand.filter(ImageFilter.GaussianBlur(h * 0.004)))
    for x, ch, col in [(0.05, 0.055, (226, 74, 128)), (0.12, 0.038, (240, 132, 56)),
                       (0.20, 0.030, (52, 172, 162)), (0.31, 0.050, (140, 82, 200)),
                       (0.44, 0.034, (238, 108, 82)), (0.56, 0.052, (48, 162, 200)),
                       (0.67, 0.030, (232, 70, 116)), (0.78, 0.048, (226, 158, 54)),
                       (0.89, 0.036, (150, 80, 204)), (0.96, 0.044, (26, 140, 118))]:
        cd = ImageDraw.Draw(img, "RGBA")
        base = h * 0.945
        for dx, sc in [(-0.5, 0.6), (0.0, 1.0), (0.5, 0.7)]:
            r = w * 0.010 * sc
            bx = w * x + dx * w * 0.012
            cd.ellipse([bx - r, base - h * ch * sc, bx + r, base + r], fill=(*col, 225))
    return img.convert("RGB")


def dither565(img):
    """Quantise toward RGB565 with error diffusion so the sky does not band.

    The pane is a large smooth gradient and RGB565 has 5-6-5 bits, which is
    exactly where banding shows; the old strip banded visibly on the TV.
    """
    px = img.convert("RGB").load()
    w, h = img.size
    buf = [[list(px[x, y]) for x in range(w)] for y in range(h)]
    bits = (3, 2, 3)
    for y in range(h):
        for x in range(w):
            old = buf[y][x][:]
            new = []
            for c in range(3):
                q = max(0, min(255, int(old[c])))
                q = (q >> bits[c]) << bits[c]
                q |= q >> (8 - bits[c])
                new.append(q)
            buf[y][x] = new
            for c in range(3):
                err = old[c] - new[c]
                for dx, dy, f in ((1, 0, 7 / 16), (-1, 1, 3 / 16), (0, 1, 5 / 16), (1, 1, 1 / 16)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h:
                        buf[ny][nx][c] += err * f
    out = Image.new("RGB", (w, h))
    op = out.load()
    for y in range(h):
        for x in range(w):
            op[x, y] = tuple(max(0, min(255, int(v))) for v in buf[y][x])
    return out


def wordmark(w, h, fit=0.88):
    """WiiFlow KIDS, the same lockup the boot splash uses.

    The type is shrunk until the lockup occupies at most `fit` of the
    texture width. The icon pane scales its 120x48 texture by 1.10, so
    type drawn edge to edge came back clipped on both sides in the Wii
    Menu; measuring instead of guessing a point size fixes that for any
    string length.
    """
    img = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    left, right = "WiiFlow", "KIDS"
    size = int(h * S * 0.46)
    while size > 6:
        f = ImageFont.truetype(str(FONT), size)
        gap = size * 0.28
        lw = d.textlength(left, font=f)
        rw = d.textlength(right, font=f)
        if lw + gap + rw <= w * S * fit:
            break
        size -= 1
    f = ImageFont.truetype(str(FONT), size)
    gap = size * 0.28
    lw = d.textlength(left, font=f)
    rw = d.textlength(right, font=f)
    x = (w * S - (lw + gap + rw)) / 2
    y = h * S * 0.5

    for text, adv, fill in ((left, lw, (255, 255, 255)), (right, rw, (255, 214, 64))):
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((x, y + size * 0.10), text, font=f,
                                fill=(10, 52, 96, 190), anchor="lm")
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(size * 0.09)))
        d.text((x, y), text, font=f, fill=(*fill, 255), anchor="lm")
        x += adv + gap
    return img.resize((w, h), Image.Resampling.LANCZOS)


def main():
    print("banner:")
    bg = scene(304, 228)
    dither565(bg).save(ROOT / "banner_BG.png")
    print(f"  banner_BG.png: 304x228 (pane 608x456, dithered for RGB565)")

    # top band: bubbles rising, tinted pale cyan by the layout
    W1 = 614
    res = seamless_band(W1, 48, [
        (bubble(30), 34, 27), (bubble(17), 88, 13),
        (dolphin(20, -7), 168, 24), (bubble(15), 246, 15),
        (fish(13, True), 296, 31), (bubble(26), 356, 26),
        (dolphin(17, 6, True), 448, 25), (bubble(16), 528, 14),
        (fish(12), 570, 30), (bubble(22), 610, 28),
    ])
    ia_png(res, ROOT / "banner_sil_res.png")

    # bottom band: a pod cruising past, tinted light grey
    spo = seamless_band(W1, 48, [
        (cloud(17), 70, 22), (cloud(11, True), 196, 28), (cloud(20), 330, 20),
        (cloud(9), 436, 30), (cloud(14, True), 528, 24),
    ])
    ia_png(spo, ROOT / "banner_sil_spo.png")

    wordmark(496, 169).save(ROOT / "banner_logo.png")
    print("  banner_logo.png: 496x169")

    print("icon:")
    icon_bg = scene(170, 96)
    icon_bg.convert("RGBA").save(ROOT / "menubnr_BG.png")
    print("  menubnr_BG.png: 170x96 (pane 170x96, was 2x96)")

    wordmark(120, 48, fit=0.80).save(ROOT / "menubnr_logo.png")
    print("  menubnr_logo.png: 120x48")

    ia_png(seamless_band(116, 32, [
        (bubble(17), 20, 20), (dolphin(12, -6), 62, 17), (bubble(10), 100, 11),
    ]), ROOT / "menubnr_sil_res.png")
    ia_png(seamless_band(120, 32, [
        (cloud(11), 28, 15), (cloud(8, True), 84, 19),
    ]), ROOT / "menubnr_sil_spo.png")


if __name__ == "__main__":
    main()
