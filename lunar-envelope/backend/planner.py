"""Site/date comparison. Geometric screening, not a safety/mission assessment."""
from datetime import datetime, timedelta, timezone
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
        for hour in range(request.days*24):
            time=request.start+timedelta(hours=hour)
            mid=ephemeris.at_site(time+timedelta(minutes=30),site.latitude,site.longitude)
            solar=mid['sun']['elevation_deg']; earth=mid['earth']['elevation_deg']
            bins.append({'start':z(time),'sun_up':solar>0,'earth_up':earth>0,
                         'sun_elevation_deg':solar,'earth_elevation_deg':earth,
                         'ideal_horizontal_solar_fraction':max(0.,math.sin(math.radians(solar)))})
        def windows(key):
            result=[]
            for bin in bins:
                valid=bin['sun_up'] if key=='sun' else bin['earth_up'] if key=='earth' else bin['sun_up'] and bin['earth_up']
                if valid:
                    begin=datetime.fromisoformat(bin['start'].replace('Z','+00:00'));finish=z(begin+timedelta(hours=1))
                    if result and result[-1]['end']==bin['start']:result[-1]['end']=finish
                    else:result.append({'start':bin['start'],'end':finish})
            return result
        sites.append({'name':site.name,'latitude':site.latitude,'longitude':site.longitude,'at_start':now,
                      'sun_hours':sum(x['sun_up'] for x in bins),'earth_hours':sum(x['earth_up'] for x in bins),
                      'overlap_hours':sum(x['sun_up'] and x['earth_up'] for x in bins),
                      'ideal_horizontal_solar_fraction_mean':sum(x['ideal_horizontal_solar_fraction'] for x in bins)/len(bins),
                      'sun_windows':windows('sun'),'earth_windows':windows('earth'),'overlap_windows':windows('both'),'timeline':bins})
    return {'start':z(request.start),'end':z(end),'step_minutes':60,'frame':'MOON_ME_DE421',
            'source':'JPL DE421 SPICE-derived two-hour vectors, interpolated',
            'limits':'Spherical Moon, no terrain or antenna; one-hour midpoint bins. Not flight-qualified.','sites':sites}
