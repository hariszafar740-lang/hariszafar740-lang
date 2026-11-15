import math
from fastapi.testclient import TestClient
from backend.ballistic import Request,calculate,advance,norm,MU,RADIUS
from backend.main import app

def test_energy_conservation_short_integration():
    p=(RADIUS+100,0.,0.);v=(0.,math.sqrt(MU/norm(p)),0.)
    energy=lambda a,b:sum(x*x for x in b)/2-MU/norm(a)
    original=energy(p,v)
    for _ in range(1000):p,v=advance(p,v,1)
    assert abs(energy(p,v)-original)<1e-8

def test_pulse_deterministic_and_surface_returns():
    req=Request(species='Na',temperature_k=250,count=30,duration_s=1800,seed=4)
    out=calculate(req);assert out==calculate(req)
    assert out['frames'][0]['airborne']==30
    assert out['frames'][-1]['returned']>0
    for frame in out['frames']:
        assert frame['airborne']+frame['returned']==30
        assert all(norm(p)>=RADIUS-0.001 for p in frame['positions_km'])

def test_api_validation():
    client=TestClient(app)
    r=client.post('/api/ballistic-pulse',json={'count':4,'duration_s':60})
    assert r.status_code==200 and len(r.json()['frames'])==3
    assert client.post('/api/ballistic-pulse',json={'count':101}).status_code==422
    assert client.post('/api/ballistic-pulse',json={'species':'unobtainium'}).status_code==422
