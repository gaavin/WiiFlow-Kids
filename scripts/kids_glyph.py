#!/usr/bin/env python3
"""Kids UI button glyphs: the Wii Remote's A and B keys.

The stock hint drew a black rounded square with a green A, which is an
Xbox convention. The Wii Remote's A is a round, slightly domed light key
with dark grey lettering, so this draws that instead — given the Frutiger
Aero treatment the rest of the theme uses: a glass dome with a bright
upper shelf, a cool bounce along the bottom and a white rim. B is the
same key with a B, so PLAY and BACK carry a matching pair.

Authored at 128px for a 52px (main hint) / 40px (PLAY/BACK) slot so the
GPU downsamples it, and compiled into the dol by bin2s alongside the splash.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "data" / "images"
FONT = ROOT / "out" / "imgs" / "font.ttf"

W = 128
S = 4
SW = W * S


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


def wii_letter(letter: str) -> Image.Image:
    img = Image.new("RGBA", (SW, SW), (0, 0, 0, 0))
    c = SW / 2
    r = SW * 0.425

    # contact shadow, so the key sits on the background rather than floating
    sh = Image.new("RGBA", (SW, SW), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([c - r, c - r + r * 0.10, c + r, c + r + r * 0.13],
                               fill=(8, 34, 62, 120))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(SW * 0.022)))

    # key face: near-white crown falling to a cool grey base
    disc = Image.new("L", (SW, SW), 0)
    ImageDraw.Draw(disc).ellipse([c - r, c - r, c + r, c + r], fill=255)
    disc = disc.filter(ImageFilter.GaussianBlur(SW * 0.004))
    face = Image.new("RGBA", (SW, SW), (0, 0, 0, 0))
    face.paste(vgrad((SW, SW), [
        (0.00, (255, 255, 255)), (0.30, (246, 250, 253)), (0.52, (216, 228, 238)),
        (0.74, (188, 204, 219)), (1.00, (214, 228, 240)),
    ]), (0, 0))
    face.putalpha(disc)
    img.alpha_composite(face)

    # glass shelf across the top half
    shelf = Image.new("RGBA", (SW, SW), (0, 0, 0, 0))
    ImageDraw.Draw(shelf).ellipse([c - r * 0.80, c - r * 0.86, c + r * 0.80, c + r * 0.10],
                                  fill=(255, 255, 255, 175))
    shelf.putalpha(Image.composite(shelf.getchannel("A"), Image.new("L", (SW, SW), 0), disc))
    img.alpha_composite(shelf.filter(ImageFilter.GaussianBlur(SW * 0.028)))

    # cool bounce along the bottom rim
    bounce = Image.new("RGBA", (SW, SW), (0, 0, 0, 0))
    ImageDraw.Draw(bounce).ellipse([c - r * 0.74, c + r * 0.30, c + r * 0.74, c + r * 0.94],
                                   fill=(150, 205, 240, 130))
    bounce.putalpha(Image.composite(bounce.getchannel("A"), Image.new("L", (SW, SW), 0), disc))
    img.alpha_composite(bounce.filter(ImageFilter.GaussianBlur(SW * 0.030)))

    # white rim
    rim = Image.new("RGBA", (SW, SW), (0, 0, 0, 0))
    ImageDraw.Draw(rim).ellipse([c - r, c - r, c + r, c + r],
                                outline=(255, 255, 255, 235), width=int(SW * 0.022))
    img.alpha_composite(rim.filter(ImageFilter.GaussianBlur(SW * 0.003)))

    # the letter, in the dark navy the rest of the UI uses for ink
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(str(FONT), int(SW * 0.50))
    d.text((c, c + SW * 0.012), letter, font=f, fill=(27, 46, 70, 255), anchor="mm")

    return img.resize((W, W), Image.Resampling.LANCZOS)


def main():
    IMG.mkdir(parents=True, exist_ok=True)
    for letter, name in (("A", "a_button.png"), ("B", "b_button.png")):
        out = IMG / name
        wii_letter(letter).save(out, optimize=True)
        print("wrote", out, f"{W}x{W}")


if __name__ == "__main__":
    main()
