#!/usr/bin/env python3
"""Compose the Kids channel banner jingle and encode it as a BNS.

An original piece, not a Sonic track. The channel ships in a public
release, so bundling somebody else's recording is not on the table; this
is written here in the same idiom — 16-bit console voices, bright major
key, fast shuffle — so it sits next to the ones it is meant to evoke.

Voices are period-appropriate rather than sampled: a pulse lead, a second
pulse a sixth under it, a saw bass on straight eighths, and noise-based
hats and snare with a sine kick. Rendered to stereo 32kHz, then encoded
DSP-ADPCM to match the BNS the banner already carries (codec 0, channels
stored sequentially, loop disabled).
"""
from __future__ import annotations

import math
import struct
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import dspadpcm  # noqa: E402

RATE = 32000
BPM = 160.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
BARS = 4

# A major. Semitone offsets from A3 (220 Hz).
A3 = 220.0


def hz(semi):
    return A3 * (2.0 ** (semi / 12.0))


# (start_beat, length_beats, semitone). Four bars, a bright rising hook
# that answers itself, then lifts an octave on the last bar.
LEAD = [
    (0.0, 0.5, 12), (0.5, 0.5, 16), (1.0, 0.5, 19), (1.5, 0.5, 16),
    (2.0, 1.0, 21), (3.0, 0.5, 19), (3.5, 0.5, 16),
    (4.0, 0.5, 14), (4.5, 0.5, 17), (5.0, 0.5, 21), (5.5, 0.5, 17),
    (6.0, 1.5, 19), (7.5, 0.5, 21),
    (8.0, 0.5, 24), (8.5, 0.5, 21), (9.0, 0.5, 19), (9.5, 0.5, 16),
    (10.0, 1.0, 17), (11.0, 0.5, 19), (11.5, 0.5, 21),
    (12.0, 0.75, 24), (12.75, 0.25, 26), (13.0, 0.5, 28),
    (13.5, 0.5, 26), (14.0, 2.0, 24),
]
HARMONY = [(s, l, n - 9) for s, l, n in LEAD]
BASS = [
    (0.0, 9), (0.5, 9), (1.0, 9), (1.5, 9), (2.0, 9), (2.5, 9), (3.0, 9), (3.5, 9),
    (4.0, 5), (4.5, 5), (5.0, 5), (5.5, 5), (6.0, 7), (6.5, 7), (7.0, 7), (7.5, 7),
    (8.0, 4), (8.5, 4), (9.0, 4), (9.5, 4), (10.0, 2), (10.5, 2), (11.0, 2), (11.5, 2),
    (12.0, 5), (12.5, 5), (13.0, 7), (13.5, 7), (14.0, 9), (14.5, 9), (15.0, 9), (15.5, 9),
]


def env(i, n, attack, release):
    a = max(1, int(n * attack))
    r = max(1, int(n * release))
    if i < a:
        return i / a
    if i > n - r:
        return max(0.0, (n - i) / r)
    return 1.0


def render():
    total = int(BARS * BAR * RATE)
    left = [0.0] * total
    right = [0.0] * total

    def add(buf, start, samples, gain):
        for k, v in enumerate(samples):
            j = start + k
            if 0 <= j < total:
                buf[j] += v * gain

    # pulse lead + harmony
    for notes, duty, gain, panL, panR, vib in (
        (LEAD, 0.25, 0.30, 0.42, 0.58, 5.5),
        (HARMONY, 0.50, 0.16, 0.60, 0.40, 4.0),
    ):
        for start_b, len_b, semi in notes:
            n = int(len_b * BEAT * RATE * 0.94)
            s0 = int(start_b * BEAT * RATE)
            f = hz(semi)
            buf = []
            ph = 0.0
            for i in range(n):
                t = i / RATE
                fm = f * (1.0 + 0.006 * math.sin(2 * math.pi * vib * t))
                ph += fm / RATE
                v = 1.0 if (ph % 1.0) < duty else -1.0
                buf.append(v * env(i, n, 0.02, 0.25))
            add(left, s0, buf, gain * panL)
            add(right, s0, buf, gain * panR)

    # saw bass, centre
    for start_b, semi in BASS:
        n = int(0.5 * BEAT * RATE * 0.9)
        s0 = int(start_b * BEAT * RATE)
        f = hz(semi - 12)
        buf = []
        for i in range(n):
            ph = (f * i / RATE) % 1.0
            buf.append((2.0 * ph - 1.0) * env(i, n, 0.01, 0.35))
        add(left, s0, buf, 0.26)
        add(right, s0, buf, 0.26)

    # drums
    seed = 0x1234

    def noise():
        nonlocal seed
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        return (seed / 0x3FFFFFFF) - 1.0

    for b in range(int(BARS * 4 * 2)):
        beat = b * 0.5
        s0 = int(beat * BEAT * RATE)
        # closed hat every eighth
        n = int(0.045 * RATE)
        buf = [noise() * env(i, n, 0.005, 0.9) for i in range(n)]
        add(left, s0, buf, 0.055)
        add(right, s0, buf, 0.055)
        if b % 4 == 0:  # kick on 1 and 3
            n = int(0.13 * RATE)
            buf = []
            for i in range(n):
                t = i / RATE
                f = 110.0 * math.exp(-t * 22.0) + 42.0
                buf.append(math.sin(2 * math.pi * f * t) * math.exp(-t * 13.0))
            add(left, s0, buf, 0.55)
            add(right, s0, buf, 0.55)
        if b % 4 == 2:  # snare on 2 and 4
            n = int(0.11 * RATE)
            buf = [(noise() * 0.8 + math.sin(2 * math.pi * 190 * i / RATE) * 0.35)
                   * math.exp(-i / RATE * 26.0) for i in range(n)]
            add(left, s0, buf, 0.30)
            add(right, s0, buf, 0.30)

    def finish(buf):
        peak = max(abs(v) for v in buf) or 1.0
        g = 0.89 / peak
        out = []
        for v in buf:
            x = v * g
            # soft knee so the pulse stack does not clip harshly
            x = math.tanh(x * 1.18) / math.tanh(1.18)
            out.append(int(max(-32768, min(32767, round(x * 32767)))))
        # trim to a whole ADPCM frame
        n = len(out) // dspadpcm.SAMPLES_PER_FRAME * dspadpcm.SAMPLES_PER_FRAME
        return out[:n]

    return finish(left), finish(right)


