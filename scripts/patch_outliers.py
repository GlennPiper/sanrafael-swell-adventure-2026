import json, pathlib

p=pathlib.Path('places_geocoded_complete.json')
rows=json.loads(p.read_text(encoding='utf-8'))
by={r['place']: r for r in rows}

def skip(place, reason):
    r=by[place]
    r['lat']=None
    r['lon']=None
    r['method']='skipped'
    r['notes']=reason
    r['display_name']=r.get('display_name') or None

# Fix mis-geocode: Hidden Splendor should be in the Swell. We already found OSM matches.
if 'Hidden Splendor' in by:
    r=by['Hidden Splendor']
    r['lat']=38.5658209
    r['lon']=-110.9536762
    r['display_name']='Hidden Splendor Overlook (OSM)'
    r['method']='overpass'
    r['notes']='Corrected: earlier geocode matched a different Hidden Splendor in northern Utah; using OSM Hidden Splendor Overlook in the Swell.'

# Fix duplicate/wrong town: Green River, UT should be the town of Green River near the Swell.
if 'Green River, UT' in by and 'Green River' in by:
    gr=by['Green River']
    r=by['Green River, UT']
    r['lat']=gr['lat']
    r['lon']=gr['lon']
    r['display_name']='Green River, Utah (proxy from Green River)'
    r['method']='derived'
    r['notes']='Corrected: earlier geocode was wrong; using same coordinates as Green River (town near the Swell).'

# If we canâ€™t confidently locate these in 1-2 tries, skip rather than risk bad pins.
for place, reason in [
    ('Split Rock', 'Skipped: could not confidently locate a San Rafael Swell Split Rock in quick lookups; left blank to avoid wrong pin.'),
    ('The Icebox', 'Skipped: could not confidently locate the San Rafael Swell Icebox in quick lookups; left blank to avoid wrong pin.'),
]:
    if place in by:
        skip(place, reason)

# Clean up any weird quote encoding in notes (turn curly quotes into plain)
for r in rows:
    for k in ['notes','display_name']:
        v=r.get(k)
        if isinstance(v,str):
            r[k]=v.replace('Ã¢â‚¬Å“','"').replace('Ã¢â‚¬Â','"').replace('â€™',"'").replace('â€œ','"').replace('â€','"')

out=list(by.values())
pathlib.Path('places_geocoded_complete.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
print('patched places_geocoded_complete.json')

# show skipped
sk=[r['place'] for r in out if r.get('method')=='skipped']
print('skipped:', sk)
