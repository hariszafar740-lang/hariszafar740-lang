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

def local_direction(body,lat,lon,height_m=0):
    """Center of target, topocentric azimuth/elevation (deg), spherical Moon."""
    phi,lam=math.radians(lat),math.radians(lon)
    up=(math.cos(phi)*math.cos(lam),math.cos(phi)*math.sin(lam),math.sin(phi))
    east=(-math.sin(lam),math.cos(lam),0.)
    north=(-math.sin(phi)*math.cos(lam),-math.sin(phi)*math.sin(lam),math.cos(phi))
    relative=tuple(body[i]-(RADIUS_M+height_m)*up[i] for i in range(3))
    dot=lambda u,v: sum(a*b for a,b in zip(u,v))
    e,n,u=dot(relative,east),dot(relative,north),dot(relative,up)
    horizontal=math.hypot(e,n); distance=math.sqrt(e*e+n*n+u*u)
    return {'elevation_deg':math.degrees(math.atan2(u,horizontal)),
            'azimuth_deg':math.degrees(math.atan2(e,n))%360,
            'azimuth_defined':horizontal>max(1e-9,distance*1e-12),
            'distance_km':round(distance/1000,3)}

def at_site(at,latitude,longitude,height_m=0):
    vectors=vectors_at(at)
    sun=local_direction(vectors[:3],latitude,longitude,height_m)
    earth=local_direction(vectors[3:],latitude,longitude,height_m)
    return {'sun':sun,'earth':earth}


# Runtime uses a second, self-generated, hash-gated table when it is available.
# The original third-party 2026 table is retained as an offline fallback.
EXTENDED_PATH = PATH.parent / 'de421_2020_2030.csv'
EXTENDED_SHA256 = '966bed14200d762ee124812b6de891c4c6d169e2a5101be303563750c0b4ce61'
EXTENDED_START = datetime(2020,1,1,tzinfo=timezone.utc)
EXTENDED_END = datetime(2031,1,1,tzinfo=timezone.utc)
EXTENDED_SOURCE = 'https://github.com/skyfielders/python-skyfield/tree/31a6ed7584cd09b6e48e07546a4b5921e1cd5bb4/ci'
LEGACY_SOURCE = 'https://github.com/julianascencio/orbital-pv/tree/7c2b1a64f7d43b9662b022ac3b88351228bbd3cd/examples/lunar/_data'

class DataUnavailable(Exception):
    """No verified dataset can cover the requested interval."""

@lru_cache(maxsize=1)
def load_extended():
    if hashlib.sha256(EXTENDED_PATH.read_bytes()).hexdigest()!=EXTENDED_SHA256:
        raise ValueError('Extended ephemeris checksum mismatch')
    times=[]; vectors=[]
    with EXTENDED_PATH.open(newline='',encoding='ascii') as f:
        reader=csv.DictReader(f)
        fields=['utc','sun_x_m','sun_y_m','sun_z_m','earth_x_m','earth_y_m','earth_z_m']
        if reader.fieldnames!=fields: raise ValueError('Unexpected extended ephemeris schema')
        for row in reader:
            t=datetime.fromisoformat(row['utc'].replace('Z','+00:00'))
            values=tuple(float(row[k]) for k in fields[1:])
            if not all(math.isfinite(x) for x in values): raise ValueError('Nonfinite vector')
            if times and (t-times[-1]).total_seconds()!=7200: raise ValueError('Nonuniform time step')
            times.append(t);vectors.append(values)
    if len(times)!=48217 or times[0]!=EXTENDED_START or times[-1]!=EXTENDED_END:
        raise ValueError('Unexpected extended ephemeris coverage')
    return tuple(times),tuple(vectors)

class Ephemeris:
    def __init__(self, table, digest, source, kind):
        self.times,self.vectors=table
        self.digest,self.source,self.kind=digest,source,kind
    def at(self,at,latitude,longitude,height_m=0):
        if at.tzinfo is None or at.utcoffset() is None: raise ValueError('Time must include a timezone')
        at=at.astimezone(timezone.utc)
        if not self.times[0]<=at<=self.times[-1]: raise ValueError('Time outside ephemeris coverage')
        i=bisect.bisect_right(self.times,at)-1
        if i==len(self.times)-1: values=self.vectors[-1]
        else:
            fraction=(at-self.times[i]).total_seconds()/7200
            # Linear interpolation of raw Moon-fixed vectors artificially shrinks
            # range during rotation (several thousand km for the Sun at midpoint).
            # Interpolate direction and range separately, then renormalize.
            values=[]
            for offset in (0,3):
                a=self.vectors[i][offset:offset+3]; b=self.vectors[i+1][offset:offset+3]
                ra=math.sqrt(sum(v*v for v in a)); rb=math.sqrt(sum(v*v for v in b))
                direction=tuple((1-fraction)*a[j]/ra+fraction*b[j]/rb for j in range(3))
                norm=math.sqrt(sum(v*v for v in direction)); radius=ra+(rb-ra)*fraction
                values.extend(v*radius/norm for v in direction)
        return {'sun':local_direction(values[:3],latitude,longitude,height_m),
                'earth':local_direction(values[3:],latitude,longitude,height_m)}

def select(start,end):
    if start < EXTENDED_START or end > EXTENDED_END:
        raise ValueError('The full interval must lie between 2020-01-01 and 2031-01-01 UTC')
    try:
        return Ephemeris(load_extended(),EXTENDED_SHA256,EXTENDED_SOURCE,'extended')
    except (OSError,ValueError):
        if start>=START and end<=END:
            try: return Ephemeris(load_table(),SHA256,LEGACY_SOURCE,'2026 fallback')
            except (OSError,ValueError): pass
        raise DataUnavailable('No verified ephemeris covers this interval; 2026 fallback may be available')
