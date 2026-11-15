"""South-polar overview and geometric routes, using the pinned coarse terrain grid."""
import math
from functools import lru_cache
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from . import terrain, ephemeris

router = APIRouter()
RADIUS_KM = ephemeris.RADIUS_M / 1000
EXTENT = 2 * ephemeris.RADIUS_M * math.tan(math.radians(5))

class Point(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    latitude: float = Field(ge=-90, le=-80)
    longitude: float = Field(ge=-180, le=180)

class Route(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    points: list[Point] = Field(min_length=2, max_length=8)

def vector(p):
    lat, lon = math.radians(p.latitude), math.radians(p.longitude)
    return (math.cos(lat)*math.cos(lon), math.cos(lat)*math.sin(lon), math.sin(lat))

def segment(a,b):
    u,v=vector(a),vector(b)
    dot=max(-1,min(1,sum(x*y for x,y in zip(u,v))))
    angle=math.acos(dot)
    steps=max(1,math.ceil(angle*RADIUS_KM/5))
    for i in range(steps+1):
        f=i/steps
        if angle < 1e-9: w=u
        else:
            x,y=math.sin((1-f)*angle)/math.sin(angle),math.sin(f*angle)/math.sin(angle)
            w=tuple(x*aa+y*bb for aa,bb in zip(u,v))
        yield f,math.degrees(math.asin(max(-1,min(1,w[2])))),math.degrees(math.atan2(w[1],w[0])),angle*RADIUS_KM

@lru_cache(maxsize=1)
def overview():
    grid=terrain.load_grid(); size=160; vals=[]
    for row in range(size):
        y=EXTENT*(1-2*row/(size-1))
        for col in range(size):
            x=EXTENT*(2*col/(size-1)-1)
            h=terrain.sample_xy(grid,x,y) if x*x+y*y<=EXTENT*EXTENT else None
            vals.append(None if h is None else round(h))
    return {'size':size,'extent_m':EXTENT,'elevation_m':vals,'min_m':min(x for x in vals if x is not None),'max_m':max(x for x in vals if x is not None),'source':terrain.SOURCE,'sha256':terrain.SHA256,'grid_spacing_m':400,'radius_m':ephemeris.RADIUS_M}

@router.get('/api/south-pole-map')
def map_data():
    try:return overview()
    except terrain.TerrainUnavailable as e:raise HTTPException(status_code=503,detail=str(e)) from e

@router.post('/api/south-pole-route')
def route(request:Route):
    try:grid=terrain.load_grid()
    except terrain.TerrainUnavailable as e:raise HTTPException(status_code=503,detail=str(e)) from e
    samples=[]; total=0
    for i in range(len(request.points)-1):
        for j,(f,lat,lon,distance) in enumerate(segment(request.points[i],request.points[i+1])):
            if i and not j:continue
            x,y=terrain.projected_xy(lat,lon);elev=terrain.sample_xy(grid,x,y)
            samples.append({'latitude':round(lat,7),'longitude':round(lon,7),'distance_km':round(total+f*distance,4),'elevation_m':None if elev is None else round(elev,2)})
        total+=distance
    return {'distance_km':round(total,4),'samples':samples,'radius_km':RADIUS_KM,'source':terrain.SOURCE,'sha256':terrain.SHA256,'limits':'Spherical shortest surface arcs, not a spacecraft trajectory or feasible traverse. Elevation is bilinear interpolation of the 400 m derivative, approximately 5 km along-route samples; missing and sub-grid hazards are not represented.'}

class Sites(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    points: list[Point] = Field(min_length=1, max_length=8)

@router.post('/api/south-pole-elevations')
def elevations(request:Sites):
    try:grid=terrain.load_grid()
    except terrain.TerrainUnavailable as e:raise HTTPException(status_code=503,detail=str(e)) from e
    return {'sites':[{'latitude':p.latitude,'longitude':p.longitude,'elevation_m':round(terrain.sample_xy(grid,*terrain.projected_xy(p.latitude,p.longitude)),2)} for p in request.points], 'source':terrain.SOURCE,'sha256':terrain.SHA256,'reference':'meters above a 1737.4 km reference sphere; bilinear interpolation of the averaged 400 m derivative'}
