from pathlib import Path
from struct import unpack_from
import ctypes as C
import numpy as np
import pandas as pd

class Decoder:
    def __init__(self,b,i=0):
        self.b,self.i=b,i
    def pop(self,n):
        a=self.i
        self.i+=n
        return self.b[a:self.i]
    def byte(self):
        return self.pop(1)[0]
    def vint(self):
        v=0;s=0
        while True:
            b=self.byte();v|=(b&127)<<s
            if b<128: return v
            s+=7
    def zz(self):
        v=self.vint()
        return (v>>1)^-(v&1)
    def value(self,t):
        if t in (1,2): return t==1
        if t==3: return self.byte()
        if t in (4,5,6): return self.zz()
        if t==7: return unpack_from('<d',self.pop(8))[0]
        if t==8: return self.pop(self.vint())
        if t in (9,10):
            v=self.byte(); n=v>>4; t=v&15
            if n==15: n=self.vint()
            return [self.value(t) for _ in range(n)]
        if t==12: return self.struct()
        raise ValueError(t)
    def struct(self):
        out={};idx=0
        while True:
            v=self.byte()
            if v==0: return out
            idx=idx+(v>>4) if (v>>4) else self.zz()
            out[idx]=self.value(v&15)
sn=C.CDLL('libsnappy.so.1')
def decompress(b,n,codec):
    if codec==0: return b
    assert codec==1,codec
    buf=C.create_string_buffer(n); nn=C.c_size_t(n)
    assert sn.snappy_uncompress(b,C.c_size_t(len(b)),buf,C.byref(nn))==0 and nn.value==n
    return buf.raw
def rle(b,width,n):
    d=Decoder(b); parts=[]; pos=0
    while pos<n:
        h=d.vint()
        if h&1:
            count=(h>>1)*8
            piece=d.pop(count*width//8)
            if width:
                bits=np.unpackbits(np.frombuffer(piece,dtype='u1'),bitorder='little').reshape(-1,width)
                a=bits@(1<<np.arange(width))
            else: a=np.zeros(count,dtype=np.int64)
        else:
            count=h>>1
            a=np.full(count,int.from_bytes(d.pop((width+7)//8),'little'),dtype=np.int64)
        pos+=count;parts.append(a)
    return np.concatenate(parts)[:n]
def plain(b,n,t):
    if t==6:
        out=[];i=0
        for _ in range(n):
            cnt=unpack_from('<I',b,i)[0];i+=4;out.append(b[i:i+cnt].decode());i+=cnt
        return np.array(out,dtype=object)
    return np.frombuffer(b,dtype={1:'<i4',2:'<i8',4:'<f4',5:'<f8'}[t],count=n)
def read(p,cols=None):
    b=Path(p).read_bytes(); size=unpack_from('<I',b,len(b)-8)[0]
    md=Decoder(b,len(b)-8-size).struct(); out={}
    for rg in md[4]:
        for col in rg[1]:
            c=col[3];name=c[3][0].decode()
            if cols and name not in cols: continue
            assert c[5]==rg[3]
            optional=next(s.get(3) for s in md[2] if s.get(4)==c[3][0])==1
            i=c.get(11,c[9]);n=0; dic=None
            while n<c[5]:
                d=Decoder(b,i);h=d.struct();i=d.i
                x=decompress(b[i:i+h[3]],h[2],c[4]);i+=h[3]
                if h[1]==2: dic=plain(x,h[7][1],c[1]);continue
                assert h[1]==0,h
                num,enc=h[5][1],h[5][2]
                if optional:
                    ln=unpack_from('<I',x)[0]; levels=rle(x[4:4+ln],1,num); assert levels.min()==1; x=x[4+ln:]
                if enc in (2,8): v=dic[rle(x[1:],x[0],num)]
                else: assert enc==0; v=plain(x,num,c[1])
                out.setdefault(name,[]).append(v);n+=num
    return pd.DataFrame({k:np.concatenate(v) for k,v in out.items()})
if __name__=='__main__':
    import sys
    f=read(sys.argv[1]); print(f.shape, f.columns);print(f.head().to_string(index=False))
