#!/usr/bin/env python3
"""Compare optional native-mode rays with independently computed PDS cases.

Usage: LUNARIS_NATIVE_DEM_DIR=/path python scripts/check_native_horizon_regression.py
Requires the two source rasters; compares 33 selected directions and prints a
JSON report. Half-degree directions are interpolated in the application. This
is a regression cross-check, not an independent scientific review or bound.
"""
import csv,json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend import terrain

def main():
    path=Path(__file__).resolve().parents[1]/'tests/pds_native_horizon_comparison.csv'
    rows=list(csv.DictReader(path.open(newline='',encoding='ascii')))
    results=[];started=time.monotonic()
    for row in rows:
        ground,profile,coverage,_=terrain.native_horizon(float(row['latitude']),float(row['longitude']),float(row['height_above_ground_m']))
        diff=terrain.horizon_at(profile,float(row['azimuth_deg']))-float(row['native_horizon_deg'])
        results.append({'latitude':float(row['latitude']),'longitude':float(row['longitude']),'azimuth':float(row['azimuth_deg']),'ground_difference_m':ground-float(row['native_ground_m']),'horizon_difference_deg':diff})
    print(json.dumps({'cases':results,'max_ground_difference_m':max(abs(r['ground_difference_m']) for r in results),'max_horizon_difference_deg':max(abs(r['horizon_difference_deg']) for r in results),'seconds':time.monotonic()-started},sort_keys=True))
if __name__=='__main__':main()
