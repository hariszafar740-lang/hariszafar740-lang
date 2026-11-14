"""Phase 1 lunar environment demonstrator. Not flight-qualified."""
from __future__ import annotations
import csv
import io
import math
from pathlib import Path
from fastapi import FastAPI, Query
from . import diviner
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict

app = FastAPI(title='Lunar Envelope API', version='0.1.0')

class Scenario(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra='forbid')
    phase: float = Field(default=7.4, ge=0, le=29.53)
    wind: float = Field(default=400, ge=200, le=1000)
    uv: float = Field(default=1, ge=0.1, le=3)
    meteor: float = Field(default=1, ge=0.1, le=5)
    latitude: float = Field(default=-85, ge=-90, le=90)
    longitude: float = Field(default=0, ge=-180, le=180)


def calculate(s: Scenario):
    # Fixed equatorial subsolar latitude; phase 0 puts noon at longitude 0.
    subsolar_lon = (s.phase / 29.53 * 360 + 180) % 360 - 180
    cosz = math.cos(math.radians(s.latitude))*math.cos(math.radians(s.longitude-subsolar_lon))
    zenith = math.degrees(math.acos(max(-1, min(1, cosz))))
    light = max(0., cosz)
    # Grey-body temperature interpolation, not a Diviner map or terrain model.
    temp = (95**4 + light * (390**4 - 95**4))**0.25
    # Monotone idealized current balance in microamps/m². Saturating electron/ion
    # currents are proxies for OML collection, not a kinetic sheath solution.
    electron = 0.55 * s.wind / 400
    ion = 0.025 * s.wind / 400
    photo = 4.5 * s.uv * light
    def balance(v):
        je = electron * (math.exp(max(-100, v/12)) if v < 0 else 1 + v/12)
        ji = ion * (1 - v/15 if v < 0 else math.exp(max(-100, -v/15)))
        jp = photo * (math.exp(max(-100, -v/2)) if v > 0 else 1)
        return ji + jp - je
    lo, hi = -200., 100.
    for _ in range(70):
        mid = (lo + hi)/2
        if balance(mid) > 0: lo = mid
        else: hi = mid
    potential = (lo + hi)/2
    # Illustrative near-surface 1-micron grains; cohesion is a parameterized,
    # highly uncertain effective value (not measured lunar cohesion).
    radius = 1e-6
    grain_mass = 4/3*math.pi*radius**3*3000
    charge = 4*math.pi*8.854e-12*radius*potential
    field = abs(potential)/0.05  # assumed sheath scale [m]
    electrical_force = abs(charge)*field
    resisting_force = grain_mass*1.62 + 1e-13
    loft_ratio = electrical_force/resisting_force
    # Scaled dust proxy retains meteoroid ejecta even below loft threshold.
    terminator = math.exp(-((zenith-90)/13)**2)
    dust_density = (0.003*s.meteor + 0.018*terminator*s.meteor*(s.wind/400))
    deposit = (0.00012*s.meteor + 0.00035*terminator*s.meteor*s.wind/400) # g/m²/day, scenario proxy
    # Beer-Lambert attenuation with assumed mass extinction [m²/g].
    curve = [{'day': day, 'efficiency': round(100*math.exp(-0.8*deposit*day),3)} for day in range(31)]
    species = {'He':4.0026, 'Ar':39.948, 'Na':22.990, 'K':39.098}
    base = {'He':6000, 'Ar':4000, 'Na':80, 'K':15} # illustrative surface densities cm^-3
    gases = []
    for name, mass in species.items():
        h = 1.380649e-23*temp/(mass*1.660539e-27*1.62)/1000
        gases.append({'species':name, 'scale_height_km':round(h,1), 'density_100km':round(base[name]*math.exp(-100/h),2)})
    risk = 'HIGH' if abs(potential) >= 25 or dust_density >= .03 else 'ELEVATED' if abs(potential) >= 12 or dust_density >= .012 else 'LOW'
    return {'subsolar_longitude':round(subsolar_lon,2), 'zenith':round(zenith,1), 'temperature':round(temp,1), 'potential':round(potential,1), 'dust_density':round(dust_density,4), 'deposit_rate':round(deposit,6), 'loft_force_ratio':round(loft_ratio,4), 'loft_threshold_met':loft_ratio > 1, 'efficiency':curve[-1]['efficiency'], 'risk':risk, 'curve':curve, 'gases':gases, 'illuminated':cosz > 0}

