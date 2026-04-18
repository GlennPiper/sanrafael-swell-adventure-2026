import json, urllib.parse, urllib.request

UA='SanRafaelSwellPlanner/1.0'
overpass='https://overpass-api.de/api/interpreter'

def run(q, timeout=180):
    body=urllib.parse.urlencode({'data':q}).encode('utf-8')
    req=urllib.request.Request(overpass, data=body, headers={'User-Agent':UA,'Content-Type':'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8'))

def show(label, data, limit=40):
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
        for k in ['historic','tourism','natural','highway','waterway','place','man_made','bridge','ref','amenity']:
            if k in tags:
                extra.append(f"{k}={tags[k]}")
        print(f"- {name} | {lat},{lon} | {el.get('type')} {el.get('id')} | {';'.join(extra)}")

# very small bbox around Eagle Canyon area (from existing Nominatim hits)
# Eagle Canyon approx center: 38.86, -110.86
bbox_eagle_small=(38.80,-110.98,38.92,-110.78)

q1=f'''[out:json][timeout:120];(node["name"~"Eagle Canyon",i]({bbox_eagle_small[0]},{bbox_eagle_small[1]},{bbox_eagle_small[2]},{bbox_eagle_small[3]});way["name"~"Eagle Canyon",i]({bbox_eagle_small[0]},{bbox_eagle_small[1]},{bbox_eagle_small[2]},{bbox_eagle_small[3]}););out center tags;'''
q2=f'''[out:json][timeout:120];(
  way["bridge"~"yes|viaduct|suspension",i][highway]({bbox_eagle_small[0]},{bbox_eagle_small[1]},{bbox_eagle_small[2]},{bbox_eagle_small[3]});
  way[bridge][highway]({bbox_eagle_small[0]},{bbox_eagle_small[1]},{bbox_eagle_small[2]},{bbox_eagle_small[3]});
);
out center tags;'''
q3=f'''[out:json][timeout:120];(
  way["ref"~"I ?70",i][highway=motorway]({bbox_eagle_small[0]},{bbox_eagle_small[1]},{bbox_eagle_small[2]},{bbox_eagle_small[3]});
  way["ref"~"I ?70",i][highway=motorway_link]({bbox_eagle_small[0]},{bbox_eagle_small[1]},{bbox_eagle_small[2]},{bbox_eagle_small[3]});
);
out center tags;'''

for label,q in [('Eagle Canyon (small bbox)', q1), ('Bridge ways (small bbox)', q2), ('I-70 ways (small bbox)', q3)]:
    try:
        data=run(q)
        show(label, data)
    except Exception as e:
        print(f"\n=== {label}: ERROR {e} ===")

# Buckhorn bridge candidate search: smaller bbox around San Rafael River + Buckhorn Draw corridor
bbox_buck_small=(38.85,-110.78,39.05,-110.55)
q4=f'''[out:json][timeout:120];(
  way[bridge][highway]({bbox_buck_small[0]},{bbox_buck_small[1]},{bbox_buck_small[2]},{bbox_buck_small[3]});
  node["name"~"(Swing|Suspension)",i]({bbox_buck_small[0]},{bbox_buck_small[1]},{bbox_buck_small[2]},{bbox_buck_small[3]});
  way["name"~"(Swing|Suspension)",i]({bbox_buck_small[0]},{bbox_buck_small[1]},{bbox_buck_small[2]},{bbox_buck_small[3]});
);
out center tags;'''
try:
    data=run(q4)
    show('Buckhorn/San Rafael bridges (small bbox)', data)
except Exception as e:
    print('\n=== Buckhorn/San Rafael bridges (small bbox): ERROR', e, '===')

# Sinbad: small bbox near I-70 west end of Swell-ish (approx -110.95..-110.6, 38.85..39.05)
bbox_sinbad=(38.80,-110.95,39.05,-110.55)
q5=f'''[out:json][timeout:120];(node["name"~"Sinbad",i]({bbox_sinbad[0]},{bbox_sinbad[1]},{bbox_sinbad[2]},{bbox_sinbad[3]});way["name"~"Sinbad",i]({bbox_sinbad[0]},{bbox_sinbad[1]},{bbox_sinbad[2]},{bbox_sinbad[3]}););out center tags;'''
try:
    data=run(q5)
    show('Sinbad (small bbox)', data)
except Exception as e:
    print('\n=== Sinbad (small bbox): ERROR', e, '===')
