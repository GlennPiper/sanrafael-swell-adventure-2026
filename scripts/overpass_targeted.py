import json, urllib.parse, urllib.request

UA='SanRafaelSwellPlanner/1.0'
overpass='https://overpass-api.de/api/interpreter'

def run(q):
    body=urllib.parse.urlencode({'data':q}).encode('utf-8')
    req=urllib.request.Request(overpass, data=body, headers={'User-Agent':UA,'Content-Type':'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode('utf-8'))

def show(label, data, limit=30):
    els=data.get('elements', [])
    print(f"\n=== {label}: {len(els)} matches ===")
    for el in els[:limit]:
        tags=el.get('tags',{})
        name=tags.get('name','')
        lat=el.get('lat'); lon=el.get('lon')
        if lat is None or lon is None:
            c=el.get('center') or {}
            lat,lon=c.get('lat'),c.get('lon')
        extra=[]
        for k in ['historic','tourism','natural','highway','waterway','place','man_made','bridge','ref','route']:
            if k in tags:
                extra.append(f"{k}={tags[k]}")
        print(f"- {name} | {lat},{lon} | {el.get('type')} {el.get('id')} | {';'.join(extra)}")

# bounding boxes
bbox_swell=(38.4,-111.35,39.35,-110.0)
# focus boxes
bbox_buckhorn=(38.85,-110.95,39.25,-110.55)
bbox_blackdragon=(38.85,-110.65,39.05,-110.25)
bbox_eagle=(38.75,-111.05,39.05,-110.65)
bbox_temple=(38.45,-110.90,38.90,-110.45)

queries={
 'Eagle Canyon (name)': f'''[out:json][timeout:120];(node["name"~"Eagle Canyon",i]({bbox_eagle[0]},{bbox_eagle[1]},{bbox_eagle[2]},{bbox_eagle[3]});way["name"~"Eagle Canyon",i]({bbox_eagle[0]},{bbox_eagle[1]},{bbox_eagle[2]},{bbox_eagle[3]}););out center tags;''',
 'Bridge ways near Eagle Canyon': f'''[out:json][timeout:120];way[bridge][highway]({bbox_eagle[0]},{bbox_eagle[1]},{bbox_eagle[2]},{bbox_eagle[3]});out center tags;''',
 'Wedge': f'''[out:json][timeout:120];(node["name"~"Wedge",i]({bbox_swell[0]},{bbox_swell[1]},{bbox_swell[2]},{bbox_swell[3]});way["name"~"Wedge",i]({bbox_swell[0]},{bbox_swell[1]},{bbox_swell[2]},{bbox_swell[3]}););out center tags;''',
 'Warrior': f'''[out:json][timeout:120];(node["name"~"Warrior",i]({bbox_temple[0]},{bbox_temple[1]},{bbox_temple[2]},{bbox_temple[3]});way["name"~"Warrior",i]({bbox_temple[0]},{bbox_temple[1]},{bbox_temple[2]},{bbox_temple[3]}););out center tags;''',
 'Sinbad': f'''[out:json][timeout:120];(node["name"~"Sinbad",i]({bbox_swell[0]},{bbox_swell[1]},{bbox_swell[2]},{bbox_swell[3]});way["name"~"Sinbad",i]({bbox_swell[0]},{bbox_swell[1]},{bbox_swell[2]},{bbox_swell[3]}););out center tags;''',
 'Temple Wash Petroglyph/Pictograph': f'''[out:json][timeout:120];(node["name"~"Temple.*(Wash|Mountain).*(Pict|Petro)",i]({bbox_temple[0]},{bbox_temple[1]},{bbox_temple[2]},{bbox_temple[3]});way["name"~"Temple.*(Wash|Mountain).*(Pict|Petro)",i]({bbox_temple[0]},{bbox_temple[1]},{bbox_temple[2]},{bbox_temple[3]}););out center tags;''',
 'Bridge ways near Buckhorn/San Rafael': f'''[out:json][timeout:120];way[bridge][highway]({bbox_buckhorn[0]},{bbox_buckhorn[1]},{bbox_buckhorn[2]},{bbox_buckhorn[3]});out center tags;''',
}

for label,q in queries.items():
    try:
        data=run(q)
    except Exception as e:
        print(f"\n=== {label}: ERROR {e} ===")
        continue
    show(label, data)
