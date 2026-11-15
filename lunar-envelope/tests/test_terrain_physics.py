import math
from backend.terrain_physics import incidence, thermal_step, SIGMA

def test_flat_surface_sun_incidence():
    assert math.isclose(incidence(0,0,0,30),.5,abs_tol=1e-12)
    assert incidence(0,0,0,-10)==0

def test_east_facing_slope():
    assert incidence(-1,0,90,0)>0.70
    assert incidence(-1,0,270,0)==0

def test_thermal_equilibrium_and_cooling():
    t=250; e=.95; f=e*SIGMA*t**4
    assert thermal_step(t,f,0,e,500000,60)==t
    assert thermal_step(t,0,0,e,500000,60)<t
