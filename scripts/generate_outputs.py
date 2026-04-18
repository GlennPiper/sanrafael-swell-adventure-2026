import json, pathlib, html
from datetime import datetime

rows=json.loads(pathlib.Path('places_geocoded_complete.json').read_text(encoding='utf-8'))
rows_sorted=sorted(rows, key=lambda r: r['place'].lower())

# Places that are recommended campsites (from "Camping Recommendations" in Trip Details)
CAMPSITE_PLACES = {
    'Buckhorn Wash', 'Mexican Mountain Road', 'San Rafael River Road',
    'The Wedge (San Rafael Swell)', 'Wedge Overlook',
    'Eva Conover Trail', 'Eagle Canyon Arch', 'Circa Loan Warrior petroglyph',
    'Behind the Reef Trail', 'Chute Canyon Vicinity', 'North Temple Mountain Wash',
    'Family Butte area', 'Tomsich Butte vicinity', 'Hidden Splendor', 'Block Mountain vicinity',
    'Red Canyon', 'McKay Flat Road',
}

# Route order from trip narrative (driving sequence). Skips omitted if no coords.
ROUTE_ORDER = [
    'Black Dragon Canyon', 'Black Dragon Canyon petroglyphs',
    'Buckhorn Draw Road', 'Buckhorn Wash', 'Buckhorn Wash petroglyphs',
    'Old San Rafael Swinging Bridge', 'San Rafael River',
    'Mexican Mountain Road', 'Fuller Bottom Road',
    'Wedge Overlook', 'Little Grand Canyon',
    'Dutch Flat Road', 'Dutch Flat', 'Coal Wash', 'Eva Conover Trail',
    'Eagle Canyon Overlook', 'Eagle Canyon Bridges', 'Eagle Canyon Trail', 'Eagle Canyon Arch',
    'Red Canyon', 'McKay Flat Road',
    'Behind the Reef Trail', 'Chute Canyon', 'Crack Canyon',
    'Temple Mountain Wash', 'Temple Wash Petroglyphs', 'North Temple Wash',
    'Temple Mountain Road', 'Head of Sinbad', "Sinbad's Head", 'Dutchman Arch',
]

# Markdown (include rows even if skipped)
md=[]
md.append('# San Rafael Swell places (extracted from Trip Details from Chuck.md)')
md.append('')
md.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
md.append('')
md.append('## Places')
md.append('')
def gmaps_url(lat, lon):
    if isinstance(lat, (int,float)) and isinstance(lon, (int,float)):
        return f"https://www.google.com/maps?q={lat:.6f},{lon:.6f}"
    return None

md.append('| Place | Latitude | Longitude | Google Maps | Source/Method | Notes |')
md.append('|---|---:|---:|---:|---|')
for r in rows_sorted:
    lat = f"{r['lat']:.6f}" if isinstance(r.get('lat'), (int,float)) else ''
    lon = f"{r['lon']:.6f}" if isinstance(r.get('lon'), (int,float)) else ''
    url = gmaps_url(r.get('lat'), r.get('lon'))
    link = f"[Map]({url})" if url else '-'
    method = r.get('method') or r.get('source') or ''
    notes = (r.get('notes') or '').replace('|','\\|')
    md.append(f"| {r['place']} | {lat} | {lon} | {link} | {method} | {notes} |")
pathlib.Path('SanRafaelSwell_Places.md').write_text('\n'.join(md)+'\n', encoding='utf-8')

# KML (skip rows without coords)
by_place = {r['place']: r for r in rows_sorted}
kml=[]
kml.append('<?xml version="1.0" encoding="UTF-8"?>')
kml.append('<kml xmlns="http://www.opengis.net/kml/2.2">')
kml.append('  <Document>')
kml.append('    <name>San Rafael Swell Places</name>')
kml.append('    <Style id="icon-default">')
kml.append('      <IconStyle><Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon></IconStyle>')
kml.append('    </Style>')
kml.append('    <Style id="icon-campground">')
kml.append('      <IconStyle><Icon><href>http://maps.google.com/mapfiles/kml/shapes/campground.png</href></Icon></IconStyle>')
kml.append('    </Style>')
for r in rows_sorted:
    if not isinstance(r.get('lat'), (int,float)) or not isinstance(r.get('lon'), (int,float)):
        continue
    name=html.escape(r['place'])
    lat=r['lat']; lon=r['lon']
    gurl=gmaps_url(lat, lon)
    desc_parts=[]
    if r.get('display_name'):
        desc_parts.append(f"OSM/Nominatim: {r['display_name']}")
    if r.get('method'):
        desc_parts.append(f"method: {r['method']}")
    if r.get('notes'):
        desc_parts.append(r['notes'])
    if gurl:
        desc_parts.append(f'<a href="{gurl}" target="_blank">View in Google Maps</a>')
    desc_inner='\n'.join(desc_parts)
    desc='<![CDATA[' + desc_inner.replace(']]>', ']]]]><![CDATA[>') + ']]>'
    style = '#icon-campground' if r['place'] in CAMPSITE_PLACES else '#icon-default'
    kml.append('    <Placemark>')
    kml.append(f'      <name>{name}</name>')
    kml.append(f'      <styleUrl>{style}</styleUrl>')
    if desc_inner:
        kml.append(f'      <description>{desc}</description>')
    kml.append('      <Point>')
    kml.append(f'        <coordinates>{lon:.6f},{lat:.6f},0</coordinates>')
    kml.append('      </Point>')
    kml.append('    </Placemark>')
