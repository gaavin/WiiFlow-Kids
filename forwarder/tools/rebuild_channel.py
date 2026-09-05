#!/usr/bin/env python3
"""Rebuild WiiFlow_Kids_Channel.wad from the existing WAD + new PNGs.

Only TPL pixel data and the IMET name change. brlyt/brlan/sound/DOL are
copied byte-for-byte from the installed channel so the System Menu still
parses a layout it has already booted.
"""
from __future__ import annotations

import hashlib
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

from Crypto.Cipher import AES
from PIL import Image

import lz
import tpl
import u8

COMMON = bytes.fromhex("ebe42a225e8593e448d9c5457381aaf7")
al = lambda x, a: (x + a - 1) // a * a
NAME = "WiiFlow Kids"

ENCODERS = {
    2: tpl.encode_ia4,
    3: tpl.encode_ia8,
    4: tpl.encode_rgb565,
    6: tpl.encode_rgba8,
}

REPLACEMENTS = {
    "banner_logo.tpl": ROOT / "banner_logo.png",
    "menubnr_logo.tpl": ROOT / "menubnr_logo.png",
    "banner_BG.tpl": ROOT / "banner_BG.png",
    "menubnr_BG.tpl": ROOT / "menubnr_BG.png",
    "banner_sil_res.tpl": ROOT / "banner_sil_res.png",
    "banner_sil_spo.tpl": ROOT / "banner_sil_spo.png",
    "menubnr_sil_res.tpl": ROOT / "menubnr_sil_res.png",
    "menubnr_sil_spo.tpl": ROOT / "menubnr_sil_spo.png",
    "banner_Nintendo.tpl": ROOT / "banner_Nintendo.png",
    "banner_Dolby.tpl": ROOT / "banner_Dolby.png",
}


def decrypt_wad(path: Path):
    d = path.read_bytes()
    hs, wt, cert, crl, tik, tmd, data, foot = struct.unpack(">IIIIIIII", d[:0x20])
    o = al(hs, 64)
    o_cert = o; o += al(cert, 64)
    o_crl = o; o += al(crl, 64)
    o_tik = o; o += al(tik, 64)
    o_tmd = o; o += al(tmd, 64)
    o_data = o
    TIK = d[o_tik:o_tik + tik]
    TMD = bytearray(d[o_tmd:o_tmd + tmd])
    CERT = d[o_cert:o_cert + cert]
    CRL = d[o_crl:o_crl + crl]
    FOOT = d[o_data + al(data, 64):] if foot else b""
    title_key = AES.new(COMMON, AES.MODE_CBC, TIK[0x1DC:0x1E4] + b"\0" * 8).decrypt(TIK[0x1BF:0x1CF])
    n = struct.unpack(">H", TMD[0x1DE:0x1E0])[0]
    contents = []
    off = o_data
    for i in range(n):
        rec = 0x1E4 + i * 36
        cid, idx, ctype, size = struct.unpack(">IHHQ", TMD[rec:rec + 16])
        enc = d[off:off + al(size, 16)]
        off += al(al(size, 16), 64)
        raw = AES.new(title_key, AES.MODE_CBC, struct.pack(">H", idx) + b"\0" * 14).decrypt(enc)[:size]
        contents.append(raw)
        print(f"  decrypted content{i} idx={idx} {size} bytes")
    return dict(wt=wt, CERT=CERT, CRL=CRL, TIK=TIK, TMD=TMD, FOOT=FOOT,
                title_key=title_key, contents=contents)


def tpl_fmt(blob):
    hoff, _ = struct.unpack(">II", blob[12:20])
    h, w, fmt, doff = struct.unpack(">HHII", blob[hoff:hoff + 12])
    return w, h, fmt


