import json, pathlib, time, urllib.parse, urllib.request, re

UA = 'SanRafaelSwellPlanner/1.0 (personal trip planning; Cursor script)'

rows = json.loads(pathlib.Path('places_geocoded.json').read_text(encoding='utf-8'))
by_place = {r['place']: r for r in rows}

# helper

def nominatim(q: str):
    base = 'https://nominatim.openstreetmap.org/search'
    params = {'q': q, 'format':'jsonv2', 'limit':1, 'addressdetails':1}
    url = base + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    return (data[0] if data else None), url

def fill(place, q):
    hit, url = nominatim(q)
    if not hit:
        return False
    r = by_place[place]
    r['lat'] = float(hit['lat'])
    r['lon'] = float(hit['lon'])
    r['display_name'] = hit.get('display_name')
    r['type'] = hit.get('type')
    r['class'] = hit.get('class')
    r['importance'] = hit.get('importance')
    r['query'] = q
    r['lookup_url'] = url
    r['method'] = 'nominatim_retry'
    return True

missing = [p for p,r in by_place.items() if r.get('lat') is None]

# 1) Derive coords for vicinity/area entries
for p in list(missing):
    m = re.match(r"^(.*?)(?:\s+(?:vicinity|Vicinity|area|Area))$", p)
    if m:
        base = m.group(1).strip()
        if base in by_place and by_place[base].get('lat') is not None:
            r = by_place[p]
            r['lat'] = by_place[base]['lat']
            r['lon'] = by_place[base]['lon']
            r['display_name'] = by_place[base].get('display_name')
            r['query'] = f"derived from {base}"
            r['method'] = 'derived'
            r['notes'] = f"Used same coordinates as {base}."

# refresh missing
missing = [p for p,r in by_place.items() if r.get('lat') is None]

# 2) Retry with better queries for the true misses
retry_queries = {
    'Black Dragon Canyon petroglyphs': [
        'Black Dragon Canyon Pictograph Panel, Utah',
        'Black Dragon Canyon pictographs, Emery County, Utah'
    ],
    'Buckhorn Wash petroglyphs': [
        'Buckhorn Wash Pictograph Panel, Utah',
        'Buckhorn Wash pictographs, Emery County, Utah'
    ],
    "Sinbad's Head": [
        "Head of Sinbad, Utah",
        "Head of Sinbad pictograph panel, Utah",
        "Sinbad's Head pictograph, Utah"
    ],
    'Old San Rafael Swinging Bridge': [
        'San Rafael Swinging Bridge, Utah',
        'San Rafael River Swinging Bridge, Emery County, Utah'
    ],
    'Temple Wash Petroglyphs': [
        'Temple Mountain Wash Petroglyphs, Utah',
        'Temple Mountain Wash pictographs, Utah'
    ],
    'Eagle Canyon Bridges': [
        'Eagle Canyon Bridge, Emery County, Utah',
        'Eagle Canyon I-70 Bridge, Utah'
    ],
    'Loan Warrior Petroglyph': [
        'Lone Warrior Panel, San Rafael Swell, Utah',
        'Lone Warrior Petroglyphs, Utah'
    ],
    'Circa Loan Warrior petroglyph': [
        'Lone Warrior Panel, San Rafael Swell, Utah',
        'Lone Warrior Petroglyphs, Utah'
    ],
    'North Temple Mountain Wash': [
        'North Temple Wash, San Rafael Swell, Utah',
        'North Temple Mountain Wash, Emery County, Utah'
    ],
    'The Wedge (San Rafael Swell)': [
        'The Wedge Overlook, Utah',
        'Wedge Overlook, San Rafael Swell, Utah'
    ],
    'Tomsich Butte Uranium Mine': [
        'Tomsich Butte, Emery County, Utah',
        'Temple Mountain mining district, Utah'
    ]
}

for p in [p for p,r in by_place.items() if r.get('lat') is None]:
    for q in retry_queries.get(p, []):
        try:
            ok = fill(p, q)
        except Exception as e:
            ok = False
            by_place[p]['error'] = str(e)
        time.sleep(1.1)
        if ok:
            break

# 3) If still missing, attempt a last-ditch "<place>, Emery County, Utah"
for p in [p for p,r in by_place.items() if r.get('lat') is None]:
    try:
        ok = fill(p, f"{p}, Emery County, Utah")
    except Exception as e:
        ok = False
        by_place[p]['error'] = str(e)
    time.sleep(1.1)

final = list(by_place.values())
pathlib.Path('places_geocoded_final.json').write_text(json.dumps(final, indent=2), encoding='utf-8')
print('wrote places_geocoded_final.json')
print('success', sum(1 for r in final if r.get('lat') is not None), 'of', len(final))
print('still missing:', [r['place'] for r in final if r.get('lat') is None])
