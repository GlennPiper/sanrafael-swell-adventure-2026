import json, urllib.parse, urllib.request

overpass='https://overpass-api.de/api/interpreter'
query='''[out:json][timeout:60];
(
  node["name"~"San Rafael",i](38.5,-111.3,39.3,-110.0);
  way["name"~"San Rafael",i](38.5,-111.3,39.3,-110.0);
  relation["name"~"San Rafael",i](38.5,-111.3,39.3,-110.0);
);
out center;'''
req=urllib.request.Request(overpass, data=query.encode('utf-8'), headers={'User-Agent':'SanRafaelSwellPlanner/1.0'})
with urllib.request.urlopen(req, timeout=90) as resp:
    data=json.loads(resp.read().decode('utf-8'))
print('elements', len(data.get('elements',[])))
# print names containing bridge
for el in data.get('elements', []):
    name = el.get('tags',{}).get('name','')
    if 'bridge' in name.lower() or 'suspension' in name.lower():
        if 'lat' in el and 'lon' in el:
            lat,lon=el['lat'],el['lon']
        else:
            c=el.get('center') or {}
            lat,lon=c.get('lat'),c.get('lon')
        print(name, lat, lon, el.get('type'), el.get('id'))
