import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend import ephemeris, events
from backend.main import app
from backend.planner import compare, PlanRequest

UTC=timezone.utc
client=TestClient(app)

# CSPICE azlcpo test vectors use the SAME source kernels but a different NAIF
# calculation route. Software cross-check only, not independent science review.
@pytest.mark.parametrize('row',list(csv.DictReader((Path(__file__).parent/'cspice_reference.csv').open())))
def test_120_cspice_reference_cases(row):
    ds=ephemeris.select(ephemeris.EXTENDED_START,ephemeris.EXTENDED_END)
    at=datetime.fromisoformat(row['utc'].replace('Z','+00:00'))
    result=ds.at(at,float(row['latitude']),float(row['longitude']),float(row['height_m']))[row['body'].lower()]
    assert result['elevation_deg']==pytest.approx(float(row['elevation_deg']),abs=.001)
    assert abs((result['azimuth_deg']-float(row['azimuth_deg'])+180)%360-180)<.002
    # Range is approximate; tolerance is specific to these selected cases.
    assert result['distance_km']==pytest.approx(float(row['distance_km']),abs=15 if row['body']=='SUN' else 1.1)

def test_extended_coverage_and_utc_conversions():
    table=ephemeris.load_extended()
    assert len(table[0])==48217 and table[0][0]==ephemeris.EXTENDED_START and table[0][-1]==ephemeris.EXTENDED_END
    ds=ephemeris.select(table[0][0],table[0][-1]); assert ds.at(table[0][-1],0,0)['sun']['distance_km']>0
    with pytest.raises(ValueError): ds.at(datetime(2027,1,1),0,0)
    with pytest.raises(ValueError):ephemeris.select(datetime(2019,12,31,tzinfo=UTC),datetime(2020,1,1,tzinfo=UTC))
    assert compare(PlanRequest(start='2028-01-01T05:00:00+05:00',days=1,sites=[{'name':'A','latitude':-85,'longitude':0}]))['start']=='2028-01-01T00:00:00Z'

def test_verified_2026_fallback_and_corruption(monkeypatch,tmp_path):
    broken=tmp_path/'bad.csv';broken.write_text('broken')
    ephemeris.load_extended.cache_clear();ephemeris.load_table.cache_clear()
    monkeypatch.setattr(ephemeris,'EXTENDED_PATH',broken)
    a=compare(PlanRequest(start='2026-01-01T00:00Z',days=1,sites=[{'name':'A','latitude':0,'longitude':0}]))
    assert a['dataset_kind']=='2026 fallback' and a['dataset_sha256']==ephemeris.SHA256
    assert client.post('/api/compare-sites',json={'start':'2028-01-01T00:00Z','days':1,'sites':[{'name':'A','latitude':0,'longitude':0}]}).status_code==503
    assert 'fallback' in client.get('/api/data-catalog').json()['datasets'][0]['coverage']
    monkeypatch.setattr(ephemeris,'PATH',broken);ephemeris.load_table.cache_clear()
    assert client.post('/api/compare-sites',json={'start':'2026-01-01T00:00Z','days':1,'sites':[{'name':'A','latitude':0,'longitude':0}]}).status_code==503
    ephemeris.load_extended.cache_clear();ephemeris.load_table.cache_clear()

def test_synthetic_crossings_no_crossing_and_overlap():
    start=datetime(2026,1,1,tzinfo=UTC);end=start+timedelta(hours=1)
    def rising(t):return (t-start).total_seconds()-1234
    windows,transitions=events.threshold_windows(start,end,timedelta(minutes=15),rising,0)
    assert len(windows)==len(transitions)==1 and transitions[0]['kind']=='rise'
    assert abs((windows[0][0]-(start+timedelta(seconds=1234))).total_seconds())<1
    falling=lambda t: 2800-(t-start).total_seconds()
    other,ts=events.threshold_windows(start,end,timedelta(minutes=15),falling,0)
    assert ts[0]['kind']=='set'
    overlap=events.intersect(windows,other)
    assert len(overlap)==1 and abs((overlap[0][1]-overlap[0][0]).total_seconds()-1566)<2
    assert events.threshold_windows(start,end,timedelta(minutes=15),lambda t:-1,0)==([],[])
    assert events.threshold_windows(start,end,timedelta(minutes=15),lambda t:1,0)==([(start,end)],[])

