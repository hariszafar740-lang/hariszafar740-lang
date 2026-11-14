"""Import explicitly normalized observations. This is not a PDS label parser."""
import argparse
import csv
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

FIELDS = ('timestamp', 'quantity', 'value', 'unit', 'source_url')
ALLOWED_HOSTS = ('nasa.gov', 'nmsu.edu', 'wustl.edu')

def ingest(source: Path, target: Path):
    rows = []
    with source.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or not set(FIELDS).issubset(reader.fieldnames):
            raise ValueError(f'CSV requires columns: {", ".join(FIELDS)}')
        for row in reader:
            datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
            val = float(row['value'])
            import math
            if not math.isfinite(val) or not row['quantity'].strip() or not row['unit'].strip():
                raise ValueError('Values must be finite and quantities and units nonempty')
            url = urlparse(row['source_url'])
            host = (url.hostname or '').lower()
            if url.scheme != 'https' or not any(host == h or host.endswith('.'+h) for h in ALLOWED_HOSTS):
                raise ValueError('Each row requires an HTTPS NASA/PDS source URL')
            rows.append({k: row[k] for k in FIELDS})
    if not rows: raise ValueError('No observations found')
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS); writer.writeheader();writer.writerows(rows)
    return len(rows)

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path,help='Previously normalized CSV with provenance')
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parent.parent/'data'/'observations.csv')
    args=parser.parse_args(); print(f'Imported {ingest(args.source,args.output)} rows to {args.output}. Review provenance independently.')
