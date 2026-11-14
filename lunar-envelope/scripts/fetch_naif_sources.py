#!/usr/bin/env python3
"""Download and SHA-256 verify the four NASA/NAIF originals used in checks.

Usage: python scripts/fetch_naif_sources.py OUTPUT_DIRECTORY
Uses only the standard library; network required. Existing mismatching files
are never overwritten. This checks source identity, not geometry accuracy.
The original DE421 differs from the pinned production mirror; no production
kernel or table is replaced. See data/ephemeris/README.md.
"""
import hashlib,os,sys,tempfile
from pathlib import Path
from urllib.request import urlopen
from check_naif_vectors import NAIF

BASE='https://naif.jpl.nasa.gov/pub/naif/generic_kernels/'
RELATIVE={'de421.bsp':'spk/planets/a_old_versions/de421.bsp',
          'moon_pa_de421_1900-2050.bpc':'pck/moon_pa_de421_1900-2050.bpc',
          'moon_080317.tf':'fk/satellites/moon_080317.tf',
          'naif0012.tls':'lsk/naif0012.tls'}

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def main(directory):
    directory.mkdir(parents=True,exist_ok=True)
    for name,relative in RELATIVE.items():
        target=directory/name;expected=NAIF[name]
        if target.exists():
            if digest(target)!=expected:raise ValueError(f'Existing file mismatch; refusing overwrite: {target}')
            print(f'NAIF SHA-256 verified: {name} {expected}',flush=True);continue
        fd,tmp=tempfile.mkstemp(prefix='.'+name+'.',suffix='.partial',dir=directory);temporary=Path(tmp)
        try:
            with os.fdopen(fd,'wb') as output,urlopen(BASE+relative,timeout=120) as response:
                while block:=response.read(1024*1024):output.write(block)
            if digest(temporary)!=expected:raise ValueError(f'NAIF download SHA-256 mismatch: {name}')
            os.link(temporary,target)
            print(f'NAIF SHA-256 verified: {name} {expected}',flush=True)
        finally:temporary.unlink(missing_ok=True)
    print('NAIF DE421 is not byte-identical to the pinned production mirror; no production data changed.')

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit(__doc__)
    main(Path(sys.argv[1]))
