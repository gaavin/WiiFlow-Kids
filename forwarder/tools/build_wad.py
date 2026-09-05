import struct, hashlib
from Crypto.Cipher import AES
import lz, u8

COMMON=bytes.fromhex('ebe42a225e8593e448d9c5457381aaf7')
al=lambda x,a: (x+a-1)//a*a
NAME="WiiFlow Kids"

# ---------- 1. compress the retextured archives, verify round-trip ----------
def imd5(payload):
    return b'IMD5'+struct.pack('>I',len(payload))+b'\0'*8+hashlib.md5(payload).digest()+payload

parts={}
for arc in ('banner.bin','icon.bin'):
    raw=open(arc+'.u8.new','rb').read()
    comp=lz.compress(raw)
    assert lz.decompress(comp)==raw, f"{arc}: LZ10 round-trip FAILED"
    parts[arc]=imd5(comp)
    print(f"  {arc}: u8={len(raw)} -> lz={len(comp)} -> imd5={len(parts[arc])}  round-trip OK")
parts['sound.bin']=open('sound.bin','rb').read()   # untouched, already IMD5-wrapped
print(f"  sound.bin: {len(parts['sound.bin'])} bytes (untouched)")

# ---------- 2. rebuild outer U8 (patch node table, keep strings) ----------
orig=open('c0.bin','rb').read()
B=0x600
ents,meta=u8.parse(orig,B)
node_tbl_off=meta['nt']-B; count=meta['count']
strt=meta['strt']-B
hdr_size, data_off = meta['hdr_size'], meta['data_off']
arch=bytearray(orig[B:B+data_off])            # header + nodes + strings + pad
cur=data_off
newdata=bytearray()
for e in ents:
    if e['type']!=0: continue
    blob=parts[e['name']]
    cur=al(cur,32)
    pad=cur-(data_off+len(newdata))
    newdata+=b'\0'*pad+blob
    n=node_tbl_off+e['idx']*12
    arch[n+4:n+12]=struct.pack('>II', cur, len(blob))
    cur+=len(blob)
outer=bytes(arch)+bytes(newdata)
print(f"  outer U8 rebuilt: {len(outer)} bytes")

# ---------- 3. IMET: rename + recompute md5 ----------
imet=bytearray(orig[0:B])
enc=NAME.encode('utf-16-be')
for L in range(10):
    off=0x5C+L*84
    imet[off:off+84]=enc+b'\0'*(84-len(enc))
imet[0x5F0:0x600]=b'\0'*16
imet[0x5F0:0x600]=hashlib.md5(bytes(imet)).digest()
print(f"  IMET: names set to {NAME!r}, md5 recomputed")

content0=bytes(imet)+outer
print(f"  content0: {len(orig)} -> {len(content0)} bytes")
open('c0.new','wb').write(content0)
