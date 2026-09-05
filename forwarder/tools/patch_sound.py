#!/usr/bin/env python3
"""Swap only the DATA payload of the stock banner BNS.

Authoring a BNS from scratch produced a file whose header is byte-identical
to Nintendo's apart from sample count, channel offset and coefficients, and
whose ADPCM decodes correctly under the exact hardware formula — yet the
console played nothing. Rather than keep guessing at the container, this
keeps the stock INFO chunk verbatim, including its own coefficient banks
and sample count, and replaces just the encoded audio. Everything the
System Menu parses is then unchanged from the file that already worked.
"""
from __future__ import annotations

import hashlib
import struct
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import dspadpcm  # noqa: E402
import make_music  # noqa: E402

STOCK = Path("/tmp/wf/sound.bin")


def main():
    stock = STOCK.read_bytes()
    bns = stock[0x20:]
    io, isz, do_, dsz = struct.unpack(">IIII", bns[0x10:0x20])
    info = bns[io:io + isz]
    total = struct.unpack(">I", info[20:24])[0]
    c1 = struct.unpack(">I", info[52:56])[0]
    cf0 = [struct.unpack(">h", info[0x40 + k * 2:0x42 + k * 2])[0] for k in range(16)]
    cf1 = [struct.unpack(">h", info[0x70 + k * 2:0x72 + k * 2])[0] for k in range(16)]
    print(f"stock: {total} samples/channel, {c1} bytes/channel")

    L, R = make_music.render()

    def fit(pcm):
        pcm = list(pcm)
        if len(pcm) < total:
            pcm += [0] * (total - len(pcm))
        return pcm[:total]

    L, R = fit(L), fit(R)
    bank0 = [(cf0[i * 2], cf0[i * 2 + 1]) for i in range(8)]
    bank1 = [(cf1[i * 2], cf1[i * 2 + 1]) for i in range(8)]
    enc_l, _ = dspadpcm.encode(L, bank0)
    enc_r, _ = dspadpcm.encode(R, bank1)
    for nm, pcm, enc, cf in (("L", L, enc_l, cf0), ("R", R, enc_r, cf1)):
        back = dspadpcm.decode(enc, cf, len(pcm))
        print(f"  {nm}: {dspadpcm.snr_db(pcm, back):.1f} dB, {len(enc)} bytes (stock {c1})")
    assert len(enc_l) == len(enc_r) == c1, (len(enc_l), len(enc_r), c1)

    payload = bytearray(bns)
    base = do_ + 8
    payload[base:base + c1] = enc_l
    payload[base + c1:base + 2 * c1] = enc_r
    out = bytes(payload)
    assert len(out) == len(bns)
    blob = b"IMD5" + struct.pack(">I", len(out)) + b"\0" * 8 + hashlib.md5(out).digest() + out
    assert len(blob) == len(stock), (len(blob), len(stock))
    (ROOT / "sound.bin").write_bytes(blob)
    print(f"  wrote sound.bin, {len(blob)} bytes, INFO chunk untouched")
    print(f"  INFO identical to stock: {out[io:io+isz] == info}")


if __name__ == "__main__":
    main()
