"""Parse the source route GPX into structured JSON.

Reads the GPX named by ``trip_config.ROUTE_GPX_FILENAME``.

Outputs (under planning/):
  - route_waypoints.json     : every <wpt> with name, lat, lon, ele, time, sym, desc
  - route_tracks.json        : every <trk> with name and full polyline
  - waypoint_sym_counts.json : histogram of <sym> tags
"""
from __future__ import annotations
import json
import pathlib
import sys
import xml.etree.ElementTree as ET

_SCRIPTS = pathlib.Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import trip_config as cfg  # noqa: E402

BASE = _SCRIPTS.parent
SRC = BASE / cfg.ROUTE_GPX_FILENAME
OUT = BASE / 'planning'
OUT.mkdir(exist_ok=True)

# GPX 1.0 and 1.1 differ only by namespace URI; detect from the root tag so we
# don't have to care which one the source export used.
GPX_NAMESPACES = (
    'http://www.topografix.com/GPX/1/1',
    'http://www.topografix.com/GPX/1/0',
)


def _namespace(root: ET.Element) -> dict[str, str]:
    if root.tag.startswith('{'):
        return {'g': root.tag[1:].split('}')[0]}
    return {'g': GPX_NAMESPACES[0]}


def _t(elem, tag, ns):
    if elem is None:
        return None
    child = elem.find(f'g:{tag}', ns)
    return None if child is None else (child.text or '').strip()


def parse() -> dict:
    if not SRC.exists():
        raise SystemExit(
            f'Source route GPX not found: {SRC}\n'
            f'Set trip_config.ROUTE_GPX_FILENAME to the correct filename.'
        )
    root = ET.parse(SRC).getroot()
    ns = _namespace(root)

    wpts = []
    for w in root.findall('g:wpt', ns):
        wpts.append({
            'name': _t(w, 'name', ns),
            'lat': float(w.get('lat')),
            'lon': float(w.get('lon')),
            'ele': float(_t(w, 'ele', ns)) if _t(w, 'ele', ns) else None,
            'time': _t(w, 'time', ns),
            'sym': _t(w, 'sym', ns),
            'desc': _t(w, 'desc', ns),
        })

    tracks = []
    for trk in root.findall('g:trk', ns):
        name = _t(trk, 'name', ns)
        pts = []
        for seg in trk.findall('g:trkseg', ns):
            for p in seg.findall('g:trkpt', ns):
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

    print(f'Source: {SRC.name}')
    print(f'Waypoints: {len(wpts)}')
    print('Sym histogram:')
    for sym, n in sorted(sym_counts.items(), key=lambda kv: -kv[1]):
        print(f'  {sym:24s} {n}')
    print()
    print('Tracks:')
    names = [t['name'] for t in tracks]
    for t in tracks:
        tag = ''
        if t['name'] == cfg.MAIN_TRACK_NAME:
            tag = '  <-- MAIN'
        elif t['name'] in cfg.IGNORED_TRACK_NAMES:
            tag = '  (ignored per trip_config)'
        if not t['points']:
            print(f'  {t["name"]}: 0 pts{tag}')
            continue
        lats = [p[0] for p in t['points']]
        lons = [p[1] for p in t['points']]
        print(
            f'  {t["name"]}: {t["point_count"]} pts, '
            f'lat {min(lats):.4f}..{max(lats):.4f}, '
            f'lon {min(lons):.4f}..{max(lons):.4f}{tag}'
        )
        print(f'    first: {t["points"][0][0]:.5f},{t["points"][0][1]:.5f}  '
              f'last: {t["points"][-1][0]:.5f},{t["points"][-1][1]:.5f}')

    if cfg.MAIN_TRACK_NAME not in names:
        raise SystemExit(
            f'\nERROR: trip_config.MAIN_TRACK_NAME = {cfg.MAIN_TRACK_NAME!r} '
            f'is not one of the track names in {SRC.name}: {names}'
        )


if __name__ == '__main__':
    main()