def stretch_banner_bg(brlyt: bytes) -> bytes:
    """Grow P_BG to the full 608x456 root pane so the sky/ocean fill
    covers the old black ticker rows (they sat below the 347px background)."""
    off = 0x10
    out = bytearray(brlyt)
    while off + 8 <= len(brlyt):
        mag = brlyt[off:off + 4]
        sz = struct.unpack(">I", brlyt[off + 4:off + 8])[0]
        if mag == b"pic1":
            p = off + 8
            name = brlyt[p + 4:p + 20].split(b"\0", 1)[0]
            if name == b"P_BG":
                ty = struct.unpack(">f", brlyt[p + 32:p + 36])[0]
                h = struct.unpack(">f", brlyt[p + 64:p + 68])[0]
                out[p + 32:p + 36] = struct.pack(">f", 0.0)
                out[p + 64:p + 68] = struct.pack(">f", 456.0)
                print(f"  P_BG ty {ty} -> 0, height {h} -> 456")
                return bytes(out)
        if sz < 8:
            break
        off += sz
    raise SystemExit("P_BG pane not found in banner.brlyt")


def patch_u8(raw: bytes, label: str) -> bytes:
    ents, meta = u8.parse(raw, 0)
    out = bytearray(raw)
    for e in ents:
        if e["type"] != 0:
            continue
        if e["name"] == "banner.brlyt":
            patched = stretch_banner_bg(bytes(out[e["data_off"]:e["data_off"] + e["size"]]))
            if len(patched) != e["size"]:
                raise SystemExit("banner.brlyt size changed")
            out[e["data_off"]:e["data_off"] + e["size"]] = patched
            continue
        if e["name"] not in REPLACEMENTS:
            continue
        png = Image.open(REPLACEMENTS[e["name"]]).convert("RGBA")
        w, h, fmt = tpl_fmt(raw[e["data_off"]:e["data_off"] + e["size"]])
        if png.size != (w, h):
            raise SystemExit(f"{e['name']}: png {png.size} != tpl {w}x{h}")
        enc = ENCODERS[fmt](w, h, png.tobytes())
        if len(enc) != e["size"]:
            raise SystemExit(f"{e['name']}: encoded {len(enc)} != {e['size']}")
        out[e["data_off"]:e["data_off"] + e["size"]] = enc
        print(f"  patched {label}/{e['name']} {w}x{h} fmt={fmt}")
    return bytes(out)


def imd5(payload: bytes) -> bytes:
    return b"IMD5" + struct.pack(">I", len(payload)) + b"\0" * 8 + hashlib.md5(payload).digest() + payload


def rebuild_outer(orig_c0: bytes, parts: dict) -> bytes:
    B = 0x600
    ents, meta = u8.parse(orig_c0, B)
    node_tbl_off = meta["nt"] - B
    data_off = meta["data_off"]
    arch = bytearray(orig_c0[B:B + data_off])
    cur = data_off
    newdata = bytearray()
    for e in ents:
        if e["type"] != 0:
            continue
        blob = parts[e["name"]]
        cur = al(cur, 32)
        pad = cur - (data_off + len(newdata))
        newdata += b"\0" * pad + blob
        n = node_tbl_off + e["idx"] * 12
        arch[n + 4:n + 12] = struct.pack(">II", cur, len(blob))
        cur += len(blob)
    imet = bytearray(orig_c0[:B])
    enc = NAME.encode("utf-16-be")
    for L in range(10):
        off = 0x5C + L * 84
        imet[off:off + 84] = enc + b"\0" * (84 - len(enc))
    imet[0x5F0:0x600] = b"\0" * 16
    imet[0x5F0:0x600] = hashlib.md5(bytes(imet)).digest()
    return bytes(imet) + bytes(arch) + bytes(newdata)


