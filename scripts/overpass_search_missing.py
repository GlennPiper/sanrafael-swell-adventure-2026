import json, urllib.parse, urllib.request, re

overpass='https://overpass-api.de/api/interpreter'
UA='SanRafaelSwellPlanner/1.0'
# Swell-ish bbox
bbox=(38.4,-111.35,39.35,-110.0)  # (south, west, north, east)

patterns={
  'Black Dragon': 'Black Dragon',
  'Buckhorn': 'Buckhorn',
  'Wedge': 'Wedge',
  'Swinging Bridge': 'Swinging|Suspension',
  'Eagle Canyon': 'Eagle Canyon',
  'Temple Wash': 'Temple.*Wash',
  'Lone Warrior': 'Lone.*Warrior|Loan.*Warrior',
  'Sinbad': 'Sinbad',
}

query_tmpl='''[out:json][timeout:120];
(
  node["name"~"{pat}",i]({s},{w},{n},{e});
  way["name"~"{pat}",i]({s},{w},{n},{e});
  relation["name"~"{pat}",i]({s},{w},{n},{e});
  node["tourism"="viewpoint"]["name"~"{pat}",i]({s},{w},{n},{e});
  node["historic"]["name"~"{pat}",i]({s},{w},{n},{e});
);
out center tags;'''

for label, pat in patterns.items():
    q=query_tmpl.format(pat=pat, s=bbox[0], w=bbox[1], n=bbox[2], e=bbox[3])
    body = urllib.parse.urlencode({'data': q}).encode('utf-8')
    req = urllib.request.Request(overpass, data=body, headers={'User-Agent':UA,'Content-Type':'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    els=data.get('elements',[])
    print('\n===', label, 'pattern:', pat, 'matches:', len(els), '===')
    for el in els[:30]:
        tags=el.get('tags',{})
        name=tags.get('name','')
        lat=el.get('lat')
        lon=el.get('lon')
        if lat is None or lon is None:
            c=el.get('center') or {}
            lat,lon=c.get('lat'),c.get('lon')
        extra=[]
        for k in ['historic','tourism','natural','amenity','highway','waterway','place']:
            if k in tags:
                extra.append(f"{k}={tags[k]}")
        print(f"- {name} | {lat},{lon} | {el.get('type')} {el.get('id')} | {';'.join(extra)}")
