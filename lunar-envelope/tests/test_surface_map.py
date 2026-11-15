import math
from fastapi.testclient import TestClient
from backend.main import app
from backend import terrain
from backend.surface_map import Point,segment,RADIUS_KM
client=TestClient(app)
def test_great_circle_quarter_degree_and_endpoints():
    a=Point(latitude=-85,longitude=0);b=Point(latitude=-85,longitude=90)
    samples=list(segment(a,b))
    assert samples[0][1:3]==(-85.0,0.0)
    assert abs(samples[-1][1]+85)<1e-8 and abs(samples[-1][2]-90)<1e-8
    expected=math.acos(math.sin(math.radians(-85))**2)*RADIUS_KM
    assert abs(samples[-1][3]-expected)<1e-8

def test_map_and_route_use_actual_pinned_grid():
    m=client.get('/api/south-pole-map');assert m.status_code==200
    data=m.json();assert data['sha256']==terrain.SHA256 and len(data['elevation_m'])==160**2
    result=client.post('/api/south-pole-route',json={'points':[{'latitude':-85,'longitude':0},{'latitude':-85,'longitude':90}]}).json()
    assert result['distance_km']>0 and len(result['samples'])>2
    grid=terrain.load_grid();x,y=terrain.projected_xy(-85,0)
    assert abs(result['samples'][0]['elevation_m']-terrain.sample_xy(grid,x,y))<.01
    assert client.post('/api/south-pole-route',json={'points':[{'latitude':0,'longitude':0},{'latitude':-85,'longitude':0}]}).status_code==422

def test_site_elevations_and_missing_raster(monkeypatch):
    point={'latitude':-85,'longitude':0}
    r=client.post('/api/south-pole-elevations',json={'points':[point]})
    assert r.status_code==200
    grid=terrain.load_grid()
    assert abs(r.json()['sites'][0]['elevation_m']-terrain.sample_xy(grid,*terrain.projected_xy(-85,0)))<.01
    def unavailable():raise terrain.TerrainUnavailable('missing raster')
    monkeypatch.setattr(terrain,'load_grid',unavailable)
    assert client.post('/api/south-pole-elevations',json={'points':[point]}).status_code==503
