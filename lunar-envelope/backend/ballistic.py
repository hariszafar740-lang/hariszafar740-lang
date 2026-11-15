"""Collisionless test particles under a central lunar point-mass field.

Particles are an illustrative, simultaneous source pulse; no measured density.
"""
import math
import random
from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

router=APIRouter()
MU=4902.800118 # km^3/s^2, JPL DE440
RADIUS=1737.4 # km
K=1.380649e-23
AMU=1.66053906660e-27
MASS={'He':4.002602,'Ar':39.948,'Na':22.989769,'K':39.0983}

class Request(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    species: str = Field(default='Na',pattern='^(He|Ar|Na|K)$')
    temperature_k: float=Field(default=250,ge=50,le=500)
    count:int=Field(default=32,ge=1,le=100)
    duration_s:int=Field(default=900,ge=30,le=1800,multiple_of=30)
    latitude:float=Field(default=-85,ge=-90,le=90)
    longitude:float=Field(default=0,ge=-180,le=180)
    seed:int=Field(default=42,ge=0,le=999999)

def norm(v):return math.sqrt(sum(x*x for x in v))
def accel(p):
    r=norm(p);return tuple(-MU*x/r**3 for x in p)

def advance(p,v,dt):
    a=accel(p);q=tuple(p[i]+v[i]*dt+.5*a[i]*dt*dt for i in range(3));b=accel(q)
    w=tuple(v[i]+.5*(a[i]+b[i])*dt for i in range(3));return q,w

def calculate(req):
    rng=random.Random(req.seed);lat,lon=map(math.radians,(req.latitude,req.longitude))
    up=(math.cos(lat)*math.cos(lon),math.cos(lat)*math.sin(lon),math.sin(lat))
    east=(-math.sin(lon),math.cos(lon),0.);north=(-math.sin(lat)*math.cos(lon),-math.sin(lat)*math.sin(lon),math.cos(lat))
    # Maxwellian flux crossing an ideal plane: tangential Gaussian, outward normal Rayleigh.
    sigma=math.sqrt(K*req.temperature_k/(MASS[req.species]*AMU))/1000
    particles=[]
    for _ in range(req.count):
        ve=rng.gauss(0,sigma);vn=rng.gauss(0,sigma);vu=sigma*math.sqrt(-2*math.log(max(rng.random(),1e-15)))
        particles.append([tuple(RADIUS*x for x in up),tuple(ve*east[j]+vn*north[j]+vu*up[j] for j in range(3)),False])
    frames=[]
    def record(t):
        heights=[max(0,norm(p)-RADIUS) for p,v,landed in particles if not landed]
        frames.append({'time_s':t,'positions_km':[[round(x,4) for x in p] for p,v,landed in particles], 'landed':[landed for p,v,landed in particles], 'airborne':len(heights),'returned':req.count-len(heights),'mean_altitude_km':round(sum(heights)/len(heights),4) if heights else None,'max_altitude_km':round(max(heights),4) if heights else None})
    record(0)
    for t in range(1,req.duration_s+1):
        for particle in particles:
            p,v,landed=particle
            if landed:continue
            q,w=advance(p,v,1.0)
            if norm(q)<=RADIUS:
                # Linear chord/sphere intersection places the return marker on the reference sphere.
                d=tuple(q[i]-p[i] for i in range(3));aa=sum(x*x for x in d);bb=2*sum(p[i]*d[i] for i in range(3));cc=sum(x*x for x in p)-RADIUS**2
                disc=max(0,bb*bb-4*aa*cc); roots=[(-bb-math.sqrt(disc))/(2*aa),(-bb+math.sqrt(disc))/(2*aa)] if aa else [1]
                f=max(0,min(1,next((z for z in roots if z>1e-9 and z<=1+1e-9),1)))
                hit=tuple(p[i]+f*d[i] for i in range(3));n=norm(hit);particle[0]=tuple(x*RADIUS/n for x in hit);particle[1]=w;particle[2]=True
            else:particle[0]=q;particle[1]=w
        if t%30==0:record(t)
    return {'inputs':req.model_dump(),'mu_km3_s2':MU,'radius_km':RADIUS,'integration':'velocity Verlet, 1 s steps; frames every 30 s','frames':frames,'limits':'Simultaneous test-particle pulse with ideal flux-weighted thermal launch; not a physical emission rate or observed exosphere. Moon-fixed launch frame is treated inertial. Spherical central gravity; no terrain, rotation, collisions, radiation pressure, electric fields, photochemistry or re-emission. No density calibration or operational use.'}

@router.post('/api/ballistic-pulse')
def ballistic_pulse(req:Request):return calculate(req)
