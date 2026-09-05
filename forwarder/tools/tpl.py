import struct
def decode_rgba8(d):
    magic,nimg,tbl = struct.unpack('>III', d[:12])
    hoff,poff = struct.unpack('>II', d[tbl:tbl+8])
    h,w,fmt,doff = struct.unpack('>HHII', d[hoff:hoff+12])
    assert fmt==6, f"format {fmt} not RGBA8"
    px=bytearray(w*h*4)
    o=doff
    for ty in range(0,(h+3)//4*4,4):
        for tx in range(0,(w+3)//4*4,4):
            ar=d[o:o+32]; gb=d[o+32:o+64]; o+=64
            for k in range(16):
                x=tx+(k%4); y=ty+(k//4)
                if x>=w or y>=h: continue
                a,r = ar[k*2], ar[k*2+1]
                g,b = gb[k*2], gb[k*2+1]
                i=(y*w+x)*4
                px[i]=r; px[i+1]=g; px[i+2]=b; px[i+3]=a
    return w,h,bytes(px)

def _header(w, h, fmt):
    out = bytearray()
    out += struct.pack('>III', 0x0020AF30, 1, 0x0C)
    out += struct.pack('>II', 0x14, 0x00)
    hdr = struct.pack('>HHII', h, w, fmt, 0x40)
    hdr += struct.pack('>IIII', 0, 0, 1, 1)
    hdr += struct.pack('>f', 0.0)
    hdr += bytes([0, 0, 0, 0])
    out += hdr
    out += b'\0' * (0x40 - len(out))
    return out


def _px(px, w, h, x, y):
    if 0 <= x < w and 0 <= y < h:
        i = (y * w + x) * 4
        return px[i], px[i + 1], px[i + 2], px[i + 3]
    return 0, 0, 0, 0


def encode_rgb565(w, h, px):
    out = _header(w, h, 4)
    for ty in range(0, (h + 3) // 4 * 4, 4):
        for tx in range(0, (w + 3) // 4 * 4, 4):
            for k in range(16):
                r, g, b, _ = _px(px, w, h, tx + k % 4, ty + k // 4)
                v = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
                out += struct.pack('>H', v)
    return bytes(out)


def encode_ia8(w, h, px):
    """A then I, 4x4 tiles.

    Alpha is the high byte, matching encode_ia4 putting alpha in the high
    nibble. Writing intensity first is what produced the black bars on the
    channel banner: a transparent background encodes as (255, 0), which the
    hardware read as alpha 255 / intensity 0 — an opaque black rectangle
    with the artwork punched through it in white.
    """
    out = _header(w, h, 3)
    for ty in range(0, (h + 3) // 4 * 4, 4):
        for tx in range(0, (w + 3) // 4 * 4, 4):
            for k in range(16):
                r, g, b, a = _px(px, w, h, tx + k % 4, ty + k // 4)
                intensity = (r + g + b) // 3
                out += bytes([a, intensity])
    return bytes(out)


def encode_ia4(w, h, px):
    """A in the high nibble, I in the low nibble, 8x4 tiles."""
    out = _header(w, h, 2)
    for ty in range(0, (h + 3) // 4 * 4, 4):
        for tx in range(0, (w + 7) // 8 * 8, 8):
            for k in range(32):
                r, g, b, a = _px(px, w, h, tx + k % 8, ty + k // 8)
                intensity = (r + g + b) // 3
                out += bytes([((a >> 4) << 4) | (intensity >> 4)])
    return bytes(out)


def encode_rgba8(w,h,px):
    """px = RGBA bytes, w*h*4. Returns a complete TPL matching the WiiFlow forwarder layout."""
    out=bytearray()
    out += struct.pack('>III', 0x0020AF30, 1, 0x0C)   # magic, 1 image, table @0xC
    out += struct.pack('>II', 0x14, 0x00)             # image header @0x14, no palette
    hdr = struct.pack('>HHII', h, w, 6, 0x40)         # height,width,fmt=RGBA8,data@0x40
    hdr += struct.pack('>IIII', 0,0,1,1)              # wrapS,wrapT,minFilter,magFilter
    hdr += struct.pack('>f', 0.0)                     # LOD bias
    hdr += bytes([0,0,0,0])                           # edgeLOD,minLOD,maxLOD,unpacked
    out += hdr
    out += b'\0' * (0x40-len(out))
    for ty in range(0,(h+3)//4*4,4):
        for tx in range(0,(w+3)//4*4,4):
            ar=bytearray(); gb=bytearray()
            for k in range(16):
                x=tx+(k%4); y=ty+(k//4)
                if x<w and y<h:
                    i=(y*w+x)*4
                    r,g,b,a = px[i],px[i+1],px[i+2],px[i+3]
                else:
                    r=g=b=a=0
                ar += bytes([a,r]); gb += bytes([g,b])
            out += ar+gb
    return bytes(out)