@app.get('/api/health')
def health(): return {'status':'ok'}

@app.post('/api/simulate')
def simulate(s: Scenario): return calculate(s)

@app.get('/api/nasa-data')
def nasa_data():
    try:
        count = len(diviner.observations())
    except (OSError, ValueError) as exc:
        return {'status': 'unavailable', 'message': f'Diviner subset could not be loaded: {exc}', 'observations': []}
    return {'status':'available', 'dataset':'LRO Diviner polar cumulative product', 'count':count,
            'source_url':diviner.SOURCE_URL, 'mirror_url':diviner.MIRROR_URL,
            'message':'Historic subset; limited locations and observing conditions. Not a live feed.'}

@app.get('/api/diviner')
def diviner_nearest(latitude: float = Query(ge=-90, le=90, allow_inf_nan=False),
                    longitude: float = Query(ge=-180, le=180, allow_inf_nan=False)):
    try:
        return diviner.nearest(latitude, longitude)
    except (OSError, ValueError) as exc:
        return {'status':'unavailable', 'message':f'Diviner subset could not be loaded: {exc}'}

@app.post('/api/export-report')
def export_report(s: Scenario):
    r=calculate(s)
    out=io.StringIO(newline='')
    w=csv.writer(out)
    w.writerow(['Lunar Envelope — illustrative simulation, not operational guidance'])
    w.writerow(['Parameter','Value','Unit'])
    for row in [('Phase',s.phase,'lunar day'),('Solar wind speed',s.wind,'km/s'),('UV flux multiplier',s.uv,'relative'),('Meteoroid flux multiplier',s.meteor,'relative'),('Latitude',s.latitude,'degrees'),('Longitude',s.longitude,'degrees'),('Solar zenith angle',r['zenith'],'degrees'),('Surface temperature proxy',r['temperature'],'K'),('Surface potential proxy',r['potential'],'V'),('Dust density proxy',r['dust_density'],'particles/cm³'),('Dust deposition proxy',r['deposit_rate'],'g/m²/day'),('30-day power retained',r['efficiency'],'%'),('Hazard category',r['risk'],'illustrative')]: w.writerow(row)
    try:
        observed = diviner.nearest(s.latitude, s.longitude)
        w.writerow([]); w.writerow(['Historical Diviner reference — not a matched-time validation'])
        w.writerow(['Product', diviner.PRODUCT, ''])
        w.writerow(['PDS label URL', diviner.SOURCE_URL, ''])
        if observed['status'] == 'available':
            obs = observed['observation']
            w.writerow(['Brightness temperature', obs['temperature_k'], 'K'])
            w.writerow(['Historical local solar time', obs['local_time_h'], 'hour'])
            w.writerow(['Observation latitude', obs['latitude'], 'degrees'])
            w.writerow(['Observation longitude', obs['longitude'], 'degrees'])
            w.writerow(['Distance to selected site', observed['nearest_distance_km'], 'km'])
        else:
            w.writerow(['No reference within 2 km', observed['nearest_distance_km'], 'km to nearest subset bin'])
    except (OSError, ValueError):
        w.writerow(['Diviner reference unavailable', '', ''])
    w.writerow([]); w.writerow(['Day','Power retained (%)'])
    for point in r['curve']: w.writerow([point['day'],point['efficiency']])
    out.seek(0)
    return StreamingResponse(iter([out.getvalue().encode('utf-8-sig')]),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="lunar-mission-brief.csv"'})

static = Path(__file__).resolve().parent.parent/'frontend'/'dist'
if static.exists():
    app.mount('/assets', StaticFiles(directory=static/'assets'), name='assets')
    @app.get('/')
    def index(): return FileResponse(static/'index.html')
