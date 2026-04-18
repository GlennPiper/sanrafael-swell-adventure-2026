import json, pathlib, time, urllib.parse, urllib.request

UA = 'SanRafaelSwellPlanner/1.0 (personal trip planning; Cursor script)'

places = json.loads(pathlib.Path('places_clean.json').read_text(encoding='utf-8'))
# fix typos + add disambiguation hints
rewrite = {
    'Petroglyph Canyon Panel': 'Petroglyph Canyon Panel, Buckhorn Wash, Utah',
    'Petroglyph Canyon': 'Petroglyph Canyon, San Rafael Swell, Utah',
    'Black Dragon Canyon petroglyphs': 'Black Dragon Canyon Pictographs, Utah',
    'Buckhorn Wash petroglyphs': 'Buckhorn Wash Pictographs, Utah',
    "Sinbad's Head": "Head of Sinbad pictograph panel, Utah",
    'Head of Sinbad': "Head of Sinbad pictograph panel, Utah",
    'The Wedge (San Rafael Swell)': 'The Wedge Overlook, Utah',
    'Little Grand Canyon': 'Little Grand Canyon, San Rafael Swell, Utah',
    'Red Canyon': 'Reds Canyon, San Rafael Swell, Utah',
    'McKay Flat Road': 'McKay Flat Road, Emery County, Utah',
    'San Rafael River Road': 'San Rafael River Road, Utah',
    'Mexican Mountain Road': 'Mexican Mountain Road, Emery County, Utah',
    'Eagle Canyon': 'Eagle Canyon, San Rafael Swell, Utah',
    'Eagle Canyon Arch': 'Eagle Canyon Arch, San Rafael Swell, Utah',
    'Eagle Canyon Trail': 'Eagle Canyon Trail, San Rafael Swell, Utah',
    'Behind the Reef Trail': 'Behind the Reef Road, San Rafael Swell, Utah',
    'Temple Mountain': 'Temple Mountain, San Rafael Swell, Utah',
    'Temple Mountain Road': 'Temple Mountain Road, San Rafael Swell, Utah',
    'Temple Mountain Wash': 'Temple Mountain Wash, San Rafael Swell, Utah',
    'North Temple Wash': 'North Temple Wash, San Rafael Swell, Utah',
    'Dutch Flat Road': 'Dutch Flat Road, San Rafael Swell, Utah',
    'Dutchman Arch': 'Dutchman Arch, Utah',
    'Devil\'s Racetrack': "Devil's Racetrack, San Rafael Swell, Utah",
    'Wild Horse Window': 'Wild Horse Window, San Rafael Swell, Utah',
    'Hidden Splendor': 'Hidden Splendor, Utah',
    'Hidden Splendor Overlook': 'Hidden Splendor Overlook, Utah',
    'Hidden Splendor Road': 'Hidden Splendor Road, Utah',
    'Swasey Cabins': 'Swasey Cabin, Utah',
    'Coal Wash': 'Coal Wash, San Rafael Swell, Utah',
    'The Sinkhole': 'The Sinkhole, San Rafael Swell, Utah',
    'The Icebox': 'Icebox Canyon, San Rafael Swell, Utah',
    'The Drips': 'The Drips, San Rafael Swell, Utah',
    'Split Rock': 'Split Rock, San Rafael Swell, Utah',
}

# de-dup with stable ordering
seen=set(); place_list=[]
for p in places:
    p2 = p.replace('Petroglpyh', 'Petroglyph').replace('North Template Mountain wash', 'North Temple Mountain Wash')
    if p2 not in seen:
        seen.add(p2)
        place_list.append(p2)


def nominatim_search(q: str):
    base = 'https://nominatim.openstreetmap.org/search'
    params = {
        'q': q,
        'format': 'jsonv2',
        'limit': 1,
        'addressdetails': 1
    }
    url = base + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    return data[0] if data else None

results=[]
for i, place in enumerate(place_list, start=1):
    # build query
    q = rewrite.get(place)
    if not q:
        if ', UT' in place or ', Utah' in place:
            q = place
        elif place.endswith(', UT'):
            q = place
        else:
            q = f"{place}, San Rafael Swell, Utah"

    hit = None
    tried=[]
    for attempt in [q, f"{place}, Emery County, Utah", f"{place}, Utah"]:
        if attempt in tried:
            continue
        tried.append(attempt)
        try:
            hit = nominatim_search(attempt)
        except Exception as e:
            hit = {'_error': str(e)}
        if hit and '_error' not in hit:
            break
        time.sleep(1.1)

    if hit and '_error' not in hit:
        results.append({
            'place': place,
            'query': tried[-1],
            'lat': float(hit['lat']),
            'lon': float(hit['lon']),
            'display_name': hit.get('display_name'),
            'type': hit.get('type'),
            'class': hit.get('class'),
            'importance': hit.get('importance'),
        })
    else:
        results.append({'place': place, 'query': q, 'lat': None, 'lon': None, 'display_name': None, 'type': None, 'class': None, 'importance': None, 'error': hit.get('_error') if isinstance(hit, dict) else None})

    # respectful rate limiting
    time.sleep(1.1)
    if i % 10 == 0:
        print('geocoded', i, 'of', len(place_list))

pathlib.Path('places_geocoded.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
print('wrote places_geocoded.json')
print('success', sum(1 for r in results if r['lat'] is not None), 'of', len(results))
fail=[r['place'] for r in results if r['lat'] is None]
if fail:
    print('failed:', fail)
