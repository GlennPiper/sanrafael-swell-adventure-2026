import json, re, pathlib
raw = json.loads(pathlib.Path('extracted_places.json').read_text(encoding='utf-8'))

def is_noise(s: str) -> bool:
    if len(s) > 55:
        return True
    if any(ch in s for ch in [',',';']):
        return True
    if s.count(' ') > 8:
        return True
    bad_phrases = [
        'Those seeking', 'Full size vehicles', 'Buckhorn Draw Road is',
        'Soon enough', 'Notice the change', 'Head to the', 'Heading down',
        'Making your way', 'Once you', 'Trail. ', 'Grand Canyon. From'
    ]
    if any(bp in s for bp in bad_phrases):
        return True
    if s.lower().startswith(('the end of','east of','i-70.')):
        return True
    if s in {'Peak Trail','Peak Trail Rating: 6','Peak Trail Rating'}:
        return True
    return False

clean=[]
for s in raw:
    s = s.strip()
    if is_noise(s):
        continue
    # strip parenthetical notes
    s = re.sub(r"\s*\([^\)]*\)\s*$", "", s).strip()
    # normalize some variants
    s = s.replace('Reds Canyon', 'Red Canyon') if s == 'Reds Canyon' else s
    s = s.replace('Reds Canyon and McKay Flat Road', 'McKay Flat Road') if s == 'Reds Canyon and McKay Flat Road' else s
    if s == 'Along the San Rafael River':
        s = 'San Rafael River'
    if s == 'Along the San Rafael River on Mexican Mountain':
        s = 'Mexican Mountain Road'
    if s == 'Along the San Rafael River on Mexican Mountain Road':
        s = 'Mexican Mountain Road'
    if s == 'North Template Mountain':
        s = 'Temple Mountain'
    if s == 'North Template Mountain wash (can get busy)':
        s = 'North Temple Mountain Wash'
    if s == 'Behind the Reef vicinity':
        s = 'Behind the Reef Trail'
    if s == 'Behind the Reef':
        s = 'Behind the Reef Trail'
    if s == 'Trail. Behind the Reef':
        s = 'Behind the Reef Trail'
    if s == 'The Wedge':
        s = 'The Wedge (San Rafael Swell)'
    if s == 'Mexican Mountain':
        s = 'Mexican Mountain'
    clean.append(s)

# add a few important ones mentioned in text but not caught
extras = [
    'Castle Dale, UT',
    'Emery, UT',
    'Hanksville, UT',
    'Green River, UT',
    'Sinbad\'s Head',
    'Coal Wash',
    'Dutch Flat',
    'Temple Mountain Wash',
    'Temple Mountain Road',
    'Hidden Splendor Road'
]
for e in extras:
    clean.append(e)

# dedupe preserving order
seen=set(); out=[]
for s in clean:
    if not s or s in seen:
        continue
    seen.add(s)
    out.append(s)

pathlib.Path('places_clean.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
print('clean count', len(out))
for s in out:
    print('-', s)
