"""Coarse, truncated south-polar DEM horizon sampling; not operational visibility."""
from array import array
from datetime import timedelta
from functools import lru_cache
import gzip
import hashlib
import math
from pathlib import Path

from . import ephemeris

PATH = Path(__file__).resolve().parent.parent / 'data/terrain/dem_400m.bin.gz'
SHA256 = '71d285a32a4c1410ffed5c4d8bc62ea8ed04625f443d6f72997fa5d8b0208dbf'
SIZE = 2280
PIXEL_M = 400.0
R = ephemeris.RADIUS_M
RADIAL_STEP_M = 100
MIN_DISTANCE_M = 600
MAX_DISTANCE_M = 300000
AZIMUTH_STEP_DEG = 1
SENSITIVITY_DEG = 1.0  # illustrative perturbation, not a measured error bound
SOURCE = 'https://github.com/localizedprojects/CLPS-MOON-BROWSER/tree/9801046af387d40cc77db4f0557c802ad8cee5b4'

class TerrainUnavailable(Exception):
    """The bundled raster is missing or does not match its pinned checksum."""

@lru_cache(maxsize=1)
def load_grid():
    try:
        raw=PATH.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=SHA256: raise ValueError('Terrain checksum mismatch')
        decoded=gzip.decompress(raw)
        count=SIZE*SIZE
        if len(decoded)!=2*count: raise ValueError('Unexpected terrain data size')
        low=memoryview(decoded)[:count]; high=memoryview(decoded)[count:]
        # Reconstruct 16-bit planar residuals modulo 2**16. Predictor is
        # left + above - above-left with zeros outside the grid.
        values=array('h',[0])*count
        for y in range(SIZE):
            left=above_left=0
            for x in range(SIZE):
                i=y*SIZE+x
                above=values[i-SIZE] if y else 0
                n=(low[i]+256*high[i]+left+above-above_left)&65535
                if n>=32768:n-=65536
                values[i]=n;left=n;above_left=above
        return values
    except (OSError,EOFError,ValueError) as exc:
        raise TerrainUnavailable('The checksum-verified terrain raster is unavailable') from exc

def projected_xy(lat,lon):
    phi,lam=map(math.radians,(lat,lon)); c=math.cos(phi)
    k=2*R/(1-math.sin(phi))
    return k*c*math.sin(lam),k*c*math.cos(lam)

def sample_xy(grid,x,y):
    col=x/PIXEL_M+SIZE/2-.5; row=SIZE/2-.5-y/PIXEL_M
    if not 0<=col<=SIZE-1 or not 0<=row<=SIZE-1: return None
    c=min(int(col),SIZE-2);r=min(int(row),SIZE-2)
    fc=col-c;fr=row-r;i=r*SIZE+c
    return ((grid[i]*(1-fc)+grid[i+1]*fc)*(1-fr)
            +(grid[i+SIZE]*(1-fc)+grid[i+SIZE+1]*fc)*fr)

def elevation_angle(site_radius,terrain_radius,central_angle):
    return math.degrees(math.atan2(terrain_radius*math.cos(central_angle)-site_radius,
                                   terrain_radius*math.sin(central_angle)))

def _sample_horizon(latitude,longitude,observer_height_m,grid,sampler,radial_step):
    """360 sampled rays; stop at first raster edge, never extrapolate."""
    sx,sy=projected_xy(latitude,longitude)
    ground=sampler(grid,sx,sy)
    if ground is None:raise ValueError('Site outside terrain grid')
    phi=math.radians(latitude);lam=math.radians(longitude)
    up=(math.cos(phi)*math.cos(lam),math.cos(phi)*math.sin(lam),math.sin(phi))
    north=(-math.sin(phi)*math.cos(lam),-math.sin(phi)*math.sin(lam),math.cos(phi))
    east=(-math.sin(lam),math.cos(lam),0.)
    # Precompute the trigonometry of the range steps once.
    arc=[(math.sin(d/R),math.cos(d/R)) for d in range(MIN_DISTANCE_M,MAX_DISTANCE_M+1,radial_step)]
    values=[]; coverage=[]; peak_distances=[]
    for az in range(0,360,AZIMUTH_STEP_DEG):
        a=math.radians(az); ca=math.cos(a);sa=math.sin(a)
        direction=tuple(ca*north[i]+sa*east[i] for i in range(3))
        best=-90.;last_distance=0;peak_distance=0
        for index,(sn,cs) in enumerate(arc):
            ux=up[0]*cs+direction[0]*sn;uy=up[1]*cs+direction[1]*sn;uz=up[2]*cs+direction[2]*sn
            k=2*R/(1-uz)
            h=sampler(grid,k*uy,k*ux)
            if h is None:break
            last_distance=MIN_DISTANCE_M+index*radial_step
            angle=math.degrees(math.atan2((R+h)*cs-(R+ground+observer_height_m),(R+h)*sn))
            if angle>best:
                best=angle;peak_distance=last_distance
        if not last_distance:raise ValueError('Terrain ray starts outside raster')
        values.append(best);coverage.append(last_distance/1000);peak_distances.append(peak_distance/1000)
    return ground,tuple(values),tuple(coverage),tuple(peak_distances)

@lru_cache(maxsize=24)
def horizon(latitude,longitude,observer_height_m):
    return _sample_horizon(latitude,longitude,observer_height_m,load_grid(),sample_xy,RADIAL_STEP_M)

