"""Read the small, provenance-pinned Diviner PCP subset and its PDS4 label.

This is a historical, spatially sparse subset, not a live temperature map.
"""
import csv
from functools import lru_cache
import hashlib
import math
from pathlib import Path
import xml.etree.ElementTree as ET

DATA = Path(__file__).resolve().parent.parent / 'data' / 'diviner'
NS = {'p': 'http://pds.nasa.gov/pds4/pds/v1'}
PRODUCT = 'urn:nasa:pds:lro_diviner_derived1:data_derived_pcp:pcp_avg_tbol_pols_ls030_slon01_240'
TAB_HASH = '3549df564f412a0d573383d7fe17e809f383cf8455a2a13de9a83e05aa431537'
LABEL_HASH = 'c434aa4916cf70917a09ecbed4c6bd44537ff343687c6c9c056ede843a4064e8'
SOURCE_URL = 'https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_pcp/seasonal/slon/pols/pcp_avg_tbol_pols_ls030_slon01_240.xml'
MIRROR_URL = 'https://github.com/julianascencio/orbital-pv/tree/7c2b1a64f7d43b9662b022ac3b88351228bbd3cd/examples/lunar/_data'

def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_subset(data=DATA):
    label = data / 'diviner_label.xml'
    table = data / 'diviner_subset.tab'
    if _digest(label) != LABEL_HASH or _digest(table) != TAB_HASH:
        raise ValueError('Diviner input checksum mismatch')
    root = ET.parse(label).getroot()
    def text(path):
        node = root.find(path, NS)
        if node is None or node.text is None: raise ValueError(f'Missing label field {path}')
        return node.text.strip()
    if text('.//p:logical_identifier') != PRODUCT:
        raise ValueError('Unexpected PDS product identifier')
    if text('.//p:File/p:file_name') != 'pcp_avg_tbol_pols_ls030_slon01_240.tab':
        raise ValueError('Unexpected PDS table name')
    fields = root.findall('.//p:Field_Character', NS)
    names = [field.findtext('p:name', namespaces=NS) for field in fields]
    if names != ['x', 'y', 'clon', 'clat', 'ltim', 'tbol'] or fields[-1].findtext('p:unit', namespaces=NS) != 'K':
        raise ValueError('Unexpected PDS schema or temperature unit')
    rows = []
    with table.open(newline='', encoding='ascii') as f:
        reader = csv.DictReader(f, skipinitialspace=True)
        if [name.strip() for name in reader.fieldnames or []] != names:
            raise ValueError('Subset columns do not match label')
        for record in reader:
            record = {k.strip(): float(v.strip()) for k, v in record.items()}
            if not all(math.isfinite(v) for v in record.values()): raise ValueError('Nonfinite Diviner value')
            if not (-90 <= record['clat'] <= -80 and -180 <= record['clon'] <= 180 and 0 <= record['ltim'] < 24 and 0 < record['tbol'] < 500):
                raise ValueError('Invalid Diviner coordinates, local time or temperature')
            rows.append(record)
    if len(rows) != 551: raise ValueError('Unexpected subset size')
    return rows

@lru_cache(maxsize=1)
def observations():
    return load_subset()

def distance_km(lat1,lon1,lat2,lon2):
    a1,a2=math.radians(lat1),math.radians(lat2)
    delta_lat=a2-a1
    delta_lon=math.radians(lon2-lon1)
    a=math.sin(delta_lat/2)**2+math.cos(a1)*math.cos(a2)*math.sin(delta_lon/2)**2
    return 2*1737.4*math.asin(math.sqrt(min(1.,max(0.,a))))

def nearest(lat, lon, max_distance_km=2):
    best=min(observations(),key=lambda row:distance_km(lat,lon,row['clat'],row['clon']))
    distance=distance_km(lat,lon,best['clat'],best['clon'])
    result={'status':'available' if distance <= max_distance_km else 'outside_coverage',
            'nearest_distance_km':round(distance,3), 'max_distance_km':max_distance_km,
            'product':PRODUCT, 'source_url':SOURCE_URL, 'mirror_url':MIRROR_URL,
            'note':'Historical binned brightness temperature; not a live reading or a matched-time model validation.'}
    if distance <= max_distance_km:
        result['observation']={'latitude':best['clat'],'longitude':best['clon'],'temperature_k':best['tbol'],'local_time_h':best['ltim']}
    return result
