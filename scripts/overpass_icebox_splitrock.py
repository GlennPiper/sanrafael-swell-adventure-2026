import json, urllib.parse, urllib.request
UA='SanRafaelSwellPlanner/1.0'
overpass='https://overpass-api.de/api/interpreter'

def run(q):
    body=urllib.parse.urlencode({'data': q}).encode('utf-8')
    req=urllib.request.Request(overpass, data=body, headers={'User-Agent':UA,'Content-Type':'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode('utf-8'))

def show(label, data, limit=40):
    els=data.get('elements',[])
    print('\n===',label,'matches',len(els),'===')
    for el in els[:limit]:
        tags=el.get('tags',{})
        name=tags.get('name','')
        lat=el.get('lat'); lon=el.get('lon')
        if lat is None or lon is None:
            c=el.get('center') or {}
            lat,lon=c.get('lat'),c.get('lon')
        kind = tags.get('tourism') or tags.get('historic') or tags.get('natural') or tags.get('place') or tags.get('highway') or ''
        print('-',name,'|',lat,lon,'|',kind)

bbox=(38.45,-111.05,38.95,-110.45)
q1=f'''[out:json][timeout:120];(node["name"~"Icebox",i]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});way["name"~"Icebox",i]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}););out center tags;'''
q2=f'''[out:json][timeout:120];(node["name"~"Split Rock",i]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});way["name"~"Split Rock",i]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}););out center tags;'''

for label,q in [('Icebox (bigger bbox)', q1), ('Split Rock (bigger bbox)', q2)]:
    try:
        show(label, run(q))
    except Exception as e:
        print('\n===',label,'ERROR',e,'===')
