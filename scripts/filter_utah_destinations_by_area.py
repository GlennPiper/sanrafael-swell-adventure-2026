"""
Filter Utah destinations CSV by San Rafael Swell trip area (KML polygon).
Outputs places inside or very near the area to a markdown file.
"""
import csv
import json
import pathlib
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UA = 'SanRafaelSwellPlanner/1.0 (personal trip planning; Cursor script)'

# Manual coordinate overrides from research (lat, lon) - for places in/near San Rafael Swell
COORD_OVERRIDES = {
    'The Wedge': (39.093041, -110.758868),
    'San Rafael River Swinging Bridge': (39.081111, -110.667381),
    'Buckhorn Wash Pictograph Panel': (39.123586, -110.693775),
    'Little Wild Horse Canyon': (38.583, -110.803),
    'Little Wild Horse Canyon & Bell Canyon Trailhead': (38.583, -110.803),
    'Temple Mountain Townsite Campground': (38.667778, -110.685542),
    'Cleveland-Lloyd Dinosaur Quarry': (39.32282, -110.689509),
    'Museum of the San Rafael': (39.212718, -111.017429),
    'Moon Overlook Rd': (38.447014, -110.858294),
    'Furniture Draw': (39.16408, -110.72927),
    'Swing Arm City': (38.36567, -110.91498),
    'Moonshine Wash': (38.6847, -110.1701),
    'Little Grand Canyon': (39.083206, -110.783218),
    'Devil\'s Kitchen': (38.5737, -110.7071),
    'Bentonite Hills': (38.4695, -111.3636),
    'Clawson UFO Landing Site': (38.923, -110.851),  # Clawson, Emery County
}


def parse_kml_polygon(kml_path):
    """Parse KML and extract polygon coordinates (lon, lat)."""
    tree = ET.parse(kml_path)
    root = tree.getroot()
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    coords_el = root.find('.//kml:coordinates', ns)
    if coords_el is None:
        coords_el = root.find('.//coordinates')
    if coords_el is None or not coords_el.text:
        raise ValueError("No coordinates found in KML")
    points = []
    for part in coords_el.text.strip().split():
        vals = part.split(',')
        if len(vals) >= 2:
            lon, lat = float(vals[0]), float(vals[1])
            points.append((lon, lat))
    return points


def point_in_polygon(px, py, polygon):
    """Ray casting algorithm for point-in-polygon test."""
    n = len(polygon)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def dist_to_polygon(px, py, polygon):
    """Approximate min distance from point to polygon (min dist to any vertex or edge)."""
    min_d = float('inf')
    n = len(polygon)
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]
        d = ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
        min_d = min(min_d, d)
        denom = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        if denom > 1e-10:
            t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / (denom ** 2)))
            proj_x = x1 + t * (x2 - x1)
            proj_y = y1 + t * (y2 - y1)
            d = ((px - proj_x) ** 2 + (py - proj_y) ** 2) ** 0.5
            min_d = min(min_d, d)
    return min_d


def extract_coords_from_url(url):
    """Extract lat,lon from Google Maps search URL if present."""
    if not url:
        return None
    # Match: /search/37.27222,-109.51734 or .../search/37.1415815,-113.1311814
    m = re.search(r'/search/([+-]?\d+\.?\d*),([+-]?\d+\.?\d*)', url)
    if m:
        try:
            lat, lon = float(m.group(1)), float(m.group(2))
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return (lat, lon)
        except ValueError:
            pass
    return None


def nominatim_geocode(name, note=None):
    """Geocode using Nominatim. Returns (lat, lon) or None."""
    base = 'https://nominatim.openstreetmap.org/search'
    for q in [
        f"{name}, San Rafael Swell, Utah",
        f"{name}, Emery County, Utah",
        f"{name}, Utah",
    ]:
        params = {'q': q, 'format': 'json', 'limit': 1}
        url = base + '?' + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            if data:
                return (float(data[0]['lat']), float(data[0]['lon']))
        except Exception:
            pass
        time.sleep(1.1)
    return None