def test_refined_window_arithmetic_and_bounds():
    r=compare(PlanRequest(start='2026-11-14T12:00Z',days=7,sites=[{'name':'A','latitude':-85,'longitude':0,'height_m':100}]))
    s=r['sites'][0]; assert s['height_m']==100
    for body in ('sun','earth','overlap'):
        wins=s['refined'][body+'_windows']; duration=0
        for w in wins:
            a=datetime.fromisoformat(w['start'].replace('Z','+00:00'));b=datetime.fromisoformat(w['end'].replace('Z','+00:00'))
            assert datetime.fromisoformat(r['start'].replace('Z','+00:00'))<=a<b<=datetime.fromisoformat(r['end'].replace('Z','+00:00'))
            duration+=(b-a).total_seconds()/3600
        assert s['refined'][body+'_hours']==pytest.approx(duration,abs=.0001)
    assert s['refined']['overlap_hours']<=min(s['refined']['sun_hours'],s['refined']['earth_hours'])+.0001
    assert 'grazing' in r['limits'] and 'tangent plane' in r['limits']

def test_height_and_date_validation():
    base={'start':'2028-01-01T00:00Z','days':1,'sites':[{'name':'A','latitude':0,'longitude':0,'height_m':100}]}
    assert client.post('/api/compare-sites',json=base).status_code==200
    for bad in (-1,1001,'NaN'):
        assert client.post('/api/compare-sites',json={**base,'sites':[{'name':'A','latitude':0,'longitude':0,'height_m':bad}]}).status_code==422
    assert client.post('/api/compare-sites',json={**base,'start':'2030-12-31T01:00Z'}).status_code==422

@pytest.mark.parametrize('row',list(csv.DictReader((Path(__file__).parent/'cspice_crossings.csv').open())))
def test_selected_cspice_transition_cases(row):
    # Direct CSPICE/azlcpo reference with separate five-minute scan, same kernels.
    req=PlanRequest(start=row['start'],days=int(row['days']),sites=[{'name':'ref','latitude':float(row['latitude']),'longitude':float(row['longitude'])}])
    site=compare(req)['sites'][0]
    reference=datetime.fromisoformat(row['utc'].replace('Z','+00:00'))
    matching=[datetime.fromisoformat(e['time'].replace('Z','+00:00')) for e in site['refined'][row['body'].lower()+'_transitions'] if e['kind']==row['kind']]
    assert matching and min(abs((t-reference).total_seconds()) for t in matching)<30

def test_undefined_azimuth_and_ranges():
    r=ephemeris.RADIUS_M
    assert not ephemeris.local_direction((r+10000,0,0),0,0)['azimuth_defined']
    assert ephemeris.local_direction((r,10000,0),0,0)['azimuth_defined']
    horizon=ephemeris.local_direction((r,1e8,0),0,0,1000)
    assert horizon['elevation_deg']<0

def test_numerical_interpolation_preserves_vector_range():
    ds=ephemeris.select(ephemeris.EXTENDED_START,ephemeris.EXTENDED_END)
    t=datetime(2026,11,14,13,tzinfo=UTC)
    result=ds.at(t,-85,0)['sun']
    # The former raw-vector lerp shrank apparent range by about 6000 km here.
    row=next(r for r in csv.DictReader((Path(__file__).parent/'cspice_reference.csv').open()) if r['utc']=='2026-11-14T13:00:00Z' and r['latitude']=='-85' and r['body']=='SUN')
    assert abs(result['distance_km']-float(row['distance_km']))<15

