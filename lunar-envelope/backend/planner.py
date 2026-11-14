"""Site/date comparison. Geometric screening, not a safety/mission assessment."""
from datetime import datetime, timedelta, timezone
from typing import Literal
import math
from pydantic import BaseModel, Field, ConfigDict, field_validator
from . import ephemeris

class Site(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    name: str=Field(min_length=1,max_length=40)
    latitude:float=Field(ge=-90,le=90)
    longitude:float=Field(ge=-180,le=180)

class PlanRequest(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    start: datetime
    days: int=Field(default=7,ge=1,le=14)
    sites: list[Site]=Field(min_length=1,max_length=3)
    step_minutes: Literal[15,30,60] = 60
    sun_clearance_deg: float = Field(default=0, ge=0, le=10)
    earth_clearance_deg: float = Field(default=0, ge=0, le=10)
    @field_validator('start')
    @classmethod
    def utc_time(cls,v):
        if v.tzinfo is None or v.utcoffset() is None: raise ValueError('Include a timezone, for example Z for UTC')
        return v.astimezone(timezone.utc)


def compare(request:PlanRequest):
    end=request.start+timedelta(days=request.days)
    if request.start<ephemeris.START or end>ephemeris.END:
        raise ValueError('The full interval must lie between 2026-01-01 and 2027-01-01 UTC')
    def z(dt): return dt.isoformat().replace('+00:00','Z')
    sites=[]
    for site in request.sites:
        now=ephemeris.at_site(request.start,site.latitude,site.longitude)
        bins=[]
        for step in range(request.days*24*60//request.step_minutes):
            time=request.start+timedelta(minutes=step*request.step_minutes)
            mid=ephemeris.at_site(time+timedelta(minutes=request.step_minutes/2),site.latitude,site.longitude)
            solar=mid['sun']['elevation_deg']; earth=mid['earth']['elevation_deg']
            bins.append({'start':z(time),'sun_up':solar>request.sun_clearance_deg,'earth_up':earth>request.earth_clearance_deg,
                         'sun_elevation_deg':solar,'earth_elevation_deg':earth,
                         'sun_azimuth_deg':mid['sun']['azimuth_deg'],'earth_azimuth_deg':mid['earth']['azimuth_deg'],
                         'ideal_horizontal_solar_fraction':max(0.,math.sin(math.radians(solar)))})
        def windows(key):
            result=[]
            for bin in bins:
                valid=bin['sun_up'] if key=='sun' else bin['earth_up'] if key=='earth' else bin['sun_up'] and bin['earth_up']
                if valid:
                    begin=datetime.fromisoformat(bin['start'].replace('Z','+00:00'));finish=z(begin+timedelta(minutes=request.step_minutes))
                    if result and result[-1]['end']==bin['start']:result[-1]['end']=finish
                    else:result.append({'start':bin['start'],'end':finish})
            return result
        sites.append({'name':site.name,'latitude':site.latitude,'longitude':site.longitude,'at_start':now,
                      'sun_hours':sum(x['sun_up'] for x in bins)*request.step_minutes/60,'earth_hours':sum(x['earth_up'] for x in bins)*request.step_minutes/60,
                      'overlap_hours':sum(x['sun_up'] and x['earth_up'] for x in bins)*request.step_minutes/60,
                      'overlap_hours_plus_2deg':sum(x['sun_elevation_deg']>request.sun_clearance_deg+2 and x['earth_elevation_deg']>request.earth_clearance_deg+2 for x in bins)*request.step_minutes/60,
                      'ideal_horizontal_solar_fraction_mean':sum(x['ideal_horizontal_solar_fraction'] for x in bins)/len(bins),
                      'sun_windows':windows('sun'),'earth_windows':windows('earth'),'overlap_windows':windows('both'),'timeline':bins})
    return {'start':z(request.start),'end':z(end),'step_minutes':request.step_minutes,'sun_clearance_deg':request.sun_clearance_deg,'earth_clearance_deg':request.earth_clearance_deg,
            'dataset_sha256':ephemeris.SHA256, 'model_version':'lunaris-geometry-1.1', 'frame':'MOON_ME_DE421',
            'assumptions':{'longitude':'east-positive degrees','radius_km':ephemeris.RADIUS_M/1000,
                           'corrections':'geometric; no light-time or aberration','target':'Sun and Earth centers',
                           'bin_classification':'midpoint; strict elevation > clearance',
                           'solar_fraction':'mean max(0, sin(solar elevation)); geometric horizon only',
                           'sensitivity':'both clearances increased by 2 degrees; not an uncertainty interval'},
            'provenance_url':'https://github.com/julianascencio/orbital-pv/tree/7c2b1a64f7d43b9662b022ac3b88351228bbd3cd/examples/lunar/_data',
            'source':'JPL DE421 SPICE-derived two-hour vectors, interpolated',
            'limits':'Spherical Moon, no terrain or antenna; midpoint bins; fixed elevation thresholds are not terrain. Not flight-qualified.','sites':sites}
