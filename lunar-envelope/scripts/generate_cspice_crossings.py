#!/usr/bin/env python3
"""Independent code path for selected threshold crossings, same CSPICE kernels.

Five-minute scan + bisection using azlcpo directly, not the application event
or geometry functions. Limited regression cases, not independent peer review.
Usage: python scripts/generate_cspice_crossings.py /path/to/kernels /path/to/output.csv
"""
from pathlib import Path
from datetime import datetime,timedelta
import csv,hashlib,math,sys
from build_ephemeris import KERNELS

CASES=[('2020-03-20T00:00:00',-85,0),('2026-11-14T12:00:00',-85,0),('2026-11-14T12:00:00',-88,-90),('2028-02-25T12:00:00',0,0),('2030-12-15T00:00:00',45,120)]

def main(directory,output):
    import spiceypy as sp
    if sp.__version__!='7.0.0' or sp.tkvrsn('TOOLKIT')!='CSPICE_N0067':raise RuntimeError('Requires SpiceyPy 7.0.0 / CSPICE N0067')
    sp.kclear()
    for name,digest in KERNELS.items():
        path=directory/name
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('Kernel checksum mismatch: '+name)
        sp.furnsh(str(path))
    sp.pdpool('BODY301_RADII',[1737.4]*3);sp.pcpool('OBJECT_301_FRAME',['MOON_ME_DE421'])
    with output.open('x',newline='',encoding='ascii') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['start','days','latitude','longitude','body','kind','utc'])
        for date,lat,lon in CASES:
            start=datetime.fromisoformat(date+'+00:00');end=start+timedelta(days=14)
            xyz=sp.latrec(1737.4,math.radians(lon),math.radians(lat))
            for body in ('SUN','EARTH'):
                def state(t):
                    et=sp.str2et(t.strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
                    p,_=sp.azlcpo('ELLIPSOID',body,et,'NONE',False,True,xyz,'MOON','MOON_ME_DE421')
                    return p[2]>0
                left=start;on=state(left)
                while left<end:
                    right=min(left+timedelta(minutes=5),end);new=state(right)
                    if on!=new:
                        a,b=left,right
                        for _ in range(12):
                            mid=a+(b-a)/2
                            if state(mid)==on:a=mid
                            else:b=mid
                        w.writerow([date+'Z',14,lat,lon,body,'rise' if new else 'set',(a+(b-a)/2).isoformat().replace('+00:00','Z')])
                    left=right;on=new
    sp.kclear()

if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit(__doc__)
    main(Path(sys.argv[1]),Path(sys.argv[2]))
