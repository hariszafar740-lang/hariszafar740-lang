#!/usr/bin/env python3
"""Compare selected coarse horizons with direct higher-resolution PDS raster rays.

Usage: python scripts/compare_terrain_high_resolution.py DIR OUTPUT.csv
Requires NumPy and the two hash-verified original PDS files in DIR. Samples
native 80/120 m rasters with a separate spherical destination/bilinear code at
40 m intervals, from 600 m until 300 km or the coarse raster edge. Uses native
bilinear ground elevation. Output selected differences are not global bounds.
"""
import csv,math,sys
from pathlib import Path
import numpy as np
from validate_terrain_sources import SOURCES,verify
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend import terrain

SITES=[(-89.4679,-137.411),(-85.98,-.26),(-80.13,1.44)]
AZIMUTHS=[0,22.5,45,67.5,90,135,180,225,270,315,359.5]
R=1737400.0

def native_sample(a,size,pixel,x,y):
    col=x/pixel+size/2-.5;row=size/2-.5-y/pixel
    valid=(col>=0)&(row>=0)&(col<=size-1)&(row<=size-1)
    # Clip only for array access; caller uses the validity mask.
    c=np.clip(np.floor(col).astype(int),0,size-2);r=np.clip(np.floor(row).astype(int),0,size-2)
    fc=col-c;fr=row-r
    h=((1-fr)*((1-fc)*a[r,c]+fc*a[r,c+1])+fr*((1-fc)*a[r+1,c]+fc*a[r+1,c+1]))*.5
    return h,valid

def main(directory,output):
    rasters={name:verify(directory/name,*spec) for name,spec in SOURCES.items()}
    fine=rasters['ldem_80s_80m.img'];coarse=rasters['ldem_75s_120m.img']
    def height(x,y):
        x=np.atleast_1d(x);y=np.atleast_1d(y)
        h,valid=native_sample(fine,7600,80,x,y);alt,other=native_sample(coarse,7624,120,x,y)
        return np.where(valid,h,alt),valid|other
    with output.open('x',newline='',encoding='ascii') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['latitude','longitude','height_above_ground_m','azimuth_deg','coarse_ground_m','native_ground_m','coarse_horizon_deg','native_horizon_deg','coarse_minus_native_deg','native_peak_distance_km','end_distance_km'])
        for lat,lon in SITES:
            ground,profile,_,_=terrain.horizon(lat,lon,2)
            phi,lam=map(math.radians,(lat,lon));sp,cp=math.sin(phi),math.cos(phi)
            rr=2*R*cp/(1-sp);site,valid=height(rr*math.sin(lam),rr*math.cos(lam))
            if not valid[0]:raise ValueError('Site outside source raster')
            d=np.arange(600,300001,40,dtype=float);delta=d/R
            for az in AZIMUTHS:
                bearing=math.radians(az)
                p=np.arcsin(np.clip(sp*np.cos(delta)+cp*np.sin(delta)*math.cos(bearing),-1,1))
                l=lam+np.arctan2(math.sin(bearing)*np.sin(delta)*cp,np.cos(delta)-sp*np.sin(p))
                rho=2*R*np.cos(p)/(1-np.sin(p));x=rho*np.sin(l);y=rho*np.cos(l)
                # Restrict both models to the bundled grid's pixel-center domain.
                inside=(np.abs(x)<=455800)&(np.abs(y)<=455800)
                first=np.flatnonzero(~inside);n=int(first[0]) if first.size else len(d)
                x,y=x[:n],y[:n];ds=delta[:n]
                h,valid=height(x,y)
                if not len(h) or not valid.all():raise ValueError('Reference ray outside original raster')
                angles=np.degrees(np.arctan2((R+h)*np.cos(ds)-(R+site[0]+2),(R+h)*np.sin(ds)))
                idx=int(np.argmax(angles));reference=float(angles[idx]);pred=terrain.horizon_at(profile,az)
                w.writerow([lat,lon,2,az,f'{ground:.6f}',f'{site[0]:.6f}',f'{pred:.9f}',f'{reference:.9f}',f'{pred-reference:.9f}',f'{d[idx]/1000:.2f}',f'{d[n-1]/1000:.2f}'])
if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit(__doc__)
    main(Path(sys.argv[1]),Path(sys.argv[2]))
