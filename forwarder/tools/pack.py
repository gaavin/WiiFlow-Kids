#!/usr/bin/env python3
"""
Pack the WiiFlow Kids channel WAD.

Takes the retextured banner content (c0.new, already built and verified) plus
the untouched contents 1 and 2 from the original forwarder, re-encrypts them,
updates and fake-signs the TMD, and writes WiiFlow_Kids_Channel.wad.

Everything structural in the banner - banner.brlyt, banner_Start.brlan,
banner_Loop.brlan, icon.brlyt, icon.brlan and sound.bin - is byte-for-byte the
original, field-tested data. Only two RGBA8 textures and the IMET channel name
were changed.

Run:  nix-shell -p python3Packages.pycryptodome --run "python3 pack.py"
"""
import struct, hashlib, sys
from Crypto.Cipher import AES

COMMON = bytes.fromhex('ebe42a225e8593e448d9c5457381aaf7')   # Wii common key
al = lambda x, a: (x + a - 1) // a * a

d = open('base.wad', 'rb').read()
hs, wt, cert, crl, tik, tmd, data, foot = struct.unpack('>IIIIIIII', d[:0x20])

o = al(hs, 64)
o_cert = o; o += al(cert, 64)
o_crl  = o; o += al(crl, 64)
o_tik  = o; o += al(tik, 64)
o_tmd  = o; o += al(tmd, 64)
o_data = o; o_foot = o_data + al(data, 64)

CERT = d[o_cert:o_cert + cert]
CRL  = d[o_crl:o_crl + crl]
TIK  = d[o_tik:o_tik + tik]
TMD  = bytearray(d[o_tmd:o_tmd + tmd])
FOOT = d[o_foot:o_foot + foot] if foot else b''

title_key = AES.new(COMMON, AES.MODE_CBC,
                    TIK[0x1DC:0x1E4] + b'\0' * 8).decrypt(TIK[0x1BF:0x1CF])
n = struct.unpack('>H', TMD[0x1DE:0x1E0])[0]

print("packing contents")
contents = [open('c0.new', 'rb').read(),
            open('c1.bin', 'rb').read(),
            open('c2.bin', 'rb').read()]

blob = bytearray()
for i in range(n):
    rec = 0x1E4 + i * 36
    cid, idx, ctype, old = struct.unpack('>IHHQ', TMD[rec:rec + 16])
    raw = contents[i]
    TMD[rec + 8:rec + 16]  = struct.pack('>Q', len(raw))
    TMD[rec + 16:rec + 36] = hashlib.sha1(raw).digest()
    padded = raw + b'\0' * (al(len(raw), 16) - len(raw))
    enc = AES.new(title_key, AES.MODE_CBC,
                  struct.pack('>H', idx) + b'\0' * 14).encrypt(padded)
    blob += enc + b'\0' * (al(len(enc), 64) - len(enc))
    print(f"  content{i} idx={idx}: {old} -> {len(raw)} bytes")

# Fake-sign the TMD: zero the RSA signature, then brute-force the 2 padding
# bytes at 0x19A until SHA1 of the signed region starts with 0x00 (trucha).
TMD[0x04:0x104] = b'\0' * 256
found = None
for v in range(0x10000):
    TMD[0x19A:0x19C] = struct.pack('>H', v)
    if hashlib.sha1(bytes(TMD[0x140:])).digest()[0] == 0:
        found = v
        break
if found is None:
    sys.exit("fakesign brute-force failed")
print(f"  TMD fake-signed (padding@0x19A = {found:#06x})")

out = bytearray()
out += struct.pack('>IIIIIIII', 0x20, wt, len(CERT), len(CRL),
                   len(TIK), len(TMD), len(blob), len(FOOT))
out += b'\0' * (al(len(out), 64) - len(out))
for sec in (CERT, CRL, TIK, bytes(TMD)):
    out += sec + b'\0' * (al(len(sec), 64) - len(sec))
out += blob
if FOOT:
    out += FOOT + b'\0' * (al(len(FOOT), 64) - len(FOOT))

open('WiiFlow_Kids_Channel.wad', 'wb').write(bytes(out))
print(f"  wrote WiiFlow_Kids_Channel.wad ({len(out)} bytes)")

# ---------------------------------------------------------------- verify ----
print("\nverifying the packed WAD from scratch")
w = open('WiiFlow_Kids_Channel.wad', 'rb').read()
hs2, wt2, c2, r2, t2, m2, d2, f2 = struct.unpack('>IIIIIIII', w[:0x20])
o = al(hs2, 64); oc = o; o += al(c2, 64); o += al(r2, 64)
ot = o; o += al(t2, 64); om = o; o += al(m2, 64); od = o
T2 = w[om:om + m2]
tid = struct.unpack('>Q', T2[0x18C:0x194])[0]
ios = struct.unpack('>Q', T2[0x184:0x18C])[0] & 0xFFFFFFFF
nn = struct.unpack('>H', T2[0x1DE:0x1E0])[0]
tk = AES.new(COMMON, AES.MODE_CBC,
             w[ot:ot + t2][0x1DC:0x1E4] + b'\0' * 8).decrypt(w[ot:ot + t2][0x1BF:0x1CF])
ok = True
p = od
for i in range(nn):
    rec = 0x1E4 + i * 36
    cid, idx, ct, sz = struct.unpack('>IHHQ', T2[rec:rec + 16])
    sha = T2[rec + 16:rec + 36]
    dec = AES.new(tk, AES.MODE_CBC, struct.pack('>H', idx) + b'\0' * 14
                  ).decrypt(w[p:p + al(sz, 16)])[:sz]
    good = hashlib.sha1(dec).digest() == sha
    ok &= good
    print(f"  content{i}: size={sz} sha1_matches_TMD={good}")
    p += al(sz, 64)

sig_zero = w[om + 4:om + 0x104] == b'\0' * 256
trucha   = hashlib.sha1(T2[0x140:]).digest()[0] == 0
tid_hi, tid_lo = tid >> 32, tid & 0xFFFFFFFF
print(f"  title id      = {tid:016X} ({struct.pack('>I', tid_lo).decode('latin1')})")
print(f"  category      = {tid_hi:08X} " +
      ("(homebrew channel range - safe)" if tid_hi == 0x00010001 else "*** NOT 00010001 - DO NOT INSTALL ***"))
print(f"  requires      = IOS{ios}")
print(f"  sig zeroed    = {sig_zero}")
print(f"  trucha sha1   = {trucha}")
print(f"\nRESULT: {'ALL CHECKS PASSED' if (ok and sig_zero and trucha and tid_hi == 0x00010001) else 'FAILED - DO NOT INSTALL'}")
