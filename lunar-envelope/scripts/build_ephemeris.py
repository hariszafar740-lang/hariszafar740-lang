#!/usr/bin/env python3
"""Reproduce 2020–2030 Moon-fixed vectors. Requires separately obtained, pinned SPICE kernels.

Usage: python scripts/build_ephemeris.py /path/to/kernel-directory /path/to/output.csv
The directory must contain the names listed in KERNELS. Output is not overwritten.
Install SpiceyPy 7.0.0 separately; it is not a runtime dependency.
"""
from datetime import datetime, timedelta, timezone
import csv
import hashlib
import sys
from pathlib import Path

KERNELS = {
    'naif0012.tls':'678e32bdb5a744117a467cd9601cd6b373f0e9bc9bbde1371d5eee39600a039b',
    'de421.bsp':'a20a7139da04cbc462454634918e9a9ca69127044e2cc9d4f9c16e238d2deedc',
    'moon_pa_de421_1900-2050.bpc':'656f90616403d75a75f0cd6c8830fc5b44f8cb4facb5ccb8915e752b397520cf',
    'moon_080317.tf':'78732477b96f9863e7b0d65bcee3c22b8707ca5ed0db56d1173319cb2e8c7993',
}

def build(directory, output):
    import spiceypy as spice
    if spice.__version__ != '7.0.0' or spice.tkvrsn('TOOLKIT') != 'CSPICE_N0067':
        raise RuntimeError('Reproduction requires SpiceyPy 7.0.0 / CSPICE N0067')
    spice.kclear()
    for name, expected in KERNELS.items():
        path = directory / name
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f'Kernel hash mismatch: {name}')
        spice.furnsh(str(path))
    start=datetime(2020,1,1,tzinfo=timezone.utc); end=datetime(2031,1,1,tzinfo=timezone.utc)
    with output.open('x',newline='',encoding='ascii') as f:
        writer=csv.writer(f,lineterminator='\n')
        writer.writerow(['utc','sun_x_m','sun_y_m','sun_z_m','earth_x_m','earth_y_m','earth_z_m'])
        current=start
        while current<=end:
            utc=current.strftime('%Y-%m-%dT%H:%M:%SZ')
            et=spice.str2et(utc)
            sun,_=spice.spkpos('SUN',et,'MOON_ME_DE421','NONE','MOON')
            earth,_=spice.spkpos('EARTH',et,'MOON_ME_DE421','NONE','MOON')
            writer.writerow([utc,*[f'{v*1000:.6f}' for v in (*sun,*earth)]])
            current+=timedelta(hours=2)
    spice.kclear()

if __name__=='__main__':
    if len(sys.argv)!=3: raise SystemExit(__doc__)
    build(Path(sys.argv[1]),Path(sys.argv[2]))