@pytest.mark.parametrize('row',list(csv.DictReader((Path(__file__).parent/'horizons_reference.csv').open())))
def test_60_horizons_de441_reference_cases(row):
    # Positions from NASA/JPL Horizons DE441, geometric Moon-center ICRF.
    # Reference transforms use shared DE421 lunar-frame kernels: not an
    # independent frame/orientation benchmark or external scientific audit.
    ds=ephemeris.select(ephemeris.EXTENDED_START,ephemeris.EXTENDED_END)
    at=datetime.fromisoformat(row['utc'].replace('Z','+00:00'))
    got=ds.at(at,float(row['latitude']),float(row['longitude']),float(row['height_m']))[row['body'].lower()]
    assert got['elevation_deg']==pytest.approx(float(row['elevation_deg']),abs=.001)
    assert abs((got['azimuth_deg']-float(row['azimuth_deg'])+180)%360-180)<.002
    assert got['distance_km']==pytest.approx(float(row['distance_km']),abs=15 if row['body']=='SUN' else 1.1)

def test_start_extremes_and_bad_scan_rejected():
    data={'days':1,'sites':[{'name':'A','latitude':0,'longitude':0}]}
    for start in ('9999-12-31T23:59:59Z','2019-12-31T23:59:59Z','2031-01-01T00:00:00Z'):
        assert client.post('/api/compare-sites',json={**data,'start':start}).status_code==422
    t=datetime(2026,1,1,tzinfo=UTC)
    with pytest.raises(ValueError):events.threshold_windows(t,t+timedelta(hours=1),timedelta(0),lambda x:1,0)
    with pytest.raises(ValueError):events.threshold_windows(t+timedelta(hours=1),t,timedelta(minutes=15),lambda x:1,0)

@pytest.mark.parametrize('row',list(csv.DictReader((Path(__file__).parent/'horizons_independent_axes_reference.csv').open())))
def test_horizons_independent_lunar_orientation(row):
    # Horizons supplies DE441 vectors AND lunar axis orientations from separate
    # site-to-Moon vectors. No local SPICE kernels create this reference.
    ds=ephemeris.select(ephemeris.EXTENDED_START,ephemeris.EXTENDED_END)
    at=datetime.fromisoformat(row['utc'].replace('Z','+00:00'))
    got=ds.at(at,float(row['latitude']),float(row['longitude']),float(row['height_m']))[row['body'].lower()]
    assert got['elevation_deg']==pytest.approx(float(row['elevation_deg']),abs=.001)
    assert abs((got['azimuth_deg']-float(row['azimuth_deg'])+180)%360-180)<.002
    assert got['distance_km']==pytest.approx(float(row['distance_km']),abs=15 if row['body']=='SUN' else 1.1)

def test_horizons_reference_reproduction_and_direct_topocentric_vectors(tmp_path):
    import math,subprocess,sys
    folder=Path(__file__).parent
    generated=tmp_path/'reference.csv'
    subprocess.run([sys.executable,str(folder.parent/'scripts/generate_horizons_axes_reference.py'),str(folder/'horizons_lunar_axes.csv'),str(folder/'horizons_de441_icrf.csv'),str(generated)],check=True)
    assert generated.read_bytes()==(folder/'horizons_independent_axes_reference.csv').read_bytes()
    axes={}
    for r in csv.DictReader((folder/'horizons_lunar_axes.csv').open()):axes.setdefault(r['utc'],{})[r['axis']]=[float(r[k]) for k in ('x_km','y_km','z_km')]
    earth={r['utc']:r for r in csv.DictReader((folder/'horizons_de441_icrf.csv').open()) if r['body']=='EARTH'}
    for row in csv.DictReader((folder/'horizons_earth_site_85s.csv').open()):
        # Vectors in axes file point from the axis site to the Moon center.
        v=axes[row['utc']];b=earth[row['utc']];phi=math.radians(-85)
        for i,key in enumerate(('x_km','y_km','z_km')):
            calculated=float(b[key])+math.cos(phi)*v['X'][i]+math.sin(phi)*v['Z'][i]
            assert calculated==pytest.approx(float(row[key]),abs=1e-6)