def load_utah_destinations_csv(csv_path):
    """Load Utah destinations from CSV. Returns list of dicts with title, note, url, comment."""
    rows = []
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = (row.get('Title') or '').strip()
            url = (row.get('URL') or '').strip()
            if not title and not url:
                continue
            note = (row.get('Note') or '').strip()
            comment = (row.get('Comment') or '').strip()
            tags = (row.get('Tags') or '').strip()
            # Combine note and comment for output
            combined_note = ' | '.join(s for s in [note, comment] if s)
            rows.append({
                'title': title or '(Unnamed)',
                'note': combined_note,
                'url': url,
                'tags': tags,
            })
    return rows


def main():
    base = pathlib.Path(__file__).resolve().parent.parent
    kml_path = base / 'san-rafael-swell-trip-area.kml'
    csv_path = base / 'Takeout' / 'Saved' / 'Utah destinations.csv'
    out_path = base / 'Utah_Destinations_In_San_Rafael_Area.md'

    polygon = parse_kml_polygon(kml_path)
    destinations = load_utah_destinations_csv(csv_path)

    NEAR_THRESHOLD = 0.25  # degrees (~15-20 mi) for "very near"
    matches = []
    needs_geocode = []

    for d in destinations:
        lat, lon = None, None

        # 1. Check manual overrides
        if d['title'] in COORD_OVERRIDES:
            lat, lon = COORD_OVERRIDES[d['title']]

        # 2. Extract from URL if present
        if lat is None and d.get('url'):
            coords = extract_coords_from_url(d['url'])
            if coords:
                lat, lon = coords

        # 3. Queue for Nominatim if still missing
        if lat is None:
            needs_geocode.append(d)
            continue

        inside = point_in_polygon(lon, lat, polygon)
        dist = dist_to_polygon(lon, lat, polygon) if not inside else 0
        near = dist <= NEAR_THRESHOLD
        if inside or near:
            matches.append({
                **d,
                'lat': lat,
                'lon': lon,
                'in_area': inside,
                'distance_deg': round(dist, 4) if not inside else 0,
            })

    # Geocode remaining (Nominatim rate limit ~1 req/sec; ~2 min per 100 places)
    if needs_geocode:
        print(f"Geocoding {len(needs_geocode)} places (each takes ~1-3 sec)...", flush=True)
        for i, d in enumerate(needs_geocode):
            print(f"  [{i+1}/{len(needs_geocode)}] {d['title'][:50]}...", end=" ", flush=True)
            result = nominatim_geocode(d['title'])
            lat, lon = (result if result else (None, None))
            if lat is not None:
                inside = point_in_polygon(lon, lat, polygon)
                dist = dist_to_polygon(lon, lat, polygon) if not inside else 0
                near = dist <= NEAR_THRESHOLD
                if inside or near:
                    matches.append({
                        **d,
                        'lat': lat,
                        'lon': lon,
                        'in_area': inside,
                        'distance_deg': round(dist, 4) if not inside else 0,
                    })
                    print("match!", flush=True)
                else:
                    print("outside", flush=True)
            else:
                print("no result", flush=True)

    matches.sort(key=lambda x: x['title'].lower())

    lines = [
        '# Utah Destinations in San Rafael Swell Trip Area',
        '',
        'Places from your Utah Destinations list that fall **inside** or **very near** the San Rafael Swell trip area (defined in `san-rafael-swell-trip-area.kml`).',
        '',
        f'**Total matches: {len(matches)}**',
        '',
        'The area covers approximately:',
        '- **Longitude:** -111.18° to -110.12° (east-central Utah)',
        '- **Latitude:** 38.48° to 39.33°',
        '',
        '---',
        '',
    ]

    for m in matches:
        loc_note = ' *(inside area)*' if m['in_area'] else f" *(≈{m['distance_deg']:.2f}° from boundary)*"
        lines.append(f"## {m['title']}{loc_note}")
        lines.append('')
        lines.append(f"- **GPS:** {m['lat']:.6f}, {m['lon']:.6f}")
        if m.get('url'):
            lines.append(f"- **Google Maps:** {m['url']}")
        if m.get('note'):
            lines.append(f"- **Note/Comment:** {m['note']}")
        lines.append('')
        lines.append('---')
        lines.append('')

    out_path.write_text('\n'.join(lines), encoding='utf-8')
    print(f"\nFound {len(matches)} Utah destinations in or near the San Rafael Swell trip area.")
    print(f"Saved to: {out_path}")
    for m in matches:
        print(f"  - {m['title']}")


if __name__ == '__main__':
    main()
