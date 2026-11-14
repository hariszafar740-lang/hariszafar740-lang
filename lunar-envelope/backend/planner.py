"""Site/date comparison. Geometric screening, not a safety/mission assessment."""
from datetime import datetime, timedelta, timezone
from typing import Literal
import math
from functools import lru_cache
from pydantic import BaseModel, Field, ConfigDict, field_validator
from . import ephemeris, events

class Site(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    name: str=Field(min_length=1,max_length=40)
    latitude:float=Field(ge=-90,le=90)
    longitude:float=Field(ge=-180,le=180)
    height_m:float=Field(default=0,ge=0,le=1000)

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
        value=v.astimezone(timezone.utc)
        if not ephemeris.EXTENDED_START <= value < ephemeris.EXTENDED_END:
            raise ValueError('Start must lie between 2020-01-01 and 2031-01-01 UTC')
        return value


def compare(request:PlanRequest):
    end=request.start+timedelta(days=request.days)
    dataset=ephemeris.select(request.start,end)
    def z(dt): return dt.isoformat().replace('+00:00','Z')
    sites=[]
    for site in request.sites:
        @lru_cache(maxsize=10000)
        def geometry(time):return dataset.at(time,site.latitude,site.longitude,site.height_m)
        now=geometry(request.start)
        bins=[]
        for step in range(request.days*24*60//request.step_minutes):
            time=request.start+timedelta(minutes=step*request.step_minutes)
            mid=geometry(time+timedelta(minutes=request.step_minutes/2))
            solar=mid['sun']['elevation_deg']; earth=mid['earth']['elevation_deg']
            bins.append({'start':z(time),'sun_up':solar>request.sun_clearance_deg,'earth_up':earth>request.earth_clearance_deg,
                         'sun_elevation_deg':solar,'earth_elevation_deg':earth,
                         'sun_azimuth_deg':mid['sun']['azimuth_deg'],'earth_azimuth_deg':mid['earth']['azimuth_deg'],
                         'sun_distance_km':mid['sun']['distance_km'],'earth_distance_km':mid['earth']['distance_km'],
                         'sun_azimuth_defined':mid['sun']['azimuth_defined'],'earth_azimuth_defined':mid['earth']['azimuth_defined'],
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
        sun_intervals,sun_events=events.threshold_windows(request.start,end,timedelta(minutes=15),lambda t:geometry(t)['sun']['elevation_deg'],request.sun_clearance_deg)
        earth_intervals,earth_events=events.threshold_windows(request.start,end,timedelta(minutes=15),lambda t:geometry(t)['earth']['elevation_deg'],request.earth_clearance_deg)
        both_intervals=events.intersect(sun_intervals,earth_intervals)
        def serialize(intervals): return [{'start':z(a),'end':z(b)} for a,b in intervals]
        def hours(intervals):return round(sum((b-a).total_seconds() for a,b in intervals)/3600,4)
        def serialize_events(items):return [{'time':z(item['time']),'kind':item['kind']} for item in items]
        refined={'sun_windows':serialize(sun_intervals),'earth_windows':serialize(earth_intervals),'overlap_windows':serialize(both_intervals),
                 'sun_hours':hours(sun_intervals),'earth_hours':hours(earth_intervals),'overlap_hours':hours(both_intervals),
                 'sun_transitions':serialize_events(sun_events),'earth_transitions':serialize_events(earth_events)}
        sites.append({'name':site.name,'latitude':site.latitude,'longitude':site.longitude,'height_m':site.height_m,'at_start':now,'refined':refined,
                      'sun_hours':sum(x['sun_up'] for x in bins)*request.step_minutes/60,'earth_hours':sum(x['earth_up'] for x in bins)*request.step_minutes/60,
                      'overlap_hours':sum(x['sun_up'] and x['earth_up'] for x in bins)*request.step_minutes/60,
                      'overlap_hours_plus_2deg':sum(x['sun_elevation_deg']>request.sun_clearance_deg+2 and x['earth_elevation_deg']>request.earth_clearance_deg+2 for x in bins)*request.step_minutes/60,
                      'ideal_horizontal_solar_fraction_mean':sum(x['ideal_horizontal_solar_fraction'] for x in bins)/len(bins),
                      'sun_windows':windows('sun'),'earth_windows':windows('earth'),'overlap_windows':windows('both'),'timeline':bins})
    return {'start':z(request.start),'end':z(end),'step_minutes':request.step_minutes,'sun_clearance_deg':request.sun_clearance_deg,'earth_clearance_deg':request.earth_clearance_deg,
            'dataset_sha256':dataset.digest, 'dataset_kind':dataset.kind, 'model_version':'lunaris-geometry-1.2', 'frame':'MOON_ME_DE421',
            'assumptions':{'longitude':'east-positive degrees','radius_km':ephemeris.RADIUS_M/1000, 'observer_height':'meters above reference sphere; zero elevation is local tangent plane, not depressed visible horizon',
                           'corrections':'geometric; no light-time or aberration','target':'Sun and Earth centers',
                           'bin_classification':'midpoint; strict elevation > clearance',
                           'transition_method':'15-minute endpoint sign scan; bisection to 1-second bracket on interpolated vectors; short or grazing events may be missed',
                           'time_scale':'UTC input; ephemeris interpolation between UTC grid instants; future leap seconds not predicted',
                           'interpolation':'normalized linear direction plus linear range at two-hour vector spacing; approximate range and direction',
                           'azimuth':'clockwise from north; undefined at zenith/nadir; at poles the chosen longitude defines local axes',
                           'solar_fraction':'mean max(0, sin(solar elevation)); geometric horizon only',
                           'sensitivity':'both clearances increased by 2 degrees; not an uncertainty interval'},
            'provenance_url':dataset.source,
            'source':f'JPL DE421 SPICE-derived two-hour vectors; direction and range interpolated ({dataset.kind})',
            'limits':'Spherical Moon, no terrain or antenna; midpoint bins and 15-minute transition scans can miss short or grazing events. Thresholds refer to local tangent plane, not terrain. Future leap seconds unknown. Not flight-qualified.','sites':sites}
