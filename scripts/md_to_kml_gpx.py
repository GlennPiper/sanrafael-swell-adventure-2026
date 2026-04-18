"""
Generate KML and GPX from Utah_Destinations_In_San_Rafael_Area.md
"""
import html
import pathlib
import re


def parse_md_places(md_path):
    """Parse the MD file and yield (name, lat, lon, gmaps_url, note) for each place."""
    text = md_path.read_text(encoding='utf-8')
    blocks = text.split('\n---\n')
    for block in blocks:
        block = block.strip()
        if not block or block.startswith('# Utah Destinations'):
            continue
        # Parse ## Name *(suffix)*
        name_match = re.search(r'^##\s+(.+?)(?:\s+_\*[^)]+\*_)?\s*$', block, re.MULTILINE)
        gps_match = re.search(r'-\s*\*\*GPS:\*\*\s*([\d.-]+),\s*([\d.-]+)', block)
        gmaps_match = re.search(r'-\s*\*\*Google Maps:\*\*\s*(https://\S+)', block)
        note_match = re.search(r'-\s*\*\*Note/Comment:\*\*\s*(.+?)(?=\n\n|\n---|\Z)', block, re.DOTALL)
        if not name_match or not gps_match:
            continue
        name = name_match.group(1).strip()
        lat = float(gps_match.group(1))
        lon = float(gps_match.group(2))
        gmaps_url = gmaps_match.group(1).strip() if gmaps_match else None
        note = note_match.group(1).strip() if note_match else ''
        note = ' '.join(note.split())  # collapse whitespace
        yield name, lat, lon, gmaps_url, note


def build_kml(places):
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        '  <Document>',
        '    <name>Utah Destinations in San Rafael Swell</name>',
        '    <description>Places from Utah Destinations list that fall inside or very near the San Rafael Swell trip area</description>',
        '    <Style id="icon-default">',
        '      <IconStyle><Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon></IconStyle>',
        '    </Style>',
    ]
    for name, lat, lon, gmaps_url, note in places:
        desc_parts = []
        if gmaps_url:
            desc_parts.append(f'<a href="{html.escape(gmaps_url)}" target="_blank">View in Google Maps</a>')
        if note:
            desc_parts.append(html.escape(note))
        desc = '<br/>'.join(desc_parts) if desc_parts else ''
        lines.append('    <Placemark>')
        lines.append(f'      <name>{html.escape(name)}</name>')
        lines.append('      <styleUrl>#icon-default</styleUrl>')
        if desc:
            lines.append(f'      <description><![CDATA[{desc}]]></description>')
        lines.append(f'      <Point><coordinates>{lon},{lat},0</coordinates></Point>')
        lines.append('    </Placemark>')
    lines.append('  </Document>')
    lines.append('</kml>')
    return '\n'.join(lines)


def build_gpx(places):
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1" creator="md_to_kml_gpx.py">',
        '  <metadata>',
        '    <name>Utah Destinations in San Rafael Swell</name>',
        '    <desc>Places from Utah Destinations list that fall inside or very near the San Rafael Swell trip area</desc>',
        '  </metadata>',
    ]
    for name, lat, lon, gmaps_url, note in places:
        desc = note
        if gmaps_url:
            desc = (desc + ' | ' if desc else '') + gmaps_url
        lines.append('  <wpt lat="' + str(lat) + '" lon="' + str(lon) + '">')
        lines.append('    <name>' + html.escape(name) + '</name>')
        if desc:
            lines.append('    <desc>' + html.escape(desc) + '</desc>')
        lines.append('  </wpt>')
    lines.append('</gpx>')
    return '\n'.join(lines)


def main():
    base = pathlib.Path(__file__).resolve().parent.parent
    md_path = base / 'Utah_Destinations_In_San_Rafael_Area.md'
    kml_path = base / 'Utah_Destinations_San_Rafael.kml'
    gpx_path = base / 'Utah_Destinations_San_Rafael.gpx'

    places = list(parse_md_places(md_path))
    print(f"Parsed {len(places)} places from {md_path.name}")

    kml_path.write_text(build_kml(places), encoding='utf-8')
    print(f"Wrote {kml_path}")

    gpx_path.write_text(build_gpx(places), encoding='utf-8')
    print(f"Wrote {gpx_path}")


if __name__ == '__main__':
    main()
