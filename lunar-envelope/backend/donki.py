"""Optional, explicitly requested NASA CCMC event context; never affects models."""
from datetime import datetime, timedelta, timezone
from functools import lru_cache
import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SOURCE='https://kauai.ccmc.gsfc.nasa.gov/DONKI/WS/get/CME'

@lru_cache(maxsize=16)
def _fetch(start, end, bucket):
    url=SOURCE+'?'+urlencode({'startDate':start,'endDate':end})
    request=Request(url,headers={'Accept':'application/json','User-Agent':'Lunaris/0.3'})
    with urlopen(request,timeout=8) as response:
        data=response.read(2_000_001)
    if len(data)>2_000_000: raise ValueError('NASA response exceeded size limit')
    payload=json.loads(data)
    if not isinstance(payload,list): raise ValueError('Unexpected NASA event format')
    events=[]
    for item in payload[:100]:
        if isinstance(item,dict):
            events.append({'id':str(item.get('activityID',''))[:150], 'start':str(item.get('startTime',''))[:50],
                           'source_location':str(item.get('sourceLocation',''))[:40]})
    return datetime.now(timezone.utc).isoformat(), tuple((x['id'],x['start'],x['source_location']) for x in events)

def recent(days=7):
    if os.environ.get('LUNARIS_DONKI_ENABLED')!='1':
        return {'status':'disabled','events':[],'message':'Live NASA DONKI connection disabled. Set LUNARIS_DONKI_ENABLED=1 on the server to enable.'}
    now=datetime.now(timezone.utc); start=(now-timedelta(days=days)).date().isoformat();end=now.date().isoformat()
    try:
        fetched_at,rows=_fetch(start,end,int(now.timestamp())//600)
    except (OSError,ValueError,TimeoutError) as exc:
        return {'status':'unavailable','events':[],'message':'NASA DONKI could not be reached or returned invalid data; no events inferred.', 'source':SOURCE}
    return {'status':'available','events':[{'id':a,'start':b,'source_location':c} for a,b,c in rows],
            'source':SOURCE,'queried_utc':fetched_at,'cache_ttl_minutes':10,
            'message':'NASA CCMC event context only, not measured lunar conditions or a forecast.'}
