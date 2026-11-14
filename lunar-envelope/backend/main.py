"""Phase 1 lunar environment demonstrator. Not flight-qualified."""
from __future__ import annotations
import os
import csv
import io
import math
from pathlib import Path
from fastapi import FastAPI, Query, HTTPException
from . import diviner, ephemeris, donki
from .planner import PlanRequest, compare
from fastapi.responses import StreamingResponse, FileResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict

app = FastAPI(title='Lunar Envelope API', version='0.2.0')

class Scenario(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra='forbid')
    phase: float = Field(default=7.4, ge=0, le=29.53)
    wind: float = Field(default=400, ge=200, le=1000)
    uv: float = Field(default=1, ge=0.1, le=3)
    meteor: float = Field(default=1, ge=0.1, le=5)
    latitude: float = Field(default=-85, ge=-90, le=90)
    longitude: float = Field(default=0, ge=-180, le=180)


def snapshot(s: Scenario):
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
    species = {'He':4.0026, 'Ar':39.948, 'Na':22.990, 'K':39.098}
    base = {'He':6000, 'Ar':4000, 'Na':80, 'K':15} # illustrative surface densities cm^-3
    gases = []
    for name, mass in species.items():
        h = 1.380649e-23*temp/(mass*1.660539e-27*1.62)/1000
        gases.append({'species':name, 'scale_height_km':round(h,1), 'density_100km':round(base[name]*math.exp(-100/h),2)})
    risk = 'HIGH' if abs(potential) >= 25 or dust_density >= .03 else 'ELEVATED' if abs(potential) >= 12 or dust_density >= .012 else 'LOW'
    return {'subsolar_longitude':round(subsolar_lon,2), 'zenith':round(zenith,1), 'temperature':round(temp,1), 'potential':round(potential,1), 'dust_density':round(dust_density,4), 'deposit_rate':round(deposit,6), 'loft_force_ratio':round(loft_ratio,4), 'loft_threshold_met':loft_ratio > 1, 'risk':risk, 'gases':gases, 'illuminated':cosz > 0}