@lru_cache(maxsize=4)
def native_horizon(latitude,longitude,observer_height_m):
    from . import native_terrain
    return _sample_horizon(latitude,longitude,observer_height_m,native_terrain.load_rasters(),native_terrain.sample,40)

def horizon_at(profile,azimuth):
    x=(azimuth%360)/AZIMUTH_STEP_DEG
    lo=math.floor(x);f=x-lo
    return profile[lo]*(1-f)+profile[(lo+1)%len(profile)]*f

def sensitivity(margin):
    """Would +/- the illustrative offset change the strict-above result?"""
    return 'changes' if -SENSITIVITY_DEG < margin <= SENSITIVITY_DEG else 'unchanged'

def screen(request):
    start=request.start;end=start+timedelta(days=request.days)
    data=ephemeris.select(start,end)
    native=request.terrain_resolution=='native'
    calculator=native_horizon if native else horizon
    ground,profile,coverage,peak_distances=calculator(request.latitude,request.longitude,request.observer_height_m)
    from . import native_terrain
    source_hashes={k:v[0] for k,v in native_terrain.SOURCES.items()} if native else {PATH.name:SHA256}
    samples=[]
    for i in range(request.days*24*60//request.step_minutes):
        at=start+timedelta(minutes=(i+.5)*request.step_minutes)
        sky=data.at(at,request.latitude,request.longitude,ground+request.observer_height_m)
        item={'start':(start+timedelta(minutes=i*request.step_minutes)).isoformat().replace('+00:00','Z')}
        for body in ('sun','earth'):
            target=sky[body]
            if not target['azimuth_defined']:
                item[body+'_above_sampled']=None
                item[body+'_horizon_deg']=None
                item[body+'_margin_deg']=None
                item[body+'_sensitivity']=None
                item[body+'_neighbor_coverage_min_km']=None
            else:
                az=target['azimuth_deg']%360
                h=horizon_at(profile,az)
                margin=target['elevation_deg']-h
                lo=math.floor(az/AZIMUTH_STEP_DEG)
                item[body+'_horizon_deg']=round(h,4)
                item[body+'_margin_deg']=round(margin,6)
                item[body+'_above_sampled']=margin>0
                # Two illustrative horizon offsets, not a probability or bound.
                item[body+'_sensitivity']=sensitivity(margin)
                item[body+'_neighbor_coverage_min_km']=min(coverage[lo],coverage[(lo+1)%len(coverage)])
            item[body+'_elevation_deg']=target['elevation_deg']
            item[body+'_azimuth_deg']=target['azimuth_deg'] if target['azimuth_defined'] else None
        samples.append(item)
    # Unknown azimuth is excluded, never interpreted as above or below.
    def count(pred):return sum(pred(b) for b in samples)*request.step_minutes/60
    return {'latitude':request.latitude,'longitude':request.longitude,'observer_height_m':request.observer_height_m,
            'ground_elevation_m':round(ground,2),'start':start.isoformat().replace('+00:00','Z'),
            'end':end.isoformat().replace('+00:00','Z'),'step_minutes':request.step_minutes,
            'azimuth_step_deg':AZIMUTH_STEP_DEG,'min_distance_m':MIN_DISTANCE_M,'radial_step_m':40 if native else RADIAL_STEP_M,'max_distance_km':MAX_DISTANCE_M/1000,
            'horizon_deg':[round(x,4) for x in profile],'coverage_km':coverage,
            'peak_distance_km':peak_distances,'edge_truncated_azimuths':sum(d<MAX_DISTANCE_M/1000 for d in coverage),
            'sensitivity_offset_deg':SENSITIVITY_DEG,'samples':samples,
            'sun_above_sampled_hours':count(lambda b:b['sun_above_sampled'] is True),
            'earth_above_sampled_hours':count(lambda b:b['earth_above_sampled'] is True),
            'both_above_sampled_hours':count(lambda b:b['sun_above_sampled'] is True and b['earth_above_sampled'] is True),
            'unknown_hours':count(lambda b:b['sun_above_sampled'] is None or b['earth_above_sampled'] is None),
            'sun_sensitive_hours':count(lambda b:b['sun_sensitivity']=='changes'),
            'earth_sensitive_hours':count(lambda b:b['earth_sensitivity']=='changes'),
            'terrain_sha256':None if native else SHA256,'terrain_source':'NASA PDS LOLA 80 m and 120 m products' if native else SOURCE,
            'terrain_resolution':request.terrain_resolution,'terrain_source_sha256':source_hashes,'ephemeris_sha256':data.digest,'ephemeris_kind':data.kind,
            'method_version':'lunaris-terrain-0.2','frame':'MOON_ME_DE421','radius_m':R,
            'assumptions':{'projection':'south polar stereographic, east-positive longitude, planetocentric latitude',
                           'height':'observer height above bilinearly interpolated terrain; '+('80/120 m native grids' if native else '400 m grid'),
                           'horizon':'maximum sampled terrain angle with spherical curvature; linear interpolation in azimuth',
                           'geometry':'geometric target centers; no light-time or aberration',
                           'classification':'strictly above sampled horizon at bin midpoint; no fixed clearance',
                           'sensitivity':'fixed +/- 1 degree horizon perturbation, illustrative only; not a terrain-error or confidence bound',
                           'time':'UTC; future leap seconds not predicted'},
            'limits':('80/120 m native grids' if native else '400 m averaged terrain')+', interpolated from 600 m to 300 km or raster edge, whichever comes first; missing near-field, distant and subpixel obstructions, surface uncertainty, finite disks and occultations. Above sampled horizon does not establish visibility; below is also model-dependent. No operational use.'}