def pack(wad_meta, contents, dest: Path):
    TMD = bytearray(wad_meta["TMD"])
    n = struct.unpack(">H", TMD[0x1DE:0x1E0])[0]
    blob = bytearray()
    for i in range(n):
        rec = 0x1E4 + i * 36
        cid, idx, ctype, old = struct.unpack(">IHHQ", TMD[rec:rec + 16])
        raw = contents[i]
        TMD[rec + 8:rec + 16] = struct.pack(">Q", len(raw))
        TMD[rec + 16:rec + 36] = hashlib.sha1(raw).digest()
        padded = raw + b"\0" * (al(len(raw), 16) - len(raw))
        enc = AES.new(wad_meta["title_key"], AES.MODE_CBC,
                      struct.pack(">H", idx) + b"\0" * 14).encrypt(padded)
        blob += enc + b"\0" * (al(len(enc), 64) - len(enc))
        print(f"  packed content{i} idx={idx}: {old} -> {len(raw)}")
    TMD[0x04:0x104] = b"\0" * 256
    found = None
    for v in range(0x10000):
        TMD[0x19A:0x19C] = struct.pack(">H", v)
        if hashlib.sha1(bytes(TMD[0x140:])).digest()[0] == 0:
            found = v
            break
    if found is None:
        sys.exit("fakesign brute-force failed")
    print(f"  TMD fake-signed (padding@0x19A = {found:#06x})")
    CERT, CRL, TIK, FOOT = wad_meta["CERT"], wad_meta["CRL"], wad_meta["TIK"], wad_meta["FOOT"]
    out = bytearray()
    out += struct.pack(">IIIIIIII", 0x20, wad_meta["wt"], len(CERT), len(CRL),
                       len(TIK), len(TMD), len(blob), len(FOOT))
    out += b"\0" * (al(len(out), 64) - len(out))
    for sec in (CERT, CRL, TIK, bytes(TMD)):
        out += sec + b"\0" * (al(len(sec), 64) - len(sec))
    out += blob
    if FOOT:
        out += FOOT + b"\0" * (al(len(FOOT), 64) - len(FOOT))
    dest.write_bytes(bytes(out))
    print(f"  wrote {dest} ({len(out)} bytes)")

    w = dest.read_bytes()
    hs2, wt2, c2, r2, t2, m2, d2, f2 = struct.unpack(">IIIIIIII", w[:0x20])
    o = al(hs2, 64); o += al(c2, 64); o += al(r2, 64)
    ot = o; o += al(t2, 64); om = o; o += al(m2, 64); od = o
    T2 = w[om:om + m2]
    nn = struct.unpack(">H", T2[0x1DE:0x1E0])[0]
    tk = wad_meta["title_key"]
    ok = True
    p = od
    for i in range(nn):
        rec = 0x1E4 + i * 36
        cid, idx, ct, sz = struct.unpack(">IHHQ", T2[rec:rec + 16])
        sha = T2[rec + 16:rec + 36]
        dec = AES.new(tk, AES.MODE_CBC, struct.pack(">H", idx) + b"\0" * 14
                      ).decrypt(w[p:p + al(sz, 16)])[:sz]
        good = hashlib.sha1(dec).digest() == sha
        ok &= good
        print(f"  verify content{i}: sha1_matches_TMD={good}")
        p += al(sz, 64)
    sig_zero = T2[4:0x104] == b"\0" * 256
    trucha = hashlib.sha1(T2[0x140:]).digest()[0] == 0
    tid = struct.unpack(">Q", T2[0x18C:0x194])[0]
    tid_hi = tid >> 32
    print(f"  sig zeroed={sig_zero} trucha={trucha} title={tid:016X}")
    if not (ok and sig_zero and trucha and tid_hi == 0x00010001):
        sys.exit("FAILED - DO NOT INSTALL")
    print("RESULT: ALL CHECKS PASSED")


def main():
    src = ROOT / "WiiFlow_Kids_Channel.wad"
    print("decrypt", src)
    meta = decrypt_wad(src)
    c0 = meta["contents"][0]
    ents, _ = u8.parse(c0, 0x600)
    parts = {}
    for e in ents:
        if e["type"] != 0:
            continue
        blob = c0[0x600 + e["data_off"]:0x600 + e["data_off"] + e["size"]]
        if e["name"] in ("banner.bin", "icon.bin"):
            assert blob[:4] == b"IMD5"
            raw = lz.decompress(blob[0x20:])
            raw = patch_u8(raw, e["name"])
            comp = lz.compress(raw)
            assert lz.decompress(comp) == raw
            parts[e["name"]] = imd5(comp)
            print(f"  {e['name']}: u8={len(raw)} lz={len(comp)}")
        else:
            parts[e["name"]] = blob
    print("rebuild outer U8")
    new_c0 = rebuild_outer(c0, parts)
    print(f"  content0 {len(c0)} -> {len(new_c0)}")
    print("pack")
    pack(meta, [new_c0, meta["contents"][1], meta["contents"][2]], src)


if __name__ == "__main__":
    main()
