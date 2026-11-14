"""Extract a bounded area from the pinned PDS4 Diviner product or its mirror subset.

Example: python -m backend.diviner_ingest --table data/diviner/diviner_subset.tab
         --mode subset --output data/extract.csv --south -90 --north -88
Original full table SHA-256 is recorded in the mirror provenance, not verified
against NASA in this environment. Outputs are explicitly labeled with the mode.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from . import diviner

FULL_HASH = '571d11da49ceced5f3622e4d5f9e3a4cbaf88962d82688005af2cf0d9f0ace88'
FULL_COUNT = 3176166
FIELDS = ('x', 'y', 'clon', 'clat', 'ltim', 'tbol')

def digest(path: Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def extract(table: Path, output: Path, mode: str, south: float, north: float, west: float, east: float, max_rows: int = 10000):
    if mode not in ('full', 'subset') or not (-90<=south<=north<=90 and -180<=west<=east<=180) or not (1<=max_rows<=100000):
        raise ValueError('Invalid mode, bounds or row limit')
    if output.exists() or output.with_suffix(output.suffix+'.json').exists():
        raise FileExistsError('Output already exists; choose a new path')
    expected = FULL_HASH if mode=='full' else diviner.TAB_HASH
    if digest(table) != expected: raise ValueError('Table checksum does not match the pinned source')
    # Verify pinned PDS label and schema using bundled sample; no arbitrary labels accepted.
    diviner.load_subset()
    selected=[]; count=0; rejected=0
    with table.open(newline='', encoding='ascii') as f:
        reader=csv.DictReader(f,skipinitialspace=True)
        if tuple(x.strip() for x in reader.fieldnames or []) != FIELDS: raise ValueError('Unexpected product schema')
        for raw in reader:
            row={key.strip():float(value.strip()) for key,value in raw.items()}
            if not all(math.isfinite(value) for value in row.values()): raise ValueError('Nonfinite product value')
            count+=1
            # PDS label documents missing constants and boundary bin centres up
            # to -79.995525 degrees. Reject invalid rows but preserve counts.
            if not (-90<=row['clat']<=-79.99 and -180<=row['clon']<=180 and 0<=row['ltim']<24 and 0<row['tbol']<500):
                rejected+=1
                continue
            if south<=row['clat']<=north and west<=row['clon']<=east:
                if len(selected)>=max_rows: raise ValueError('Row limit exceeded; narrow bounds or increase --max-rows')
                selected.append(row)
    if count != (FULL_COUNT if mode=='full' else 551): raise ValueError('Input row count mismatch')
    output.parent.mkdir(parents=True,exist_ok=True)
    created = False
    try:
        with output.open('x',newline='',encoding='ascii') as f:
            created = True
            writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(selected)
        manifest={'product':diviner.PRODUCT,'label_sha256':diviner.LABEL_HASH,'input_sha256':expected,
                  'input_mode':mode,'input_rows':count,'rejected_rows':rejected,'selected_rows':len(selected),'bounds':{'south':south,'north':north,'west':west,'east':east},
                  'temperature_unit':'K','source_label':diviner.SOURCE_URL,'mirror':diviner.MIRROR_URL,
                  'warning':'Historical binned data; not live telemetry or independent model validation.'}
        output.with_suffix(output.suffix+'.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    except Exception:
        if created: output.unlink(missing_ok=True)
        raise
    return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--table',type=Path,required=True)
    parser.add_argument('--mode',choices=('full','subset'),required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--south',type=float,default=-90);parser.add_argument('--north',type=float,default=-80)
    parser.add_argument('--west',type=float,default=-180);parser.add_argument('--east',type=float,default=180)
    parser.add_argument('--max-rows',type=int,default=10000)
    args=parser.parse_args()
    print(json.dumps(extract(args.table,args.output,args.mode,args.south,args.north,args.west,args.east,args.max_rows),indent=2))
