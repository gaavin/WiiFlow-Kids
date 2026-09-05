import struct
def decompress(d):
    """Nintendo LZ10, optionally prefixed with 'LZ77' magic."""
    if d[:4]==b'LZ77': d=d[4:]
    assert d[0]==0x10, "not LZ10"
    size = int.from_bytes(d[1:4],'little')
    out=bytearray(); i=4
    while len(out)<size:
        flags=d[i]; i+=1
        for b in range(8):
            if len(out)>=size: break
            if flags & (0x80>>b):
                v=(d[i]<<8)|d[i+1]; i+=2
                ln=(v>>12)+3; disp=(v&0xFFF)+1
                st=len(out)-disp
                for k in range(ln): out.append(out[st+k])
            else:
                out.append(d[i]); i+=1
    return bytes(out[:size])

def compress(src):
    """Greedy LZ10 encoder. Output is verified by round-trip at call sites."""
    out=bytearray(b'LZ77'); out+=bytes([0x10])+len(src).to_bytes(3,'little')
    i=0; n=len(src)
    while i<n:
        flagpos=len(out); out.append(0); flags=0
        for b in range(8):
            if i>=n: break
            best_len=0; best_disp=0
            start=max(0,i-0x1000)
            maxlen=min(18, n-i)
            if maxlen>=3:
                window=src[start:i]
                for ln in range(maxlen,2,-1):
                    pos=window.rfind(src[i:i+ln])
                    if pos>=0:
                        best_len=ln; best_disp=i-(start+pos); break
            if best_len>=3:
                flags |= (0x80>>b)
                v=((best_len-3)<<12) | (best_disp-1)
                out += struct.pack('>H', v)
                i+=best_len
            else:
                out.append(src[i]); i+=1
        out[flagpos]=flags
    return bytes(out)
