#!/usr/bin/env python3
"""Fetch independent Horizons vectors bracketing the existing CSPICE crossings.

Usage: python scripts/fetch_horizons_crossings.py OUTPUT.csv
Output includes Horizons site-to-center and site-to-target ICRF vectors, two
samples per selected crossing, and both request URLs. Reference uses a linear
interpolation of the signed local up component; it is not an exact root or a
search for missed/grazing events. Requires network; never used during tests.
"""
import csv
from datetime import datetime,timedelta
from pathlib import Path
import sys
from urllib.parse import urlencode
from urllib.request import urlopen

SOURCE=Path(__file__).resolve().parents[1]/'tests/cspice_crossings.csv'
URL='https://ssd.jpl.nasa.gov/api/horizons.api?'

def fetch(command,site,dates):
    jd=[f'{t.timestamp()/86400+2440587.5:.9f}' for t in dates]
    params={'format':'text','COMMAND':f"'{command}'",'OBJ_DATA':"'NO'",'MAKE_EPHEM':"'YES'",'EPHEM_TYPE':"'VECTORS'",'CENTER':"'coord@301'",'SITE_COORD':f"'{site}'",'TLIST':"'"+','.join(jd)+"'",'TLIST_TYPE':"'JD'",'REF_PLANE':"'FRAME'",'REF_SYSTEM':"'ICRF'",'OUT_UNITS':"'KM-S'",'VEC_CORR':"'NONE'",'TIME_TYPE':"'UT'",'CSV_FORMAT':"'YES'"}
    url=URL+urlencode(params)
    with urlopen(url,timeout=60) as f:text=f.read().decode('utf-8')
    for marker in ('{source: DE441}','GEOMETRIC cartesian states','Reference frame : ICRF','MEAN_ME (high precision)','$$SOE','$$EOE'):
        if marker not in text:raise ValueError('Missing '+marker)
    rows=list(csv.reader(text.split('$$SOE',1)[1].split('$$EOE',1)[0].strip().splitlines()))
    if len(rows)!=2 or any(abs(float(r[0])-float(j))>1e-8 for r,j in zip(rows,jd)):raise ValueError('Unexpected data')
    return [[v.strip() for v in r[2:5]] for r in rows],url

def main(output):
    with SOURCE.open(newline='',encoding='ascii') as source,output.open('x',newline='',encoding='ascii') as result:
        w=csv.writer(result,lineterminator='\n')
        w.writerow(['start','days','latitude','longitude','body','kind','cspice_utc','sample_utc','center_x','center_y','center_z','target_x','target_y','target_z','center_url','target_url'])
        for row in csv.DictReader(source):
            at=datetime.fromisoformat(row['utc'].replace('Z','+00:00'))
            dates=[at-timedelta(seconds=120),at+timedelta(seconds=120)]
            site=','.join((row['longitude'],row['latitude'],'0'))
            axes,center_url=fetch('301',site,dates)
            targets,target_url=fetch({'SUN':'10','EARTH':'399'}[row['body']],site,dates)
            for date,a,t in zip(dates,axes,targets):
                w.writerow([row[k] for k in ('start','days','latitude','longitude','body','kind','utc')]+[date.isoformat().replace('+00:00','Z'),*a,*t,center_url,target_url])

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit(__doc__)
    main(Path(sys.argv[1]))
