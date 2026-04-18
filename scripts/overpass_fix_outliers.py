import json, urllib.parse, urllib.request
UA='SanRafaelSwellPlanner/1.0'
overpass='https://overpass-api.de/api/interpreter'

# bbox around Hidden Splendor / Temple Mountain area
bbox=(38.45,-111.05,38.75,-110.75)  # south, west, north, east

query=f'''[out:json][timeout:120];(
  node["name"~"Hidden Splendor",i]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
  way["name"~"Hidden Splendor",i]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
  node["name"~"Icebox",i]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
  way["name"~"Icebox",i]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
  node["name"~"Split Rock",i]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
  way["name"~"Split Rock",i]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
);
out center tags;'''

body=urllib.parse.urlencode({'data':query}).encode('utf-8')
req=urllib.request.Request(overpass, data=body, headers={'User-Agent':UA,'Content-Type':'application/x-www-form-urlencoded'})
with urllib.request.urlopen(req, timeout=180) as resp:
    data=json.loads(resp.read().decode('utf-8'))

els=data.get('elements',[])
print('matches',len(els))
for el in els[:40]:
    tags=el.get('tags',{})
    name=tags.get('name','')
    lat=el.get('lat'); lon=el.get('lon')
    if lat is None or lon is None:
        c=el.get('center') or {}
        lat,lon=c.get('lat'),c.get('lon')
    extra=[]
    for k in ['tourism','historic','natural','highway','place','waterway']:
        if k in tags:
            extra.append(f"{k}={tags[k]}")
    print('-',name,'|',lat,lon,'|',el.get('type'),el.get('id'),'|',';'.join(extra))
