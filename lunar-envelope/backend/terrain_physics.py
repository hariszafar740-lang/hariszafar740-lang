"""Exploratory terrain-incidence and lumped thermal response at one site."""
import math
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from . import terrain, ephemeris

router = APIRouter()
SIGMA = 5.670374419e-8
SOLAR = 1361.0

class Request(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    latitude: float = Field(default=-85, ge=-90, le=-80)
    longitude: float = Field(default=0, ge=-180, le=180)
    start: datetime = datetime(2026, 11, 14, 12, tzinfo=timezone.utc)
    days: int = Field(default=2, ge=1, le=7)
    albedo: float = Field(default=.12, ge=0, le=.9)
    emissivity: float = Field(default=.95, ge=.5, le=1)
    heat_capacity: float = Field(default=500000, ge=100000, le=5000000)
    initial_temperature: float = Field(default=200, ge=30, le=450)
    @field_validator('start')
    @classmethod
    def aware(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError('Time must include a UTC offset')
        return value.astimezone(timezone.utc)

def destination(lat, lon, az, distance):
    p,l,a=map(math.radians,(lat,lon,az)); d=distance/ephemeris.RADIUS_M
    q=math.asin(math.sin(p)*math.cos(d)+math.cos(p)*math.sin(d)*math.cos(a))
    z=l+math.atan2(math.sin(a)*math.sin(d)*math.cos(p),math.cos(d)-math.sin(p)*math.sin(q))
    return math.degrees(q), ((math.degrees(z)+180)%360)-180

def local_gradient(latitude,longitude,sampler,spacing=400):
    v=[]
    for az in (90,270,0,180):
        lat,lon=destination(latitude,longitude,az,spacing)
        value=sampler(*terrain.projected_xy(lat,lon))
        if value is None: raise ValueError('Slope requires terrain coverage around the site')
        v.append(value)
    east=(v[0]-v[1])/(2*spacing);north=(v[2]-v[3])/(2*spacing)
    return east,north

def incidence(east,north,azimuth,elevation):
    az,el=map(math.radians,(azimuth,elevation))
    se=math.cos(el)*math.sin(az);sn=math.cos(el)*math.cos(az);su=math.sin(el)
    return max(0.,(-east*se-north*sn+su)/math.sqrt(1+east*east+north*north))

def thermal_step(temp, flux, albedo, emissivity, heat_capacity, dt):
    return temp+dt*((1-albedo)*flux-emissivity*SIGMA*temp**4)/heat_capacity

def calculate(req):
    end=req.start+timedelta(days=req.days); eph=ephemeris.select(req.start,end)
    grid=terrain.load_grid();sample=lambda x,y:terrain.sample_xy(grid,x,y)
    h=sample(*terrain.projected_xy(req.latitude,req.longitude))
    if h is None:raise ValueError('Site is outside terrain grid')
    east,north=local_gradient(req.latitude,req.longitude,sample)
    _,profile,coverage,_=terrain.horizon(req.latitude,req.longitude,0)
    T=req.initial_temperature;rows=[]
    for hour in range(req.days*24+1):
        t=req.start+timedelta(hours=hour)
        sun=eph.at(t,req.latitude,req.longitude,h)['sun']
        az=sun['azimuth_deg'];el=sun['elevation_deg']
        horizon=terrain.horizon_at(profile,az) if sun['azimuth_defined'] else None
        visibility=(el>horizon) if horizon is not None else None
        inc=incidence(east,north,az,el) if visibility else 0.
        flux=SOLAR*inc
        rows.append({'time':t.isoformat().replace('+00:00','Z'),'sun_elevation_deg':round(el,3),'sun_azimuth_deg':round(az,3) if sun['azimuth_defined'] else None,'sampled_horizon_deg':round(horizon,3) if horizon is not None else None,'sun_above_sampled_horizon':visibility,'incidence_cosine':round(inc,5) if visibility is not None else None,'incident_w_m2':round(flux,2) if visibility is not None else None,'temperature_k':round(T,2) if visibility is not None else None})
        if visibility is None: raise ValueError('Solar azimuth undefined; cannot determine sampled terrain shadow')
        for _ in range(60): T=thermal_step(T,flux,req.albedo,req.emissivity,req.heat_capacity,60)
    return {'inputs':req.model_dump(mode='json'),'elevation_m':round(h,2),'slope_deg':round(math.degrees(math.atan(math.hypot(east,north))),3),'east_gradient':east,'north_gradient':north,'samples':rows,'ephemeris_sha256':eph.digest,'terrain_sha256':terrain.SHA256,'minimum_horizon_coverage_km':min(coverage),'limits':'400 m averaged LOLA-derived terrain; slope from 400 m offsets; terrain horizon sampled from 600 m to 300 km or grid edge, at 1 degree azimuth. Sub-grid and near-field shadows omitted; not 3D shadow mapping. Solar constant assumed, point Sun. Thermal model is a single lumped layer without conduction or self-heating, using assumed initial temperature, heat capacity, albedo and emissivity; not calibrated or mission-grade. Hourly illumination held constant within each hour.'}

@router.post('/api/terrain-physics')
def terrain_physics(req:Request):
    try:return calculate(req)
    except (terrain.TerrainUnavailable,ephemeris.DataUnavailable) as exc:raise HTTPException(503,str(exc)) from exc
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc
