import re, pathlib, json
text = pathlib.Path('Trip Details from Chuck.md').read_text(encoding='utf-8')
places=set()

camp_section = re.search(r"Camping Recommendations[\s\S]*?Discovery Points:", text)
if camp_section:
    for line in camp_section.group(0).splitlines():
        line=line.strip()
        if not line or line.endswith(':'):
            continue
        if line.startswith(('Camping', 'The Swell', 'Some of', 'Discovery')):
            continue
        if re.match(r"^[A-Za-z0-9'\-\.\(\) ]+$", line):
            places.add(line)

disc_section = re.search(r"Discovery Points:[\s\S]*?Route Details:", text)
if disc_section:
    for m in re.finditer(r"^\s*\d+\.?\s*(.+?)\s*$", disc_section.group(0), flags=re.M):
        places.add(m.group(1))

keywords = [
    'Canyon','Wash','Road','Trail','Overlook','Arch','Bridge','River','Butte','Mountain','Window','Cabins','Cabin','Footprint','Tunnel','Head','Racetrack','Sinkhole','Icebox','Wedge','Reef','Splendor'
]
for kw in keywords:
    for m in re.finditer(rf"\b([A-Z][A-Za-z0-9'\-\. ]{{2,}}?\s{re.escape(kw)}(?:'s)?)\b", text):
        places.add(m.group(1).strip())

ban = {
    'Fuel, Provisions, and Recommended Gear','Fuel','Provisions','Gear','Alternate route option','Freeway Access','Typical Terrain','Route Details','Updated'
}
places = {p for p in places if p not in ban}
places = {re.sub(r"\s+", " ", p).strip(' .') for p in places}

fix = {
    'Petroglpyh Canyon Panel':'Petroglyph Canyon Panel',
    'Black Dragon Canyon petroglpyhs':'Black Dragon Canyon petroglyphs',
    'Buckhorn Wash petroglpyhs':'Buckhorn Wash petroglyphs',
    'Temple Wash Petroglpyhs':'Temple Wash Petroglyphs',
    'North Template Mountain wash':'North Temple Mountain Wash',
    'Template Mountain road':'Temple Mountain Road',
    'Template mountain':'Temple Mountain',
    "Swasey Cabin's":'Swasey Cabins',
    '35.North Temple Wash':'North Temple Wash'
}
places2=set(fix.get(p,p) for p in places)
places=sorted(places2)

print('extracted', len(places))
for p in places:
    print('-', p)

pathlib.Path('extracted_places.json').write_text(json.dumps(places, indent=2), encoding='utf-8')
print('wrote extracted_places.json')
