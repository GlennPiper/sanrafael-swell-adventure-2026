"""Parse san-rafael-swell-adv-route-2025.gpx into structured JSON.

Outputs (under planning/):
  - route_waypoints.json : every <wpt> with name, lat, lon, ele, time, sym, desc
  - route_tracks.json    : every <trk> with name and decimated polyline (every Nth pt)
  - waypoint_sym_counts.json : histogram of <sym> tags
"""
from __future__ import annotations
import json
import pathlib
import re
import xml.etree.ElementTree as ET


BASE = pathlib.Path(__file__).resolve().parent.parent
SRC = BASE / 'san-rafael-swell-adv-route-2025.gpx'
OUT = BASE / 'planning'
OUT.mkdir(exist_ok=True)

NS = {'g': 'http://www.topografix.com/GPX/1/1'}


def _t(elem, tag):
    if elem is None:
        return None
    child = elem.find(f'g:{tag}', NS)
    return None if child is None else (child.text or '').strip()


def parse() -> dict:
    tree = ET.parse(SRC)
    root = tree.getroot()

    wpts = []
    for w in root.findall('g:wpt', NS):
        wpts.append({
            'name': _t(w, 'name'),
            'lat': float(w.get('lat')),
            'lon': float(w.get('lon')),
            'ele': float(_t(w, 'ele')) if _t(w, 'ele') else None,
            'time': _t(w, 'time'),
            'sym': _t(w, 'sym'),
            'desc': _t(w, 'desc'),
        })

    tracks = []
    for trk in root.findall('g:trk', NS):
        name = _t(trk, 'name')
        pts = []
        for seg in trk.findall('g:trkseg', NS):
            for p in seg.findall('g:trkpt', NS):
                pts.append([float(p.get('lat')), float(p.get('lon'))])
        tracks.append({'name': name, 'point_count': len(pts), 'points': pts})

    return {'waypoints': wpts, 'tracks': tracks}


def main() -> None:
    data = parse()
    wpts = data['waypoints']
    tracks = data['tracks']

    (OUT / 'route_waypoints.json').write_text(
        json.dumps(wpts, indent=2, ensure_ascii=False), encoding='utf-8'
    )

    # Write tracks with full points (we'll need them for HTML maps + per-day GPX)
    (OUT / 'route_tracks.json').write_text(
        json.dumps(tracks, indent=2), encoding='utf-8'
    )

    sym_counts: dict[str, int] = {}
    for w in wpts:
        sym_counts[w['sym'] or '(none)'] = sym_counts.get(w['sym'] or '(none)', 0) + 1
    (OUT / 'waypoint_sym_counts.json').write_text(
        json.dumps(dict(sorted(sym_counts.items(), key=lambda kv: -kv[1])), indent=2),
        encoding='utf-8',
    )

    # Summary print
    print(f'Waypoints: {len(wpts)}')
    print('Sym histogram:')
    for sym, n in sorted(sym_counts.items(), key=lambda kv: -kv[1]):
        print(f'  {sym:24s} {n}')
    print()
    print('Tracks:')
    for t in tracks:
        if not t['points']:
            print(f'  {t["name"]}: 0 pts')
            continue
        lats = [p[0] for p in t['points']]
        lons = [p[1] for p in t['points']]
        print(
            f'  {t["name"]}: {t["point_count"]} pts, '
            f'lat {min(lats):.4f}..{max(lats):.4f}, '
            f'lon {min(lons):.4f}..{max(lons):.4f}'
        )
        first = t['points'][0]
        last = t['points'][-1]
        print(f'    first: {first[0]:.5f},{first[1]:.5f}  last: {last[0]:.5f},{last[1]:.5f}')


if __name__ == '__main__':
    main()