def build_bns(l_pcm, r_pcm):
    enc_l, coefs = dspadpcm.encode(l_pcm)
    enc_r, _ = dspadpcm.encode(r_pcm)
    assert len(enc_l) == len(enc_r)

    # verify the encoder against its own decoder before shipping it
    for name, pcm, enc in (("L", l_pcm, enc_l), ("R", r_pcm, enc_r)):
        back = dspadpcm.decode(enc, coefs, len(pcm))
        print(f"  {name}: {dspadpcm.snr_db(pcm, back):.1f} dB SNR over {len(pcm)} samples")

    samples = len(l_pcm)
    half = len(enc_l)

    info = bytearray(0xA0)
    info[0:4] = b"INFO"
    struct.pack_into(">I", info, 4, 0xA0)
    info[8] = 0          # codec 0 = DSP-ADPCM
    info[9] = 0          # loop disabled, as shipped
    info[10] = 2         # channels
    struct.pack_into(">H", info, 12, RATE)
    struct.pack_into(">I", info, 16, 0)        # loop start
    struct.pack_into(">I", info, 20, samples)
    struct.pack_into(">I", info, 24, 0x18)     # channel table, relative to +8
    struct.pack_into(">I", info, 32, 0x20)     # chan0 entry
    struct.pack_into(">I", info, 36, 0x2C)     # chan1 entry
    struct.pack_into(">I", info, 40, 0)        # chan0 data offset
    struct.pack_into(">I", info, 44, 0x38)     # chan0 adpcm info
    struct.pack_into(">I", info, 52, half)     # chan1 data offset
    struct.pack_into(">I", info, 56, 0x68)     # chan1 adpcm info
    for base in (0x40, 0x70):
        for i, c in enumerate(coefs):
            struct.pack_into(">h", info, base + i * 2, c)

    data = bytearray(b"DATA" + struct.pack(">I", 8 + half * 2) + enc_l + enc_r)
    bns = bytearray()
    bns += b"BNS " + struct.pack(">I", 0xFEFF0100)
    bns += struct.pack(">I", 0x20 + len(info) + len(data))
    bns += struct.pack(">HH", 0x20, 2)
    bns += struct.pack(">II", 0x20, len(info))
    bns += struct.pack(">II", 0x20 + len(info), len(data))
    assert len(bns) == 0x20, len(bns)
    bns += info + data

    import hashlib
    payload = bytes(bns)
    return b"IMD5" + struct.pack(">I", len(payload)) + b"\0" * 8 + \
        hashlib.md5(payload).digest() + payload


def main():
    print(f"rendering {BARS} bars at {BPM:g} BPM ({BARS * BAR:.2f}s)")
    l_pcm, r_pcm = render()
    print(f"  {len(l_pcm)} samples/channel at {RATE} Hz")
    blob = build_bns(l_pcm, r_pcm)
    out = ROOT / "sound.bin"
    out.write_bytes(blob)
    print(f"  wrote {out} ({len(blob)} bytes)")


if __name__ == "__main__":
    main()
