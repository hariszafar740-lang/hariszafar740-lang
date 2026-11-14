from datetime import datetime, timezone
import math
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend import ephemeris, donki
from backend.main import app
from backend.planner import PlanRequest, compare

client=TestClient(app)

def test_table_coverage_and_checksum():
    times,vectors=ephemeris.load_table()
    assert len(times)==4381 and times[0]==ephemeris.START and times[-1]==ephemeris.END
    assert ephemeris.vectors_at(times[-1])==vectors[-1]
    with pytest.raises(ValueError): ephemeris.vectors_at(datetime(2026,1,1))
    with pytest.raises(ValueError): ephemeris.vectors_at(datetime(2025,12,31,tzinfo=timezone.utc))

def test_enu_geometric_invariants():
    r=ephemeris.RADIUS_M
    assert ephemeris.local_direction((r+1e8,0,0),0,0)['elevation_deg']==90
    assert abs(ephemeris.local_direction((r,1e8,0),0,0)['elevation_deg'])<1e-6
    assert ephemeris.local_direction((r,1e8,0),0,0)['azimuth_deg']==90
    assert ephemeris.local_direction((r,0,1e8),0,0)['azimuth_deg']==0

# Independently generated with NAIF CSPICE 67 / SpiceyPy azlcpo, DE421 lunar
# kernels, MOON_ME_DE421, abcorr=NONE, spherical Moon radius 1737.4 km.
# This checks five cases, not a global accuracy or scientific validation claim.
@pytest.mark.parametrize('instant,lat,lon,sun_az,sun_el,earth_az,earth_el',[
    ('2026-11-14T12:00:00+00:00',-85,0,120.55087786,-0.98527972,358.08121544,0.87519995),
    ('2026-11-14T13:00:00+00:00',-85,0,120.04468119,-0.94708245,358.02303632,0.92090000),
    ('2026-07-01T01:00:00+00:00',-88,-90,75.78986972,-0.79293983,87.17950541,-4.51126592),
    ('2026-03-20T07:30:00+00:00',0,0,88.46560737,-69.76950912,222.59190137,84.40352435),
    ('2026-12-31T23:00:00+00:00',45,120,46.80318679,-35.57715814,290.67227014,-11.72460819),
])
def test_against_independent_cspice_cases(instant,lat,lon,sun_az,sun_el,earth_az,earth_el):
    r=ephemeris.at_site(datetime.fromisoformat(instant),lat,lon)
    for body,az,el in [('sun',sun_az,sun_el),('earth',earth_az,earth_el)]:
        assert r[body]['azimuth_deg']==pytest.approx(az,abs=.002)
        assert r[body]['elevation_deg']==pytest.approx(el,abs=.002)

def test_compare_two_sites_and_invariants():
    payload={'start':'2026-11-14T12:00:00Z','days':7,'sites':[{'name':'A','latitude':-85,'longitude':0},{'name':'B','latitude':-88,'longitude':-90}]}
    response=client.post('/api/compare-sites',json=payload);assert response.status_code==200
    r=response.json();assert len(r['sites'])==2 and r['step_minutes']==60
    for site in r['sites']:
        assert len(site['timeline'])==168
        assert 0<=site['overlap_hours']<=min(site['sun_hours'],site['earth_hours'])<=168
        assert site['sun_hours']==sum(x['sun_up'] for x in site['timeline'])
        assert site['overlap_hours']==sum(x['sun_up'] and x['earth_up'] for x in site['timeline'])
    assert r['sites'][0]['sun_hours']!=r['sites'][1]['sun_hours']
    assert 'no terrain' in r['limits'].lower()

def test_input_and_coverage_rejected():
    base={'start':'2026-11-14T12:00:00Z','days':7,'sites':[{'name':'A','latitude':-85,'longitude':0}]}
    for changes in [{'start':'2026-11-14T12:00:00'}, {'days':15}, {'start':'2030-12-31T00:00:00Z'}, {'sites':[]}, {'sites':[{'name':'A','latitude':91,'longitude':0}]}]:
        assert client.post('/api/compare-sites',json={**base,**changes}).status_code==422
    p=PlanRequest(**{**base,'start':'2026-11-14T17:00:00+05:00'})
    assert p.start.isoformat()=='2026-11-14T12:00:00+00:00'

def test_catalog_and_no_fabricated_weather(monkeypatch):
    monkeypatch.delenv('LUNARIS_DONKI_ENABLED',raising=False)
    catalog=client.get('/api/data-catalog').json()['datasets']
    assert next(d for d in catalog if d['name']=='JPL DE421 derived vectors')['status']=='available'
    assert next(d for d in catalog if d['name']=='LRO LOLA terrain')['status']=='unavailable'
    weather=client.get('/api/space-weather').json()
    assert weather['status']=='disabled' and weather['events']==[]
    assert client.get('/api/space-weather?days=31').status_code==422

def test_weather_live_source_and_network_failure(monkeypatch):
    monkeypatch.setenv('LUNARIS_DONKI_ENABLED','1')
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,n):return b'[{"activityID":"2026-test","startTime":"2026-11-14T01:00Z","sourceLocation":"S01"}]'
    monkeypatch.setattr(donki,'urlopen',lambda request,timeout:Response())
    donki._fetch.cache_clear()
    result=donki.recent();assert result['status']=='available' and result['events'][0]['id']=='2026-test'
    assert 'not measured lunar conditions' in result['message']
    donki._fetch.cache_clear()
    def fail(*args,**kwargs):raise OSError('offline')
    monkeypatch.setattr(donki,'urlopen',fail)
    result=donki.recent();assert result['status']=='unavailable' and result['events']==[]

