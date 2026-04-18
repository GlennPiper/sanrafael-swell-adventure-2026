import json, pathlib, re
from difflib import SequenceMatcher

def norm(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def load_geojson(path):
    p = pathlib.Path(path)
    data = json.loads(p.read_text(encoding='utf-8'))
    feats = data.get('features', [])
    out=[]
    for f in feats:
        props = f.get('properties', {})
        loc = props.get('location', {}) if 'location' in props else props
        name = loc.get('name') or props.get('name')
        if not name:
            continue
        coords = f.get('geometry', {}).get('coordinates')
        if not coords or len(coords) < 2:
            continue
        lon, lat = coords[0], coords[1]
        out.append({'name': name, 'lat': float(lat), 'lon': float(lon), 'file': path})
    return out

places = json.loads(pathlib.Path('places_clean.json').read_text(encoding='utf-8'))
# normalize a couple of typos in the place list
places = [p.replace('Petroglpyh', 'Petroglyph').replace('North Template Mountain wash', 'North Temple Mountain Wash') for p in places]

points=[]
for fp in [
    'Takeout/Maps (your places)/Saved Places.json',
    'Takeout/Maps (your places)/Reviews.json',
    'Takeout/Maps/My labeled places/Labeled places.json'
]:
    points.extend(load_geojson(fp))

# index for exact matches
idx = {}
for pt in points:
    idx.setdefault(norm(pt['name']), []).append(pt)

results=[]
for place in places:
    n = norm(place)
    match = None
    # exact normalized match
    if n in idx:
        match = idx[n][0]
        results.append({'place': place, 'lat': match['lat'], 'lon': match['lon'], 'source':'takeout', 'matched_name': match['name'], 'confidence': 1.0})
        continue
    # fuzzy match: pick best within threshold
    best=None
    for pt in points:
        r = SequenceMatcher(None, n, norm(pt['name'])).ratio()
        if best is None or r > best[0]:
            best=(r, pt)
    if best and best[0] >= 0.86:
        r, pt = best
        results.append({'place': place, 'lat': pt['lat'], 'lon': pt['lon'], 'source':'takeout_fuzzy', 'matched_name': pt['name'], 'confidence': round(r,3)})
    else:
        results.append({'place': place, 'lat': None, 'lon': None, 'source': None, 'matched_name': None, 'confidence': None})

pathlib.Path('places_with_coords_from_takeout.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
matched = sum(1 for r in results if r['lat'] is not None)
print('takeout matched', matched, 'of', len(results))
# show any matched that look like Utah-ish (lon between -115 and -109)
for r in results:
    if r['lat'] is not None and -115.5 < r['lon'] < -108.0 and 36.5 < r['lat'] < 41.5:
        print('UT?', r['place'], '=>', r['matched_name'], r['lat'], r['lon'], r['source'], r['confidence'])
