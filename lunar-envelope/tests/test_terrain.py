import json
import math
from datetime import datetime,timezone
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend import terrain
from backend.main import app

client=TestClient(app)
REFERENCE=json.loads((Path(__file__).parent/'upstream_coarse_horizon_reference.json').read_text())
BASE={'start':'2026-11-14T12:00:00Z','days':1,'step_minutes':60,'latitude':-85,'longitude':0,'observer_height_m':2}

def test_upstream_raster_decoding_reference():
    grid=terrain.load_grid()
    assert sum(grid)==REFERENCE['sum']
    for row,col,value in REFERENCE['samples']:
        assert grid[row*terrain.SIZE+col]==value
    assert terrain.sample_xy(grid,0,0)==pytest.approx((grid[1139*2280+1139]+grid[1139*2280+1140]+grid[1140*2280+1139]+grid[1140*2280+1140])/4)
    assert terrain.sample_xy(grid,1e9,0) is None

@pytest.mark.parametrize('site',REFERENCE['sites'])
def test_upstream_horizon_comparison_with_different_sampling(site):
    ground,p,coverage,peaks=terrain.horizon(site['lat'],site['lon'],2)
    assert ground==pytest.approx(site['hSite'],abs=1e-6)
    # Reference uses 0.1 km near-field steps and up to 300 km; this model
    # uses 100 m steps to 300 km or the raster edge. Not a scientific bound.
    diff=[abs(p[2*i]-e) for i,e in enumerate(site['el2'])]
    assert max(diff)<0.012

def test_projection_and_periodic_interpolation():
    x,y=terrain.projected_xy(-85,0);assert x==pytest.approx(0,abs=1e-8) and y>0
    x,y=terrain.projected_xy(-85,90);assert x>0 and y==pytest.approx(0,abs=1e-8)
    p=list(range(360));assert terrain.horizon_at(p,359.5)==pytest.approx(179.5)
    assert terrain.horizon_at(p,-.5)==pytest.approx(terrain.horizon_at(p,359.5))
    assert terrain.elevation_angle(terrain.R,terrain.R,1000/terrain.R)==pytest.approx(-math.degrees(1000/(2*terrain.R)))

def test_flat_sphere_and_height(monkeypatch):
    terrain.horizon.cache_clear()
    monkeypatch.setattr(terrain,'load_grid',lambda:None)
    monkeypatch.setattr(terrain,'sample_xy',lambda grid,x,y:0)
    zero,p,_,peaks=terrain.horizon(-85,0,0)
    assert zero==0 and all(v==pytest.approx(-math.degrees(600/(2*terrain.R)),abs=1e-9) for v in p)
    assert peaks==(0.6,)*360
    _,raised,_,_=terrain.horizon(-85,0,100)
    assert all(raised[i]<p[i] for i in range(360))
    terrain.horizon.cache_clear()

def test_api_sample_and_bounds():
    r=client.post('/api/terrain-screen',json=BASE);assert r.status_code==200
    d=r.json();assert len(d['horizon_deg'])==360 and len(d['samples'])==24
    assert d['min_distance_m']==600 and d['max_distance_km']==300 and len(d['coverage_km'])==len(d['peak_distance_km'])==360
    assert all(.6<=peak<=end<=300 for peak,end in zip(d['peak_distance_km'],d['coverage_km']))
    assert d['edge_truncated_azimuths']==sum(v<300 for v in d['coverage_km'])
    assert d['sensitivity_offset_deg']==.25 and 'not a terrain-error' in d['assumptions']['sensitivity']
    for body in ('sun','earth'):
        assert d[body+'_sensitive_hours']==sum(s[body+'_sensitivity']=='changes' for s in d['samples'])
        for s in d['samples']:
            assert 0.6<=s[body+'_neighbor_coverage_min_km']<=300
            assert s[body+'_sensitivity'] in ('changes','unchanged')
    assert 0 < min(d['coverage_km']) <= max(d['coverage_km']) <= 300
    assert d['terrain_sha256']==terrain.SHA256 and d['unknown_hours']==0
    assert d['ground_elevation_m']==pytest.approx(-693.33,abs=.01)
    assert d['both_above_sampled_hours']<=min(d['sun_above_sampled_hours'],d['earth_above_sampled_hours'])
    assert 'does not establish visibility' in d['limits']
    for change in ({'latitude':-79}, {'longitude':181}, {'observer_height_m':-1},{'start':'2026-01-01T00:00'}, {'days':15},{'start':'2030-12-31T23:00:00Z'}):
        assert client.post('/api/terrain-screen',json={**BASE,**change}).status_code==422

def test_missing_or_modified_dem_fails_closed(monkeypatch,tmp_path):
    bad=tmp_path/'broken.gz';bad.write_bytes(b'bad')
    terrain.horizon.cache_clear();terrain.load_grid.cache_clear()
    with monkeypatch.context() as m:
        m.setattr(terrain,'PATH',bad)
        assert client.post('/api/terrain-screen',json=BASE).status_code==503
        assert next(d for d in client.get('/api/data-catalog').json()['datasets'] if d['name']=='LRO LOLA terrain')['status']=='unavailable'
    terrain.load_grid.cache_clear();terrain.horizon.cache_clear()

@pytest.mark.parametrize('margin,expected',[
    (-.251,'unchanged'),(-.25,'unchanged'),(-.249,'changes'),(0,'changes'),
    (.25,'changes'),(.251,'unchanged')])
def test_illustrative_sensitivity_boundaries(margin,expected):
    # Strictly above both perturbed horizons; this band is not an uncertainty bound.
    assert terrain.sensitivity(margin)==expected
    assert ((margin > -.25) != (margin > .25)) == (expected=='changes')


def test_unknown_azimuth_is_not_counted(monkeypatch):
    from backend.main import TerrainRequest
    class Data:
        digest='test';kind='test'
        def at(self,*args):
            return {'sun':{'azimuth_defined':False,'elevation_deg':90},'earth':{'azimuth_defined':True,'elevation_deg':1,'azimuth_deg':359.5}}
    monkeypatch.setattr(terrain.ephemeris,'select',lambda *args:Data())
    monkeypatch.setattr(terrain,'horizon',lambda *args:(0,(0,)*360,(100,)*360,(1,)*360))
    d=terrain.screen(TerrainRequest(**BASE))
    assert d['unknown_hours']==24 and d['sun_above_sampled_hours']==0 and d['both_above_sampled_hours']==0
    assert d['earth_above_sampled_hours']==24 and d['sun_sensitive_hours']==0
    assert d['samples'][0]['sun_sensitivity'] is None and d['samples'][0]['sun_neighbor_coverage_min_km'] is None
