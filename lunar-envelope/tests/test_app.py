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

def test_thirty_day_projection_uses_changing_illumination():
    from backend.main import snapshot
    scenario=Scenario(phase=0,latitude=0,longitude=0)
    result=calculate(scenario)
    assert len(result['timeline'])==120 and len(result['curve'])==31
    assert result['timeline'][0]['illuminated'] and not result['timeline'][60]['illuminated']
    assert result['timeline'][0]['potential']==snapshot(scenario)['potential']
    for window in result['screening_windows']:
        samples=[t for t in result['timeline'] if window['start_day'] <= t['day'] < window['end_day']]
        assert samples and all(t['risk']=='LOW' and t['illuminated'] for t in samples)
    assert result['curve'][0]['efficiency']==100
    assert 0 <= result['peak_deposition_day'] < 30
    assert result['cumulative_deposition'] > 0

def test_comparison_and_pdf():
    params={'latitude':-88.6,'longitude':-69.3}
    r=client.post('/api/diviner-comparison',json=params).json()
    assert r['status']=='available' and r['model_temperature_k']>0
    assert 'not model validation' in r['comparison_note']
    assert r['difference_k']==pytest.approx(r['model_temperature_k']-r['observation']['temperature_k'],abs=.01)
    r2=client.post('/api/diviner-comparison',json={'latitude':0,'longitude':0}).json()
    assert r2['status']=='outside_coverage' and 'model_temperature_k' not in r2
    response=client.post('/api/export-report.pdf',json=params)
    assert response.status_code==200 and response.content.startswith(b'%PDF-')
    assert response.headers['content-type']=='application/pdf'

def test_product_specific_ingest(tmp_path):
    import json
    from backend import diviner
    from backend.diviner_ingest import extract
    target=tmp_path/'extract.csv'
    manifest=extract(diviner.DATA/'diviner_subset.tab',target,'subset',-90,-88,-180,180,1000)
    assert manifest['input_rows']==551 and 0 < manifest['selected_rows'] <=551
    assert len(list(csv.DictReader(target.open())))==manifest['selected_rows']
    assert json.loads((tmp_path/'extract.csv.json').read_text())['input_mode']=='subset'
    with pytest.raises(FileExistsError): extract(diviner.DATA/'diviner_subset.tab',target,'subset',-90,-88,-180,180)
    with pytest.raises(ValueError,match='checksum'): extract(diviner.DATA/'diviner_subset.tab',tmp_path/'wrong.csv','full',-90,-88,-180,180)
    with pytest.raises(ValueError,match='limit'): extract(diviner.DATA/'diviner_subset.tab',tmp_path/'limited.csv','subset',-90,-80,-180,180,1)
    assert not (tmp_path/'limited.csv').exists()

def test_endpoint_validation_and_favicon():
    assert client.post('/api/export-report.pdf',json={'phase':30}).status_code==422
    assert client.post('/api/diviner-comparison',json={'latitude':100}).status_code==422
    assert client.get('/favicon.svg').status_code==200

def test_ingestion_handles_pds_boundary_and_missing_constants(tmp_path, monkeypatch):
    from backend import diviner_ingest as module
    source=tmp_path/'input.tab'
    source.write_text('x,y,clon,clat,ltim,tbol\n0,0,0,-79.995525,12,110\n0,0,0,-85,12,-9999\n')
    monkeypatch.setattr(module,'FULL_HASH',module.digest(source))
    monkeypatch.setattr(module,'FULL_COUNT',2)
    manifest=module.extract(source,tmp_path/'output.csv','full',-90,-79.99,-180,180)
    assert manifest['input_rows']==2 and manifest['rejected_rows']==1 and manifest['selected_rows']==1

def test_comparison_uses_observed_location_and_local_time():
    from backend.main import snapshot
    out=client.post('/api/diviner-comparison',json={'latitude':-88.6,'longitude':-69.3}).json()
    obs=out['observation']
    phase=((obs['longitude'] - 15*(obs['local_time_h']-12)) % 360)/360*29.53
    expected=snapshot(Scenario(latitude=obs['latitude'],longitude=obs['longitude'],phase=phase))
    assert out['matched_phase_day']==pytest.approx(phase,abs=.001)
    assert out['model_temperature_k']==expected['temperature']
