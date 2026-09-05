import struct
MAGIC=bytes([0x55,0xAA,0x38,0x2D])
def parse(d, base=0):
    assert d[base:base+4]==MAGIC, "not a U8 archive"
    root_off, hdr_size, data_off = struct.unpack('>III', d[base+4:base+16])
    nt = base+root_off
    _,_,root_count = struct.unpack('>III', d[nt:nt+12][:4]+d[nt+4:nt+8]+d[nt+8:nt+12])
    count = struct.unpack('>I', d[nt+8:nt+12])[0]
    strt = nt + count*12
    out=[]; stack=[("",count)]
    i=0
    while i < count:
        n=d[nt+i*12: nt+(i+1)*12]
        typ = n[0]; noff = int.from_bytes(n[1:4],'big')
        doff, size = struct.unpack('>II', n[4:12])
        e=d.index(b'\0', strt+noff); name=d[strt+noff:e].decode('latin1')
        out.append(dict(idx=i, type=typ, name=name, data_off=doff, size=size))
        i+=1
    return out, dict(root_off=root_off, hdr_size=hdr_size, data_off=data_off, count=count, strt=strt, nt=nt)
