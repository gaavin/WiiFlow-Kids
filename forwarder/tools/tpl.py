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
