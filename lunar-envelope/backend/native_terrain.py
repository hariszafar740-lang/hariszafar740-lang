"""Optional, checksum-verified native NASA LOLA rasters; no automatic downloads."""
import hashlib
import os
from pathlib import Path
import struct
from functools import lru_cache
from .terrain import TerrainUnavailable

SOURCES={
    'ldem_80s_80m.img':('e6591eeea35402ca5e124ca00f5bf0774381a2d4fa919144b455d82b8ff65fdc',7600,80),
    'ldem_75s_120m.img':('ae3afc3c75c33d43666ca06c83ca08f0b12ef03b7d36d2d791d972730794391b',7624,120),
}

class Raster:
    def __init__(self,path,digest,size,pixel):
        self.size=size;self.pixel=pixel
        data=path.read_bytes()
        if len(data)!=size*size*2 or hashlib.sha256(data).hexdigest()!=digest:
            raise ValueError('LOLA raster size or SHA-256 mismatch')
        # Immutable bytes prevent post-verification file edits changing cached data.
        self.data=data
    def sample(self,x,y):
        col=x/self.pixel+self.size/2-.5;row=self.size/2-.5-y/self.pixel
        if not 0<=col<=self.size-1 or not 0<=row<=self.size-1:return None
        c=min(int(col),self.size-2);r=min(int(row),self.size-2);fc=col-c;fr=row-r
        i=(r*self.size+c)*2
        a,b=struct.unpack_from('<hh',self.data,i)
        c0,d=struct.unpack_from('<hh',self.data,i+self.size*2)
        # No-data sentinels are rejected locally, not interpreted as terrain.
        if any(v in (-32768,32767) for v in (a,b,c0,d)):
            raise TerrainUnavailable('Native LOLA raster contains a missing/fill value at a sampled location')
        return .5*((a*(1-fc)+b*fc)*(1-fr)+(c0*(1-fc)+d*fc)*fr)

@lru_cache(maxsize=1)
def load_rasters():
    directory=os.environ.get('LUNARIS_NATIVE_DEM_DIR')
    if not directory:raise TerrainUnavailable('Native LOLA rasters are not configured; set LUNARIS_NATIVE_DEM_DIR and restart')
    rasters=[]
    try:
        for name,(digest,size,pixel) in SOURCES.items():
            rasters.append(Raster(Path(directory)/name,digest,size,pixel))
        return tuple(rasters)
    except (OSError,ValueError) as exc:
        raise TerrainUnavailable('Native LOLA rasters are missing or failed size/SHA-256 verification') from exc

def sample(rasters,x,y):
    first=rasters[0].sample(x,y)
    return first if first is not None else rasters[1].sample(x,y)
