#!/usr/bin/env python3
"""Generate selected CSPICE topocentric reference vectors from pinned kernels.

For angles/ranges tests only, NOT an independent domain-expert audit. Uses the
same kernels as the table but NAIF's separate azlcpo implementation.
Usage: python scripts/generate_cspice_reference.py /path/to/kernels /path/to/output.csv
See build_ephemeris.py and data/ephemeris/README.md for kernel hashes/sources.
"""
from pathlib import Path
import csv, hashlib, math, sys
from build_ephemeris import KERNELS

TIMES=['2020-01-01T00:00:00','2020-06-30T01:07:30','2021-12-31T23:45:00','2023-03-20T07:30:00','2025-07-01T01:00:00','2026-11-14T12:00:00','2026-11-14T13:00:00','2028-02-29T12:45:00','2029-09-23T03:15:00','2030-12-31T23:00:00']
SITES=[(-85,0,0),(-88,-90,50),(0,0,0),(45,120,1000),(-89.9,179.99,5),(30,-170,100)]

def main(directory,output):
    import spiceypy as sp
    if sp.__version__!='7.0.0' or sp.tkvrsn('TOOLKIT')!='CSPICE_N0067': raise RuntimeError('Requires SpiceyPy 7.0.0 / CSPICE N0067')
    sp.kclear()
    for name,digest in KERNELS.items():
        path=directory/name
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('Kernel checksum mismatch: '+name)
        sp.furnsh(str(path))
    sp.pdpool('BODY301_RADII',[1737.4]*3);sp.pcpool('OBJECT_301_FRAME',['MOON_ME_DE421'])
    with output.open('x',newline='',encoding='ascii') as f:
        writer=csv.writer(f,lineterminator='\n')
        writer.writerow(['utc','latitude','longitude','height_m','body','azimuth_deg','elevation_deg','distance_km'])
        for time in TIMES:
            et=sp.str2et(time)
            for lat,lon,height in SITES:
                xyz=sp.latrec(1737.4+height/1000,math.radians(lon),math.radians(lat))
                for body in ('SUN','EARTH'):
                    p,_=sp.azlcpo('ELLIPSOID',body,et,'NONE',False,True,xyz,'MOON','MOON_ME_DE421')
                    writer.writerow([time+'Z',lat,lon,height,body,format(math.degrees(p[1]),'.12f'),format(math.degrees(p[2]),'.12f'),format(p[0],'.9f')])
    sp.kclear()

if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit(__doc__)
    main(Path(sys.argv[1]),Path(sys.argv[2]))
