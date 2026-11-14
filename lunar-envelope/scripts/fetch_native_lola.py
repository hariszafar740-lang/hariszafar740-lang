#!/usr/bin/env python3
"""Download optional original NASA LOLA rasters (~232 MB); verify before use.

Usage: python scripts/fetch_native_lola.py OUTPUT_DIRECTORY
Requires a network connection and free space; existing nonmatching files are
never overwritten. Afterwards set LUNARIS_NATIVE_DEM_DIR and restart the app.
"""
import hashlib,os,sys,tempfile
from pathlib import Path
from urllib.request import urlopen
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.native_terrain import SOURCES
BASE='https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/'

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def main(directory):
    directory.mkdir(parents=True,exist_ok=True)
    for name,(sha,size,_) in SOURCES.items():
        path=directory/name
        if path.exists():
            if path.stat().st_size!=size*size*2 or digest(path)!=sha:raise ValueError(f'Existing file does not match; refusing overwrite: {path}')
            print(f'Already verified: {path}',flush=True);continue
        fd,temporary=tempfile.mkstemp(prefix='.'+name+'.',suffix='.partial',dir=directory)
        temp=Path(temporary)
        try:
            print(f'Downloading {BASE+name}',flush=True)
            with os.fdopen(fd,'wb') as f,urlopen(BASE+name,timeout=120) as response:
                while chunk:=response.read(1024*1024):f.write(chunk)
            if temp.stat().st_size!=size*size*2 or digest(temp)!=sha:raise ValueError(f'Download size/hash mismatch: {name}')
            # Do not silently replace an existing file that appeared during download.
            os.link(temp,path)
            print(f'Verified: {path}',flush=True)
        finally:temp.unlink(missing_ok=True)
if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit(__doc__)
    main(Path(sys.argv[1]))