kml.append('  </Document>')
kml.append('</kml>')
pathlib.Path('SanRafaelSwell_Places.kml').write_text('\n'.join(kml)+'\n', encoding='utf-8')

# HTML map (skip rows without coords)
pts=[]
for r in rows_sorted:
    if not isinstance(r.get('lat'), (int,float)) or not isinstance(r.get('lon'), (int,float)):
        continue
    url=gmaps_url(r['lat'], r['lon'])
    pts.append({'place':r['place'],'lat':r['lat'],'lon':r['lon'],'method':r.get('method'),'gmaps_url':url or '','campsite':r['place'] in CAMPSITE_PLACES})
# Route polyline for HTML map
route_latlngs = []
for pname in ROUTE_ORDER:
    r = by_place.get(pname)
    if not r or not isinstance(r.get('lat'), (int,float)) or not isinstance(r.get('lon'), (int,float)):
        continue
    route_latlngs.append([r['lat'], r['lon']])

# NOTE: this must NOT be an f-string because Leaflet uses `{s}/{z}/{x}/{y}` templates.
map_html='''<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>San Rafael Swell Places</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <style>
    html, body, #map { height: 100%; margin: 0; }
    .legend { position: absolute; bottom: 12px; left: 12px; background: white; padding: 10px 12px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,.15); font: 13px/1.3 system-ui, -apple-system, Segoe UI, Roboto, sans-serif; }
  </style>
</head>
<body>
  <div id="map"></div>
  <div class="legend">
    <div><strong>San Rafael Swell places</strong></div>
    <div>From <code>Trip Details from Chuck.md</code></div>
    <div>Blue line: approximate route from trip narrative. Campground icons in KML for recommended campsites.</div>
  </div>

  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    const map = L.map('map');
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    const points = __POINTS_JSON__;
    const routeLatlngs = __ROUTE_JSON__;
    const bounds = [];

    if (routeLatlngs.length > 1) {
      L.polyline(routeLatlngs, { color: '#0066cc', weight: 4, opacity: 0.7 }).addTo(map);
    }

    const campIcon = L.icon({
      iconUrl: 'http://maps.google.com/mapfiles/kml/shapes/campground.png',
      iconSize: [32, 32],
      iconAnchor: [16, 32],
    });
    for (const p of points) {
      const opts = p.campsite ? { icon: campIcon } : {};
      const m = L.marker([p.lat, p.lon], opts).addTo(map);
      const gmapsLink = p.gmaps_url ? `<br/><a href="${p.gmaps_url}" target="_blank">View in Google Maps</a>` : '';
      const popup = `<strong>${p.place}</strong><br/>${p.lat.toFixed(6)}, ${p.lon.toFixed(6)}${gmapsLink}<br/><em>${p.method || ''}</em>`;
      m.bindPopup(popup);
      bounds.push([p.lat, p.lon]);
    }

    if (bounds.length) {
      map.fitBounds(bounds, { padding: [30,30] });
    } else {
      map.setView([39.3, -111.7], 6);
    }
  </script>
</body>
</html>
'''
map_html = map_html.replace('__POINTS_JSON__', json.dumps(pts))
map_html = map_html.replace('__ROUTE_JSON__', json.dumps(route_latlngs))
pathlib.Path('SanRafaelSwell_Places_Map.html').write_text(map_html, encoding='utf-8')

print('regenerated SanRafaelSwell_Places.md / .kml / _Map.html')
print('mapped points:', len(pts), 'of', len(rows_sorted))
