"""
Filter Google Takeout places by San Rafael Swell trip area.
Outputs places inside or very near the area to a markdown file.
"""
import json
import pathlib
import xml.etree.ElementTree as ET


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
    # Format: "lon,lat,alt lon,lat,alt ..."
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
        # Distance to vertex
        d = ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
        min_d = min(min_d, d)
        # Distance to edge (line segment)
        denom = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        if denom > 1e-10:
            t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / (denom ** 2)))
            proj_x = x1 + t * (x2 - x1)
            proj_y = y1 + t * (y2 - y1)
            d = ((px - proj_x) ** 2 + (py - proj_y) ** 2) ** 0.5
            min_d = min(min_d, d)
    return min_d


def load_places_from_takeout(base_dir):
    """Load all places from Takeout JSON files with coords, name, description."""
    base = pathlib.Path(base_dir)
    paths = [
        base / 'Takeout' / 'Maps' / 'My labeled places' / 'Labeled places.json',
        base / 'Takeout' / 'Maps (your places)' / 'Saved Places.json',
        base / 'Takeout' / 'Maps (your places)' / 'Reviews.json',
    ]
    places = []
    for fp in paths:
        if not fp.exists():
            continue
        data = json.loads(fp.read_text(encoding='utf-8'))
        feats = data.get('features', [])
        for f in feats:
            props = f.get('properties', {})
            coords = f.get('geometry', {}).get('coordinates')
            if not coords or len(coords) < 2 or (coords[0] == 0 and coords[1] == 0):
                continue
            lon, lat = float(coords[0]), float(coords[1])

            loc = props.get('location', {}) if 'location' in props else props
            name = loc.get('name') or props.get('name') or props.get('address')
            if not name:
                continue

            desc_parts = []
            if props.get('review_text_published'):
                desc_parts.append(props['review_text_published'])
            if props.get('Comment') and 'No location' not in str(props.get('Comment', '')):
                desc_parts.append(props['Comment'])
            if props.get('address') and loc != props:
                addr = props.get('address') or loc.get('address')
                if addr:
                    desc_parts.append(f"Address: {addr}")
            desc = ' | '.join(desc_parts) if desc_parts else None

            places.append({
                'name': name,
                'lat': lat,
                'lon': lon,
                'description': desc,
                'source_file': fp.name,
            })
    return places


def main():
    base = pathlib.Path(__file__).resolve().parent.parent
    kml_path = base / 'san-rafael-swell-trip-area.kml'
    out_path = base / 'Takeout_Places_In_San_Rafael_Area.md'

    polygon = parse_kml_polygon(kml_path)
    places = load_places_from_takeout(base)

    # Filter: inside polygon or within ~0.25 deg (~15-20 mi) of polygon
    NEAR_THRESHOLD = 0.25
    matches = []
    for p in places:
        inside = point_in_polygon(p['lon'], p['lat'], polygon)
        dist = dist_to_polygon(p['lon'], p['lat'], polygon) if not inside else 0
        near = dist <= NEAR_THRESHOLD
        if inside or near:
            matches.append({
                **p,
                'in_area': inside,
                'distance_deg': round(dist, 4) if not inside else 0,
            })

    # Sort by name
    matches.sort(key=lambda x: x['name'].lower())

    lines = [
        '# Google Takeout Places in San Rafael Swell Trip Area',
        '',
        f'Places from Google Takeout data that fall **inside** or **very near** the San Rafael Swell trip area.',
        '',
        f'Total matches: {len(matches)}',
        '',
        '---',
        '',
    ]

    for m in matches:
        loc_note = ' (inside area)' if m['in_area'] else f" (≈{m['distance_deg']:.2f}° from boundary)"
        lines.append(f"## {m['name']}{loc_note}")
        lines.append('')
        lines.append(f"- **GPS:** {m['lat']:.6f}, {m['lon']:.6f}")
        if m.get('description'):
            lines.append(f"- **Description/Note:** {m['description']}")
        lines.append('')
        lines.append('---')
        lines.append('')

    out_path.write_text('\n'.join(lines), encoding='utf-8')
    print(f"Found {len(matches)} places in or near the San Rafael Swell trip area.")
    print(f"Saved to: {out_path}")
    for m in matches:
        print(f"  - {m['name']}")


if __name__ == '__main__':
    main()
