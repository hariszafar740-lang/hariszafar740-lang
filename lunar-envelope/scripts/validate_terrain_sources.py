#!/usr/bin/env python3
"""Independently compare the bundled DEM to original LOLA PDS raster samples.

Usage: python scripts/validate_terrain_sources.py DIR
DIR must contain LDEM_80S_80M and LDEM_75S_120M .img files (lowercase names).
Requires NumPy; reads the complete source rasters without writing derived data.
Hashes are upstream's published source hashes, independently checked against
files downloaded from PDS. This is a data-processing comparison, not a review
of the scientific suitability or accuracy of LOLA measurements.
"""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from backend import terrain

SOURCES={'ldem_80s_80m.img':('e6591eeea35402ca5e124ca00f5bf0774381a2d4fa919144b455d82b8ff65fdc',7600),
         'ldem_75s_120m.img':('ae3afc3c75c33d43666ca06c83ca08f0b12ef03b7d36d2d791d972730794391b',7624)}

def verify(path,sha,size):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    if path.stat().st_size!=size*size*2 or h.hexdigest()!=sha:raise ValueError(f'Source size/hash mismatch: {path}')
    return np.memmap(path,mode='r',dtype='<i2',shape=(size,size))

def main(directory):
    rasters={name:verify(directory/name,*spec) for name,spec in SOURCES.items()}
    actual=np.asarray(terrain.load_grid()).reshape(2280,2280)
    # Plain 25-pixel integer sums, independently calculated from native DN.
    inner=rasters['ldem_80s_80m.img']
    total=inner.reshape(1520,5,1520,5).sum(axis=(1,3),dtype=np.int64)
    expected=np.rint(total/50).astype(np.int16)
    diff=actual[380:1900,380:1900].astype(np.int32)-expected.astype(np.int32)
    report={'source_sha256':{k:v[0] for k,v in SOURCES.items()},'inner':{'cells':diff.size,'nonzero':int(np.count_nonzero(diff)),'max_abs_m':int(np.abs(diff).max())}}
    # Exact integer overlap areas. For one 1200 m period, destination
    # intervals overlap input samples by (3,3,3,1), (2,3,3,2), (1,3,3,3)
    # 40 m units; denominator is 10*10, and DN->metres adds 2.
    weights=np.array([[3,3,3,1,0,0,0,0,0,0],[0,0,0,2,3,3,2,0,0,0],[0,0,0,0,0,0,1,3,3,3]],dtype=np.int64)
    src=rasters['ldem_75s_120m.img']; nonzero=0;total_cells=0;maximum=0;examples=[];fills=0;ties=0;nonties=0
    for p in range(0,760,20):
        q=min(p+20,760); block=np.asarray(src[12+p*10:12+q*10,12:7612],dtype=np.int64)
        fills+=int(np.count_nonzero((block==-32768)|(block==32767)))
        block=block.reshape(q-p,10,760,10)
        values=np.einsum('pi,aibj,qj->apbq',weights,block,weights,optimize=True).reshape((q-p)*3,2280)
        ref=np.rint(values/200).astype(np.int16)
        row0=p*3;delta=actual[row0:q*3].astype(np.int32)-ref.astype(np.int32)
        # Inner region uses a different source; skip it rather than report it as an error.
        for r in range(max(380-row0,0),min(1900-row0,len(delta))):delta[r,380:1900]=0
        nz=np.argwhere(delta!=0)
        for r,c in nz[:max(0,10-len(examples))]:examples.append([int(row0+r),int(c),int(delta[r,c]),int(values[r,c])])
        ties+=int(np.count_nonzero((delta!=0)&(values%200==100)))
        nonties+=int(np.count_nonzero((delta!=0)&(values%200!=100)))
        nonzero+=len(nz); maximum=max(maximum,int(np.abs(delta).max()));total_cells+=delta.size
    report['ring']={'cells':total_cells-1520*1520,'nonzero':nonzero,'max_abs_m':maximum,'examples_row_col_delta_m_numerator':examples,'exact_half_m_differences':ties,'other_differences':nonties,'fill_values_in_source_window':fills}
    print(json.dumps(report,sort_keys=True))
if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit(__doc__)
    main(Path(sys.argv[1]))