def test_integrity_failure_and_interval_arithmetic(monkeypatch,tmp_path):
    broken=tmp_path/'broken.csv';broken.write_text('not a verified dataset')
    ephemeris.load_table.cache_clear();ephemeris.load_extended.cache_clear()
    monkeypatch.setattr(ephemeris,'PATH',broken)
    monkeypatch.setattr(ephemeris,'EXTENDED_PATH',broken)
    with pytest.raises(ValueError,match='checksum'):ephemeris.load_table()
    response=client.post('/api/compare-sites',json={'start':'2026-11-14T12:00:00Z','days':1,'sites':[{'name':'A','latitude':0,'longitude':0}]})
    assert response.status_code==503
    ephemeris.load_table.cache_clear();ephemeris.load_extended.cache_clear()

def test_windows_and_solar_geometry():
    r=compare(PlanRequest(start='2026-11-14T12:00:00Z',days=7,sites=[{'name':'A','latitude':-85,'longitude':0}]))['sites'][0]
    for key,hours in [('sun',r['sun_hours']),('earth',r['earth_hours']),('overlap',r['overlap_hours'])]:
        total=sum((datetime.fromisoformat(w['end'].replace('Z','+00:00'))-datetime.fromisoformat(w['start'].replace('Z','+00:00'))).total_seconds()/3600 for w in r[key+'_windows'])
        assert total==hours
    assert 0<=r['ideal_horizontal_solar_fraction_mean']<=1
    assert r['ideal_horizontal_solar_fraction_mean']==pytest.approx(sum(max(0,math.sin(math.radians(b['sun_elevation_deg']))) for b in r['timeline'])/len(r['timeline']))

@pytest.mark.parametrize('step',[15,30,60])
def test_variable_resolution_intervals(step):
    req=PlanRequest(start='2026-11-14T12:00:00Z',days=2,step_minutes=step,sun_clearance_deg=1.5,earth_clearance_deg=2,sites=[{'name':'A','latitude':-85,'longitude':0}])
    result=compare(req);site=result['sites'][0]
    assert result['step_minutes']==step and len(site['timeline'])==2*24*60//step
    assert result['dataset_sha256']==ephemeris.EXTENDED_SHA256
    assert result['model_version']=='lunaris-geometry-1.2'
    assert site['sun_hours']==sum(x['sun_up'] for x in site['timeline'])*step/60
    assert site['earth_hours']==sum(x['earth_up'] for x in site['timeline'])*step/60
    assert site['overlap_hours']==sum(x['sun_up'] and x['earth_up'] for x in site['timeline'])*step/60
    assert site['overlap_hours_plus_2deg']<=site['overlap_hours']
    assert all(b['sun_up']==(b['sun_elevation_deg']>1.5) and b['earth_up']==(b['earth_elevation_deg']>2) for b in site['timeline'])
    for key,hours in [('sun',site['sun_hours']),('earth',site['earth_hours']),('overlap',site['overlap_hours'])]:
        intervals=site[key+'_windows']
        total=sum((datetime.fromisoformat(w['end'].replace('Z','+00:00'))-datetime.fromisoformat(w['start'].replace('Z','+00:00'))).total_seconds()/3600 for w in intervals)
        assert total==hours
        assert all(a['end']<b['start'] for a,b in zip(intervals,intervals[1:]))

def test_threshold_monotonic_and_default_backward_compatibility():
    base={'start':'2026-11-14T12:00:00Z','days':3,'step_minutes':15,'sites':[{'name':'A','latitude':-85,'longitude':0}]}
    result=compare(PlanRequest(**base))['sites'][0]
    higher=compare(PlanRequest(**base,sun_clearance_deg=2,earth_clearance_deg=2))['sites'][0]
    assert higher['overlap_hours']==result['overlap_hours_plus_2deg']
    assert higher['sun_hours']<=result['sun_hours'] and higher['earth_hours']<=result['earth_hours']
    assert higher['ideal_horizontal_solar_fraction_mean']==result['ideal_horizontal_solar_fraction_mean']
    assert all(0<=t['sun_azimuth_deg']<360 and 0<=t['earth_azimuth_deg']<360 for t in result['timeline'])

def test_invalid_resolution_and_thresholds():
    base={'start':'2026-11-14T12:00:00Z','days':1,'sites':[{'name':'A','latitude':-85,'longitude':0}]}
    for change in [{'step_minutes':5},{'step_minutes':20},{'sun_clearance_deg':-1},{'earth_clearance_deg':11},{'earth_clearance_deg':'NaN'}]:
        assert client.post('/api/compare-sites',json={**base,**change}).status_code==422

def test_max_load_and_end_boundary():
    req={'start':'2026-12-18T00:00:00Z','days':14,'step_minutes':15,'sites':[{'name':str(i),'latitude':-85-i,'longitude':i} for i in range(3)]}
    response=client.post('/api/compare-sites',json=req)
    assert response.status_code==200 and response.json()['end']=='2027-01-01T00:00:00Z'
    assert len(response.json()['sites'][2]['timeline'])==1344
