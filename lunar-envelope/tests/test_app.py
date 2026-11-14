import csv
import io
import math
from pathlib import Path
import sys
import pytest
from fastapi.testclient import TestClient
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.main import app, calculate, Scenario
from backend.ingest import ingest

client=TestClient(app)

def test_api_and_validation():
    assert client.get('/api/health').json()=={'status':'ok'}
    assert client.post('/api/simulate',json={'latitude':91}).status_code==422
    assert client.post('/api/simulate',json={'wind':199}).status_code==422
    assert client.post('/api/simulate',json={'unexpected':1}).status_code==422
    assert client.post('/api/simulate',json={}).status_code==200

def test_day_and_night_and_cycle():
    day=calculate(Scenario(latitude=0,longitude=0,phase=0))
    night=calculate(Scenario(latitude=0,longitude=180,phase=0))
    cycle=calculate(Scenario(latitude=0,longitude=0,phase=29.53))
    assert day['illuminated'] and not night['illuminated']
    assert day['temperature'] > night['temperature'] and day['potential'] > night['potential']
    assert day['zenith']==cycle['zenith']

def test_scenarios_and_physical_bounds():
    normal=calculate(Scenario())
    extreme=calculate(Scenario(wind=850,meteor=4))
    assert extreme['dust_density']>normal['dust_density']
    assert extreme['efficiency']<normal['efficiency']
    assert len(normal['curve'])==31
    assert all(0 < x['efficiency'] <= 100 for x in extreme['curve'])
    assert all(a['efficiency']>=b['efficiency'] for a,b in zip(extreme['curve'],extreme['curve'][1:]))
    assert all(math.isfinite(g['density_100km']) and g['scale_height_km'] > 0 for g in normal['gases'])

def test_csv_matches_selected_scenario():
    params={'wind':850,'meteor':4,'latitude':0,'longitude':42}
    result=client.post('/api/simulate',json=params).json()
    response=client.post('/api/export-report',json=params)
    assert response.status_code==200 and 'attachment' in response.headers['content-disposition']
    rows=list(csv.reader(io.StringIO(response.content.decode('utf-8-sig'))))
    assert ['Longitude','42.0','degrees'] in rows
    assert ['30-day power retained',str(result['efficiency']),'%'] in rows
    assert ['30',str(result['efficiency'])] in rows

def test_no_observations_are_fabricated():
    data=client.get('/api/nasa-data').json()
    if data['status']=='unavailable': assert data['observations']==[]

def test_ingest_requires_provenance_and_valid_values(tmp_path):
    source=tmp_path/'input.csv'; out=tmp_path/'output.csv'
    source.write_text('timestamp,quantity,value,unit,source_url\n2014-01-01T00:00:00Z,temperature,100,K,https://pds.nasa.gov/file\n')
    assert ingest(source,out)==1
    assert list(csv.DictReader(out.open()))[0]['value']=='100'
    source.write_text(source.read_text().replace('pds.nasa.gov','nasa.gov.evil.com'))
    with pytest.raises(ValueError): ingest(source,out)
    source.write_text('timestamp,quantity,value,unit,source_url\n2014-01-01,temperature,nan,K,https://pds.nasa.gov/file\n')
    with pytest.raises(ValueError): ingest(source,out)

def test_diviner_label_subset_and_nearest_site():
    from backend import diviner
    rows=diviner.load_subset()
    assert len(rows)==551
    assert rows[0]['tbol']==pytest.approx(80.189095)
    result=client.get('/api/diviner',params={'latitude':-88.6,'longitude':-69.3}).json()
    assert result['status']=='available'
    assert result['observation']['temperature_k']==pytest.approx(80.360466)
    assert result['nearest_distance_km'] < 2
    assert result['observation']['local_time_h']==pytest.approx(6.9009)
    assert client.get('/api/nasa-data').json()['count']==551
    far=client.get('/api/diviner',params={'latitude':0,'longitude':0}).json()
    assert far['status']=='outside_coverage' and 'observation' not in far
    assert client.get('/api/diviner',params={'latitude':-91,'longitude':0}).status_code==422

def test_diviner_corruption_rejected(tmp_path):
    from backend import diviner
    import shutil
    for name in ['diviner_label.xml','diviner_subset.tab']:
        shutil.copy(diviner.DATA/name,tmp_path/name)
    (tmp_path/'diviner_subset.tab').write_text('altered')
    with pytest.raises(ValueError,match='checksum'): diviner.load_subset(tmp_path)

def test_report_records_historical_context():
    response=client.post('/api/export-report',json={'latitude':-88.6,'longitude':-69.3})
    text=response.content.decode('utf-8-sig')
    assert 'Brightness temperature,80.360466,K' in text
    assert 'not a matched-time validation' in text
    assert 'Historical local solar time,6.9009,hour' in text
