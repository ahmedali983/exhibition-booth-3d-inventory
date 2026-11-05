"""Bounded HTTP range reader for publicly available ProSceneverse TAR shards."""
import io
import requests

class RemoteTar(io.RawIOBase):
    def __init__(self, url):
        self.pos=0
        r=requests.head(url,allow_redirects=True,timeout=35)
        r.raise_for_status()
        self.url=r.url
        self.length=int(r.headers["Content-Length"])
    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos
    def seek(self, offset, whence=0):
        if whence==0:self.pos=offset
        elif whence==1:self.pos+=offset
        else:self.pos=self.length+offset
        return self.pos
    def read(self,n=-1):
        if self.pos>=self.length:return b""
        if n<0:n=self.length-self.pos
        n=min(n,self.length-self.pos)
        if n==0:return b""
        s=self.pos;e=s+n-1
        r=requests.get(self.url,headers={"Range":f"bytes={s}-{e}"},timeout=(20,90))
        if r.status_code!=206:raise IOError(f"Expected partial content, got {r.status_code}")
        if not r.headers.get("Content-Range","").startswith(f"bytes {s}-{e}/"):
            raise IOError("Invalid range response")
        if len(r.content)!=n:raise IOError("Truncated response")
        self.pos+=n
        return r.content

