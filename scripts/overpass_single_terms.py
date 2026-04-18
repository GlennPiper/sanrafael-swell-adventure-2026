import json, urllib.parse, urllib.request
UA='SanRafaelSwellPlanner/1.0'
overpass='https://overpass-api.de/api/interpreter'

def run(term, bbox):
    q=f'''[out:json][timeout:60];(
      node["name"~"{term}",i]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
      way["name"~"{term}",i]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
    );out center tags;'''
    body=urllib.parse.urlencode({'data': q}).encode('utf-8')
    req=urllib.request.Request(overpass, data=body, headers={'User-Agent':UA,'Content-Type':'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data=json.loads(resp.read().decode('utf-8'))
    els=data.get('elements',[])
    print('\n===',term,'matches',len(els),'===')
    for el in els[:30]:
        tags=el.get('tags',{})
        name=tags.get('name','')
        lat=el.get('lat'); lon=el.get('lon')
        if lat is None or lon is None:
            c=el.get('center') or {}
            lat,lon=c.get('lat'),c.get('lon')
        kind = tags.get('tourism') or tags.get('historic') or tags.get('natural') or tags.get('place') or tags.get('highway') or ''
        print('-',name,'|',lat,lon,'|',kind)

bbox=(38.45,-111.05,38.75,-110.75)
for term in ['Hidden Splendor','Icebox','Split Rock']:
    try:
        run(term, bbox)
    except Exception as e:
        print('\n===',term,'ERROR',e,'===')
