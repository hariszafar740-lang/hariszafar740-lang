#!/usr/bin/env python3
"""Use archived Horizons inertial site vectors to independently derive ENU.

No CSPICE kernels or app code are used. Each axis row is the geometric ICRF
vector from a cardinal lunar surface site TO the Moon center. Negate and divide
by the lunar radius to get a unit lunar axis in ICRF. The Sun/Earth vectors are
Horizons Moon-center-to-target ICRF values. No model is fit to app outputs.
Usage: python scripts/generate_horizons_axes_reference.py AXES_CSV TARGETS_CSV OUTPUT_CSV
"""
import csv
import math
import sys
from pathlib import Path

SITES=[(-85,0,0),(-88,-90,50),(0,0,0),(45,120,1000),(-89.9,179.99,5),(30,-170,100)]
R=1737.4

def dot(a,b):return sum(x*y for x,y in zip(a,b))
def combo(basis,coefs):return [sum(coefs[i]*basis[i][j] for i in range(3)) for j in range(3)]

def main(axes_file,targets_file,outfile):
    axes={}
    with axes_file.open(newline='',encoding='ascii') as f:
        for row in csv.DictReader(f):
            axes.setdefault(row['utc'],{})[row['axis']]=[-float(row[k])/R for k in ('x_km','y_km','z_km')]
    with targets_file.open(newline='',encoding='ascii') as f,outfile.open('x',newline='',encoding='ascii') as out:
        w=csv.writer(out,lineterminator='\n');w.writerow(['utc','latitude','longitude','height_m','body','azimuth_deg','elevation_deg','distance_km'])
        for row in csv.DictReader(f):
            basis=[axes[row['utc']][key] for key in 'XYZ']
            for i in range(3):
                for j in range(3):
                    if abs(dot(basis[i],basis[j])-(1 if i==j else 0))>1e-10:raise ValueError('Invalid orientation axes')
            target=[float(row[k]) for k in ('x_km','y_km','z_km')]
            for lat,lon,height in SITES:
                p,l=map(math.radians,(lat,lon));cp,sp,cl,sl=math.cos(p),math.sin(p),math.cos(l),math.sin(l)
                up=combo(basis,(cp*cl,cp*sl,sp));north=combo(basis,(-sp*cl,-sp*sl,cp));east=combo(basis,(-sl,cl,0))
                relative=[target[i]-(R+height/1000)*up[i] for i in range(3)]
                n,e,u=dot(relative,north),dot(relative,east),dot(relative,up)
                az=math.degrees(math.atan2(e,n))%360;el=math.degrees(math.atan2(u,math.hypot(n,e)))
                dist=math.sqrt(dot(relative,relative))
                w.writerow([row['utc'],lat,lon,height,row['body'],f'{az:.12f}',f'{el:.12f}',f'{dist:.9f}'])

if __name__=='__main__':
    if len(sys.argv)!=4:raise SystemExit(__doc__)
    main(*map(Path,sys.argv[1:]))
