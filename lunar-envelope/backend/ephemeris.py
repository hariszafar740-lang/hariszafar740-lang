"""2026 Moon-fixed JPL DE421-derived vector interpolation, with flat-horizon geometry.

The two-hour table is a pinned third-party calculation, not live NASA telemetry.
No terrain, antenna, occultation beyond a spherical horizon, or refraction model.
"""
from __future__ import annotations
import bisect
import csv
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import math
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / 'data' / 'ephemeris' / 'year_2026_ephemeris.csv'
SHA256 = '90c0d716388897af5c26ffc971d04e15817e5614ba92c4111447dca037c26ddd'
START = datetime(2026,1,1,tzinfo=timezone.utc)
END = datetime(2027,1,1,tzinfo=timezone.utc)
RADIUS_M = 1737400.0

@lru_cache(maxsize=1)
def load_table():
    if hashlib.sha256(PATH.read_bytes()).hexdigest() != SHA256:
        raise ValueError('Ephemeris checksum mismatch')
    times=[]; vectors=[]
    with PATH.open(newline='',encoding='ascii') as f:
        reader=csv.DictReader(f)
        expected=['utc','time_s','sun_x_m','sun_y_m','sun_z_m','earth_x_m','earth_y_m','earth_z_m']
        if reader.fieldnames != expected: raise ValueError('Unexpected ephemeris schema')
        for row in reader:
            dt=datetime.fromisoformat(row['utc'].replace('Z','+00:00'))
            values=tuple(float(row[k]) for k in expected[2:])
            if not all(math.isfinite(v) for v in values): raise ValueError('Invalid vector')
            if times and (dt-times[-1]).total_seconds()!=7200: raise ValueError('Nonuniform ephemeris time step')
            times.append(dt);vectors.append(values)
    if len(times)!=4381 or times[0]!=START or times[-1]!=END:
        raise ValueError('Unexpected ephemeris coverage')
    return tuple(times),tuple(vectors)

def vectors_at(at:datetime):
    if at.tzinfo is None or at.utcoffset() is None: raise ValueError('Time must include a timezone')
    at=at.astimezone(timezone.utc)
    times,vectors=load_table()
    if not times[0] <= at <= times[-1]: raise ValueError('Time is outside 2026 table coverage')
    i=bisect.bisect_right(times,at)-1
    if i==len(times)-1:return vectors[-1]
    fraction=(at-times[i]).total_seconds()/(times[i+1]-times[i]).total_seconds()
    return tuple(a+(b-a)*fraction for a,b in zip(vectors[i],vectors[i+1]))

def local_direction(body,lat,lon):
    """Center of target, topocentric azimuth/elevation (deg), spherical Moon."""
    phi,lam=math.radians(lat),math.radians(lon)
    up=(math.cos(phi)*math.cos(lam),math.cos(phi)*math.sin(lam),math.sin(phi))
    east=(-math.sin(lam),math.cos(lam),0.)
    north=(-math.sin(phi)*math.cos(lam),-math.sin(phi)*math.sin(lam),math.cos(phi))
    relative=tuple(body[i]-RADIUS_M*up[i] for i in range(3))
    dot=lambda u,v: sum(a*b for a,b in zip(u,v))
    e,n,u=dot(relative,east),dot(relative,north),dot(relative,up)
    return {'elevation_deg':math.degrees(math.atan2(u,math.hypot(e,n))),
            'azimuth_deg':math.degrees(math.atan2(e,n))%360,
            'distance_km':round(math.sqrt(e*e+n*n+u*u)/1000,3)}

def at_site(at,latitude,longitude):
    vectors=vectors_at(at)
    sun=local_direction(vectors[:3],latitude,longitude)
    earth=local_direction(vectors[3:],latitude,longitude)
    return {'sun':sun,'earth':earth}
