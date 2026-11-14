#!/usr/bin/env python3
"""Fetch a documented DE441 geometric-vector validation set (network required).

Usage: python scripts/fetch_horizons_validation.py OUTPUT_DIRECTORY
Writes raw NASA/JPL Horizons responses and source-vector CSVs; refuses overwrite.
The separately generated local-coordinate fixture uses no app code or CSPICE.
Horizons can change, so network results are not required by offline tests.
"""
import csv
from datetime import datetime,timezone
from pathlib import Path
import sys
from urllib.parse import urlencode
from urllib.request import urlopen

TIMES=['2020-01-01T00:30:00Z','2021-02-28T11:45:00Z','2022-09-17T17:07:30Z','2023-12-31T23:15:00Z','2024-07-04T08:20:00Z','2025-01-03T21:30:00Z','2027-05-13T16:45:00Z','2028-11-06T03:15:00Z','2029-06-29T12:20:00Z','2030-12-31T12:30:00Z']
URL='https://ssd.jpl.nasa.gov/api/horizons.api?'

def main(out):
    out.mkdir(parents=True,exist_ok=False)
    jd=[f'{datetime.fromisoformat(t.replace("Z","+00:00")).timestamp()/86400+2440587.5:.9f}' for t in TIMES]
    params={'format':'text','OBJ_DATA':"'NO'",'MAKE_EPHEM':"'YES'",'EPHEM_TYPE':"'VECTORS'",'TLIST':"'"+','.join(jd)+"'",'TLIST_TYPE':"'JD'",'REF_PLANE':"'FRAME'",'REF_SYSTEM':"'ICRF'",'OUT_UNITS':"'KM-S'",'VEC_CORR':"'NONE'",'TIME_TYPE':"'UT'",'CSV_FORMAT':"'YES'"}
    data={}
    for key,command,center,site in [('SUN','10','500@301',None),('EARTH','399','500@301',None),('X','301','coord@301','0,0,0'),('Y','301','coord@301','90,0,0'),('Z','301','coord@301','0,90,0')]:
        query=dict(params,COMMAND=f"'{command}'",CENTER=f"'{center}'")
        if site:query['SITE_COORD']=f"'{site}'"
        url=URL+urlencode(query)
        with urlopen(url,timeout=60) as response: text=response.read().decode('utf-8')
        for marker in ('{source: DE441}','GEOMETRIC cartesian states','Reference frame : ICRF','$$SOE','$$EOE'):
            if marker not in text:raise ValueError(f'{key}: missing {marker}')
        if site and 'MEAN_ME (high precision)' not in text:raise ValueError('Unexpected lunar orientation')
        (out/f'{key}.txt').write_text(text,encoding='utf-8')
        (out/f'{key}.url').write_text(url+'\n',encoding='utf-8')
        rows=list(csv.reader(text.split('$$SOE',1)[1].split('$$EOE',1)[0].strip().splitlines()))
        if len(rows)!=len(TIMES):raise ValueError('Unexpected row count')
        if any(abs(float(r[0])-float(j))>1e-8 for r,j in zip(rows,jd)):raise ValueError('Unexpected timestamps')
        data[key]=[[v.strip() for v in row[2:5]] for row in rows]
    for name,keys,header in [('axes.csv','XYZ','axis'),('targets.csv',['SUN','EARTH'],'body')]:
        with (out/name).open('x',newline='',encoding='ascii') as f:
            w=csv.writer(f,lineterminator='\n');w.writerow(['utc',header,'x_km','y_km','z_km'])
            for i,t in enumerate(TIMES):
                for k in keys:w.writerow([t,k,*data[k][i]])

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit(__doc__)
    main(Path(sys.argv[1]))
