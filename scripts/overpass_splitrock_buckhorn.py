import json, urllib.parse, urllib.request
UA='SanRafaelSwellPlanner/1.0'
overpass='https://overpass-api.de/api/interpreter'

bbox=(38.9,-110.85,39.25,-110.55) # Buckhorn-ish
term='Split Rock'
query=f'''[out:json][timeout:60];(
  node["name"~"{term}",i]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
  way["name"~"{term}",i]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
);out center tags;'''
body=urllib.parse.urlencode({'data':query}).encode('utf-8')
req=urllib.request.Request(overpass, data=body, headers={'User-Agent':UA,'Content-Type':'application/x-www-form-urlencoded'})
with urllib.request.urlopen(req, timeout=120) as resp:
    data=json.loads(resp.read().decode('utf-8'))
els=data.get('elements',[])
print('matches',len(els))
for el in els[:50]:
    tags=el.get('tags',{})
    name=tags.get('name','')
    lat=el.get('lat'); lon=el.get('lon')
    if lat is None or lon is None:
        c=el.get('center') or {}
        lat,lon=c.get('lat'),c.get('lon')
    kind = tags.get('natural') or tags.get('place') or tags.get('tourism') or tags.get('historic') or ''
    print('-',name,'|',lat,lon,'|',kind)
