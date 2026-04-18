import json, pathlib
rows=json.loads(pathlib.Path('places_geocoded.json').read_text(encoding='utf-8'))

# Define broad bounding box covering UT + a bit (to catch towns too)
# Utah roughly: lat 36.9-42.1 lon -114.1 to -109.0
UT_BBOX = (36.5, 42.5, -114.7, -108.5)

def in_bbox(lat, lon, bbox):
    mnlat, mxlat, mnlon, mxlon = bbox
    return (lat is not None and lon is not None and mnlat <= lat <= mxlat and mnlon <= lon <= mxlon)

outliers=[]
for r in rows:
    if r.get('lat') is None:
        continue
    if not in_bbox(r['lat'], r['lon'], UT_BBOX):
        outliers.append((r['place'], r['lat'], r['lon'], r.get('display_name')))

print('outliers', len(outliers))
for o in outliers[:50]:
    print('-', o[0], o[1], o[2], '|', o[3])

# also print a compact list for quick manual review
print('\nSample successes:')
for r in rows[:15]:
    print(r['place'], '=>', r.get('lat'), r.get('lon'), '|', (r.get('display_name') or '')[:80])
