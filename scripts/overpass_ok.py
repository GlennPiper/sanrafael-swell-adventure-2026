import json, urllib.parse, urllib.request

overpass='https://overpass-api.de/api/interpreter'
query='''[out:json][timeout:60];
node["name"~"San Rafael",i](38.5,-111.3,39.3,-110.0);
out;'''
body = urllib.parse.urlencode({'data': query}).encode('utf-8')
req=urllib.request.Request(overpass, data=body, headers={'User-Agent':'SanRafaelSwellPlanner/1.0','Content-Type':'application/x-www-form-urlencoded'})
with urllib.request.urlopen(req, timeout=120) as resp:
    data=json.loads(resp.read().decode('utf-8'))
print('elements', len(data.get('elements',[])))
for el in data.get('elements',[])[:10]:
    print(el.get('tags',{}).get('name'), el.get('lat'), el.get('lon'))
