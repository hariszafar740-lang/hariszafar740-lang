#!/usr/bin/env python3
"""Transform archived JPL Horizons DE441 ICRF geometric vectors to site angles.

CSPICE DE421 orientation/frame and leap-second kernels are shared with the app;
DE441 inertial vectors are independently sourced from JPL Horizons. ICRF is
approximated as J2000 for this comparison; frame differences remain. Reference
site angles use CSPICE recazl, not the application's local_direction code.
Usage: python scripts/generate_horizons_reference.py KERNEL_DIR INPUT_CSV OUTPUT_CSV
"""
from pathlib import Path
import csv,hashlib,math,sys
from build_ephemeris import KERNELS
from generate_cspice_reference import SITES

def main(directory,source,output):
    import spiceypy as sp
    if sp.__version__!='7.0.0' or sp.tkvrsn('TOOLKIT')!='CSPICE_N0067':raise RuntimeError('Requires SpiceyPy 7.0.0 / CSPICE N0067')
    sp.kclear()
    # DE421.bsp is deliberately not loaded: positions come only from Horizons.
    for name in ('naif0012.tls','moon_pa_de421_1900-2050.bpc','moon_080317.tf'):
        p=directory/name
        if hashlib.sha256(p.read_bytes()).hexdigest()!=KERNELS[name]:raise ValueError('Kernel checksum mismatch: '+name)
        sp.furnsh(str(p))
    with source.open(newline='',encoding='ascii') as f,output.open('x',newline='',encoding='ascii') as out:
        w=csv.writer(out,lineterminator='\n');w.writerow(['utc','latitude','longitude','height_m','body','azimuth_deg','elevation_deg','distance_km'])
        for row in csv.DictReader(f):
            et=sp.str2et(row['utc']);rot=sp.pxform('J2000','MOON_ME_DE421',et)
            body=sp.mxv(rot,[float(row[k]) for k in ('x_km','y_km','z_km')])
            for lat,lon,height in SITES:
                phi,lam=math.radians(lat),math.radians(lon)
                site=sp.latrec(1737.4+height/1000,lam,phi)
                up=sp.vhat(site); east=[-math.sin(lam),math.cos(lam),0.];north=sp.vcrss(up,east)
                local=sp.mxv([north,east,up],sp.vsub(body,site))
                distance,az,el=sp.recazl(local,True,True)
                w.writerow([row['utc'],lat,lon,height,row['body'],format(math.degrees(az),'.12f'),format(math.degrees(el),'.12f'),format(distance,'.9f')])
    sp.kclear()

if __name__=='__main__':
    if len(sys.argv)!=4:raise SystemExit(__doc__)
    main(*map(Path,sys.argv[1:]))