def calculate(s: Scenario):
    """Scenario projection at 6-hour increments; screening only, not EVA safety."""
    current = snapshot(s)
    cumulative = 0.0
    timeline = []
    curve = [{'day': 0, 'efficiency': 100.0}]
    for step in range(120):
        day = step / 4
        phase = (s.phase + day) % 29.53
        tick = snapshot(s.model_copy(update={'phase': phase}))
        timeline.append({'day': day, 'phase': round(phase, 3), 'risk': tick['risk'],
                         'potential': tick['potential'], 'dust_density': tick['dust_density'],
                         'deposit_rate': tick['deposit_rate'], 'illuminated': tick['illuminated']})
        cumulative += tick['deposit_rate'] * 0.25
        if (step + 1) % 4 == 0:
            curve.append({'day': (step + 1)//4, 'efficiency': round(100*math.exp(-0.8*cumulative), 3)})
    windows = []
    for tick in timeline:
        if tick['risk'] == 'LOW' and tick['illuminated']:
            if windows and windows[-1]['end_day'] == tick['day']:
                windows[-1]['end_day'] += 0.25
            else:
                windows.append({'start_day': tick['day'], 'end_day': tick['day']+0.25})
    peak = max(timeline, key=lambda x: x['deposit_rate'])
    current.update({'curve':curve, 'efficiency':curve[-1]['efficiency'], 'timeline':timeline,
                    'screening_windows':windows, 'peak_deposition_day':peak['day'],
                    'cumulative_deposition':round(cumulative, 6)})
    return current

@app.get('/api/health')
def health(): return {'status':'ok'}

@app.post('/api/compare-sites')
def compare_sites(request: PlanRequest):
    try:
        ephemeris.load_table()
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=503, detail='Ephemeris dataset unavailable or failed integrity check') from exc
    try:
        return compare(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=503, detail='Ephemeris dataset unavailable') from exc

@app.get('/api/space-weather')
def space_weather(days:int = Query(default=7,ge=1,le=30)):
    return donki.recent(days)

@app.get('/api/data-catalog')
def data_catalog():
    try:
        count=len(ephemeris.load_table()[0]); ephem_status='available'
    except (ValueError, OSError):
        count=0;ephem_status='unavailable'
    try:
        n=len(diviner.observations()); diviner_status='available'
    except (ValueError, OSError):
        n=0;diviner_status='unavailable'
    return {'datasets':[
        {'name':'JPL DE421 derived vectors','status':ephem_status,'kind':'calculated historical/predictive ephemeris, not live', 'count':count,'coverage':'2026 UTC','source':'https://naif.jpl.nasa.gov/naif/data.html'},
        {'name':'LRO Diviner subset','status':diviner_status,'kind':'historical observations','count':n,'coverage':'sparse south-polar subset','source':diviner.SOURCE_URL},
        {'name':'LRO LOLA terrain','status':'unavailable','kind':'historical topography','coverage':'not installed','source':'https://pgda.gsfc.nasa.gov/products/81'},
        {'name':'LADEE LDEX / NMS / UVS','status':'unavailable','kind':'historical observations','coverage':'not installed','source':'https://sbn.psi.edu/pds/resource/ldex.html'},
        {'name':'NASA DONKI','status':'enabled_unchecked' if os.environ.get('LUNARIS_DONKI_ENABLED') == '1' else 'disabled','kind':'near-real-time event catalogue','coverage':'on-demand; check connection','source':'https://ccmc.gsfc.nasa.gov/tools/DONKI/'}]}

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

@app.post('/api/diviner-comparison')
def diviner_comparison(s: Scenario):
    try:
        observed = diviner.nearest(s.latitude, s.longitude)
    except (OSError, ValueError) as exc:
        return {'status':'unavailable','message':str(exc)}
    if observed['status'] != 'available':
        return observed
    obs = observed['observation']
    # Match the simplified model's local solar time; the historical average has
    # a different season, topography and sampling. Not a rigorous validation.
    subsolar_lon = obs['longitude'] - 15*(obs['local_time_h']-12)
    phase = ((subsolar_lon % 360)/360)*29.53
    model = snapshot(s.model_copy(update={'latitude':obs['latitude'], 'longitude':obs['longitude'], 'phase':phase}))
    return {**observed, 'model_temperature_k':model['temperature'], 'matched_phase_day':round(phase,3),
            'difference_k':round(model['temperature']-obs['temperature_k'],2),
            'comparison_note':'Approximate local-time match only. Historical season, topography and averaging differ; not model validation.'}

@app.post('/api/export-report.pdf')
def export_pdf(s: Scenario):
    result = calculate(s)
    buf = io.BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    pdf.setTitle('Lunaris — illustrative mission brief')
    pdf.setFillColorRGB(.05,.1,.15); pdf.rect(0,0,width,height,fill=1,stroke=0)
    pdf.setFillColorRGB(.55,.9,.92); pdf.setFont('Helvetica-Bold',10); pdf.drawString(42,height-50,'LUNARIS  /  MISSION BRIEF')
    pdf.setFillColorRGB(.92,.95,.96); pdf.setFont('Helvetica-Bold',20); pdf.drawString(42,height-83,'Exploratory scenario report')
    pdf.setFont('Helvetica',9); pdf.setFillColorRGB(.95,.7,.4)
    pdf.drawString(42,height-103,'NOT FLIGHT-QUALIFIED. NOT A SAFE-EVA ASSESSMENT.')
    y=height-140
    lines=[('Site',f'{s.latitude:.1f} deg latitude / {s.longitude:.1f} deg longitude'),
           ('Scenario',f'Phase {s.phase:.1f} d; wind {s.wind:.0f} km/s; UV {s.uv:.1f}x; meteoroids {s.meteor:.1f}x'),
           ('Solar zenith / thermal proxy',f"{result['zenith']} deg / {result['temperature']} K"),
           ('Surface potential proxy',f"{result['potential']} V"),
           ('Dust density proxy',f"{result['dust_density']} particles/cm3"),
           ('30-day projected power retained',f"{result['efficiency']} %"),
           ('Peak deposition proxy',f"day {result['peak_deposition_day']:.2f}"),
           ('Screening windows',f"{len(result['screening_windows'])} candidate intervals; not operational windows")]
    for label,value in lines:
        pdf.setFillColorRGB(.62,.71,.75);pdf.setFont('Helvetica',9);pdf.drawString(42,y,label)
        pdf.setFillColorRGB(.92,.96,.97);pdf.setFont('Helvetica-Bold',10);pdf.drawString(245,y,value);y-=28
    windows=result['screening_windows']
    if windows:
        pdf.setFillColorRGB(.62,.71,.75);pdf.setFont('Helvetica',9)
        pdf.drawString(42,y,'Candidate intervals (days)')
        pdf.setFillColorRGB(.92,.96,.97);pdf.setFont('Helvetica-Bold',9)
        listed=', '.join(f"{w['start_day']:.2f}-{w['end_day']:.2f}" for w in windows[:4])
        if len(windows)>4: listed += ' (see CSV for all)'
        pdf.drawString(245,y,listed);y-=28
    y-=8;pdf.setFillColorRGB(.55,.9,.92);pdf.setFont('Helvetica-Bold',10);pdf.drawString(42,y,'OBSERVATIONS AND LIMITATIONS');y-=22
    try:
        obs=diviner.nearest(s.latitude,s.longitude)
        if obs['status']=='available':
            o=obs['observation']; note=f"Historic Diviner bin: {o['temperature_k']:.2f} K, {obs['nearest_distance_km']:.2f} km away."
        else: note='No bundled Diviner bin is within 2 km of this site.'
    except (OSError,ValueError): note='Diviner subset unavailable.'
    pdf.setFillColorRGB(.8,.86,.88);pdf.setFont('Helvetica',9)
    for line in [note,'Observation and model are not matched in season or terrain.',
                 'Dust, charging, hazard thresholds and power loss are unvalidated proxies.',
                 'Do not use this brief to plan a mission or EVA.',
                 'Data source: NASA PDS LRO Diviner, through a pinned third-party subset.']:
        pdf.drawString(42,y,line);y-=17
    pdf.showPage();pdf.save();buf.seek(0)
    return StreamingResponse(buf,media_type='application/pdf',headers={'Content-Disposition':'attachment; filename="lunar-mission-brief.pdf"'})

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
    w.writerow([]); w.writerow(['Illustrative screening windows — NOT safe EVA windows'])
    w.writerow(['Start day','End day'])
    for window in r['screening_windows']: w.writerow([window['start_day'],window['end_day']])
    w.writerow([]); w.writerow(['Day','Phase (days)','Risk proxy','Illuminated','Dust proxy (particles/cm³)','Deposition proxy (g/m²/day)'])
    for point in r['timeline']:
        w.writerow([point['day'],point['phase'],point['risk'],point['illuminated'],point['dust_density'],point['deposit_rate']])
    out.seek(0)
    return StreamingResponse(iter([out.getvalue().encode('utf-8-sig')]),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="lunar-mission-brief.csv"'})

static = Path(__file__).resolve().parent.parent/'frontend'/'dist'
if static.exists():
    app.mount('/assets', StaticFiles(directory=static/'assets'), name='assets')
    @app.get('/favicon.svg')
    def favicon(): return FileResponse(static/'favicon.svg', media_type='image/svg+xml')
    @app.get('/')
    def index(): return FileResponse(static/'index.html')
