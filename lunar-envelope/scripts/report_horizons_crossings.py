#!/usr/bin/env python3
"""Compare app events to linearly interpolated archived Horizons brackets.

Prints a CSV report. The Horizons reference is the zero of linearly
interpolated signed local-up distance between two samples 240 s apart; this
is not an exact root or a search for missed events. No CSPICE code is used.
"""
import csv,math,sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.planner import compare,PlanRequest

PATH=Path(__file__).resolve().parents[1]/'tests/horizons_crossing_brackets.csv'
def dt(s):return datetime.fromisoformat(s.replace('Z','+00:00'))
def main():
    with PATH.open(newline='',encoding='ascii') as f:rows=list(csv.DictReader(f))
    if len(rows)!=16:raise ValueError('Expected 16 samples')
    w=csv.writer(sys.stdout,lineterminator='\n');w.writerow(['start','latitude','longitude','body','kind','sample_before_utc','sample_after_utc','before_elevation_deg','after_elevation_deg','horizons_linear_utc','app_utc','app_minus_horizons_s'])
    for a,b in zip(rows[::2],rows[1::2]):
        for k in ('start','days','latitude','longitude','body','kind','cspice_utc'):
            if a[k]!=b[k]:raise ValueError('Sample identity mismatch')
        up=[];el=[]
        for row in (a,b):
            center=[float(row['center_'+k]) for k in 'xyz'];target=[float(row['target_'+k]) for k in 'xyz']
            dot=-sum(x*y for x,y in zip(center,target))/math.sqrt(sum(x*x for x in center))
            up.append(dot);el.append(math.degrees(math.asin(max(-1.,min(1.,dot/math.sqrt(sum(x*x for x in target)))))))
        if not up[0]*up[1]<0 or ((up[1]>up[0]) != (a['kind']=='rise')):raise ValueError('Samples do not bracket crossing')
        t0=dt(a['sample_utc']);t1=dt(b['sample_utc']);ref=t0+(t1-t0)*(-up[0]/(up[1]-up[0]))
        req=PlanRequest(start=a['start'],days=int(a['days']),sites=[{'name':'reference','latitude':float(a['latitude']),'longitude':float(a['longitude'])}])
        transitions=compare(req)['sites'][0]['refined'][a['body'].lower()+'_transitions']
        candidates=[dt(x['time']) for x in transitions if x['kind']==a['kind']]
        if not candidates:raise ValueError('Missing app transition')
        app=min(candidates,key=lambda t:abs((t-ref).total_seconds()))
        w.writerow([*[a[k] for k in ('start','latitude','longitude','body','kind')],a['sample_utc'],b['sample_utc'],f'{el[0]:.12f}',f'{el[1]:.12f}',ref.isoformat().replace('+00:00','Z'),app.isoformat().replace('+00:00','Z'),f'{(app-ref).total_seconds():.6f}'])
if __name__=='__main__':main()
