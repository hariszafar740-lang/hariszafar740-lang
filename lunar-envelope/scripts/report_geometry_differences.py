#!/usr/bin/env python3
"""Report app minus archived independent Horizons-derived reference values.

Run from the project root: python scripts/report_geometry_differences.py
Values are selected-case comparisons, not global error bounds.
"""
import csv
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend import ephemeris

REFERENCE=Path(__file__).resolve().parents[1]/'tests/horizons_broad_reference.csv'

def main():
    ds=ephemeris.select(ephemeris.EXTENDED_START,ephemeris.EXTENDED_END)
    w=csv.writer(sys.stdout,lineterminator='\n');w.writerow(['utc','latitude','longitude','height_m','body','reference_elevation_deg','delta_elevation_deg','delta_azimuth_deg','delta_distance_km'])
    with REFERENCE.open(newline='',encoding='ascii') as f:
        for r in csv.DictReader(f):
            at=datetime.fromisoformat(r['utc'].replace('Z','+00:00'))
            got=ds.at(at,float(r['latitude']),float(r['longitude']),float(r['height_m']))[r['body'].lower()]
            w.writerow([*[r[k] for k in ('utc','latitude','longitude','height_m','body','elevation_deg')],f"{got['elevation_deg']-float(r['elevation_deg']):.12f}",f"{(got['azimuth_deg']-float(r['azimuth_deg'])+180)%360-180:.12f}",f"{got['distance_km']-float(r['distance_km']):.9f}"])
if __name__=='__main__':main()
