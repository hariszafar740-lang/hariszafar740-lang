#!/usr/bin/env python3
"""Compare bundled grid vectors against NAIF originals, offline after download.

Usage: python scripts/check_naif_vectors.py KERNEL_DIR [MIRROR_DE421]
Requires SpiceyPy 7.0.0 / CSPICE N0067, and four SHA-verified NAIF files in
KERNEL_DIR. Prints JSON with observed errors; this is not a scientific audit.
"""
import csv
from datetime import datetime,timedelta,timezone
import hashlib
import json
import math
from pathlib import Path
import sys

NAIF={
 'de421.bsp':'08b20db2ae22488650641c5a9033e5bfda4b1c4b440cfeaf20f621cfa18ecdb3',
 'moon_pa_de421_1900-2050.bpc':'656f90616403d75a75f0cd6c8830fc5b44f8cb4facb5ccb8915e752b397520cf',
 'moon_080317.tf':'78732477b96f9863e7b0d65bcee3c22b8707ca5ed0db56d1173319cb2e8c7993',
 'naif0012.tls':'678e32bdb5a744117a467cd9601cd6b373f0e9bc9bbde1371d5eee39600a039b',
}
MIRROR='a20a7139da04cbc462454634918e9a9ca69127044e2cc9d4f9c16e238d2deedc'
TABLE=Path(__file__).resolve().parents[1]/'data/ephemeris/de421_2020_2030.csv'
TABLE_SHA='966bed14200d762ee124812b6de891c4c6d169e2a5101be303563750c0b4ce61'

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def main(directory,mirror=None):
    import spiceypy as sp
    if sp.__version__!='7.0.0' or sp.tkvrsn('TOOLKIT')!='CSPICE_N0067':raise ValueError('Requires SpiceyPy 7.0.0 / CSPICE N0067')
    for name,digest in NAIF.items():
        if sha(directory/name)!=digest:raise ValueError(f'NASA file hash mismatch: {name}')
    if sha(TABLE)!=TABLE_SHA:raise ValueError('Bundled table hash mismatch')
    if mirror and sha(mirror)!=MIRROR:raise ValueError('Mirror kernel hash mismatch')
    start=datetime(2020,1,1,tzinfo=timezone.utc);end=datetime(2031,1,1,tzinfo=timezone.utc)
    stats={'count':0,'max_table_vector_difference_m':{'sun':0.,'earth':0.},'max_naif_mirror_vector_difference_m':{'sun':0.,'earth':0.} if mirror else None}
    def load(spk):
        sp.kclear()
        for path in (directory/'naif0012.tls',spk,directory/'moon_pa_de421_1900-2050.bpc',directory/'moon_080317.tf'):sp.furnsh(str(path))
    load(directory/'de421.bsp')
    with TABLE.open(newline='',encoding='ascii') as f:
        reader=csv.DictReader(f)
        for row in reader:
            instant=start+timedelta(hours=2*stats['count'])
            if row['utc']!=instant.strftime('%Y-%m-%dT%H:%M:%SZ') or instant>end:raise ValueError('Unexpected grid date')
            et=sp.str2et(row['utc'])
            for body in ('sun','earth'):
                actual,_=sp.spkpos(body.upper(),et,'MOON_ME_DE421','NONE','MOON')
                reference=[float(row[f'{body}_{key}_m']) for key in 'xyz']
                diff=math.dist([x*1000 for x in actual],reference)
                stats['max_table_vector_difference_m'][body]=max(stats['max_table_vector_difference_m'][body],diff)
            stats['count']+=1
    if stats['count']!=48217:raise ValueError('Unexpected row count')
    # Compare the kernels directly at a separate, evenly spaced set of dates.
    if mirror:
        original_bytes=(directory/'de421.bsp').read_bytes()
        mirror_bytes=mirror.read_bytes()
        common=min(len(original_bytes),len(mirror_bytes))
        offsets=[i for i,(a,b) in enumerate(zip(original_bytes,mirror_bytes)) if a!=b]
        stats['file_comparison']={'naif_bytes':len(original_bytes),'mirror_bytes':len(mirror_bytes),'differing_overlap_bytes':len(offsets),'first_difference_offset':offsets[0] if offsets else None,'last_difference_offset':offsets[-1] if offsets else None,'naif_extra_bytes':len(original_bytes)-common,'naif_daf_format':original_bytes[88:96].decode('ascii',errors='replace'),'mirror_daf_format':mirror_bytes[88:96].decode('ascii',errors='replace')}
        # Locate a long mirror data slice in the original; evidence for layout
        # differences, not proof that all numerical records are equivalent.
        sample=mirror_bytes[4096:4224]
        stats['file_comparison']['mirror_offset_4096_first_found_at_naif_offset']=original_bytes.find(sample)
        stats['file_comparison']['trailing_mirror_matches_shifted_naif']=original_bytes[6144:]==mirror_bytes[4096:]
        # Two kernels may coexist; last loaded takes precedence, so switch per body/time.
        # Restrict the direct kernel-to-kernel check to a reproducible 111 dates to
        # avoid repeatedly unloading the large SPK for every grid point.
        for i in range(111):
            instant=start+(end-start)*(i/110);et=sp.str2et(instant.strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            load(directory/'de421.bsp');original=[sp.spkpos(b,et,'MOON_ME_DE421','NONE','MOON')[0] for b in ('SUN','EARTH')]
            load(mirror);copied=[sp.spkpos(b,et,'MOON_ME_DE421','NONE','MOON')[0] for b in ('SUN','EARTH')]
            for key,a,b in zip(('sun','earth'),original,copied):stats['max_naif_mirror_vector_difference_m'][key]=max(stats['max_naif_mirror_vector_difference_m'][key],math.dist(a,b)*1000)
        stats['naif_mirror_sample_count']=111
    sp.kclear()
    print(json.dumps(stats,sort_keys=True))

if __name__=='__main__':
    if len(sys.argv) not in (2,3):raise SystemExit(__doc__)
    main(Path(sys.argv[1]),Path(sys.argv[2]) if len(sys.argv)==3 else None)
