"""Nintendo DSP-ADPCM codec, enough of it to author a banner sound.

The Wii banner's sound.bin is a BNS holding codec 0 — DSP-ADPCM — so a
replacement track has to be encoded in it. Frames are 8 bytes: one header
byte carrying a predictor index and a scale, then 14 samples as signed
4-bit residuals against a second-order predictor.

The coefficients live in the BNS header, so the decoder uses whatever the
encoder chose. That means a fixed, well-conditioned predictor bank plus a
per-frame search is entirely valid, and much less delicate than deriving
coefficients by autocorrelation. Quality is checked by decoding the
encoder's own output and measuring SNR against the source, the same
round-trip discipline the LZ codec in this directory already uses.
"""
from __future__ import annotations

import struct

# Q11 second-order predictors: (a1, a2), reconstruction is
#   (a1*yn1 + a2*yn2) >> 11  plus the scaled residual.
# A spread from "no prediction" through delta to linear extrapolation, so
# the per-frame search has something suitable for both flat and steep runs.
COEFS = [
    (0, 0),
    (2048, 0),
    (0, 2048),
    (1024, 1024),
    (4096, -2048),
    (3072, -1024),
    (3584, -1536),
    (2560, -512),
]

SAMPLES_PER_FRAME = 14
BYTES_PER_FRAME = 8


def _clamp16(v):
    return -32768 if v < -32768 else (32767 if v > 32767 else v)


def _clamp4(v):
    return -8 if v < -8 else (7 if v > 7 else v)


def encode(pcm, bank=None):
    """pcm: list of int16. Returns (frames_bytes, flat_coef_list).

    bank overrides the built-in predictors, so a stream can be encoded
    against coefficients that already live in a known-good header.
    """
    table = bank if bank is not None else COEFS
    out = bytearray()
    yn1 = yn2 = 0
    n = len(pcm)
    for base in range(0, n, SAMPLES_PER_FRAME):
        block = list(pcm[base:base + SAMPLES_PER_FRAME])
        block += [0] * (SAMPLES_PER_FRAME - len(block))

        best = None
        for pi, (a1, a2) in enumerate(table):
            # smallest scale that keeps every residual inside 4 bits
            scale = 0
            while scale < 16:
                ok = True
                s1, s2 = yn1, yn2
                for s in block:
                    pred = (a1 * s1 + a2 * s2) >> 11
                    diff = s - pred
                    step = 1 << scale
                    q = int(round(diff / step))
                    if q < -8 or q > 7:
                        ok = False
                        break
                    rec = _clamp16(pred + q * step)
                    s2, s1 = s1, rec
                if ok:
                    break
                scale += 1
            if scale >= 16:
                continue

            # measure this candidate honestly, on reconstructed output
            err = 0
            s1, s2 = yn1, yn2
            nib = []
            for s in block:
                pred = (a1 * s1 + a2 * s2) >> 11
                step = 1 << scale
                q = _clamp4(int(round((s - pred) / step)))
                rec = _clamp16(pred + q * step)
                err += (s - rec) * (s - rec)
                nib.append(q & 0xF)
                s2, s1 = s1, rec
            if best is None or err < best[0]:
                best = (err, pi, scale, nib, s1, s2)

        if best is None:
            # nothing fit even at scale 15; fall back to the flattest predictor
            best = (0, 0, 15, [0] * SAMPLES_PER_FRAME, yn1, yn2)

        _, pi, scale, nib, yn1, yn2 = best
        out.append((pi << 4) | scale)
        for k in range(0, SAMPLES_PER_FRAME, 2):
            out.append((nib[k] << 4) | nib[k + 1])
    return bytes(out), [c for pair in table for c in pair]


def decode(data, coefs, count):
    """Mirror of the hardware decoder, used to verify the encoder."""
    out = []
    yn1 = yn2 = 0
    for off in range(0, len(data), BYTES_PER_FRAME):
        hdr = data[off]
        pi, scale = hdr >> 4, hdr & 0xF
        a1, a2 = coefs[pi * 2], coefs[pi * 2 + 1]
        step = 1 << scale
        for k in range(SAMPLES_PER_FRAME):
            byte = data[off + 1 + k // 2]
            q = (byte >> 4) if k % 2 == 0 else (byte & 0xF)
            if q > 7:
                q -= 16
            rec = _clamp16(((a1 * yn1 + a2 * yn2) >> 11) + q * step)
            out.append(rec)
            yn2, yn1 = yn1, rec
            if len(out) >= count:
                return out
    return out


def snr_db(ref, got):
    import math
    n = min(len(ref), len(got))
    sig = sum(float(ref[i]) ** 2 for i in range(n))
    noise = sum((float(ref[i]) - got[i]) ** 2 for i in range(n))
    if noise == 0:
        return float("inf")
    return 10.0 * math.log10(sig / noise) if sig else 0.0
