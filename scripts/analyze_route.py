"""Analyze the main route track and project every waypoint onto it.

Reads planning/route_waypoints.json + planning/route_tracks.json and writes
planning/route_analysis.json:
  - track summary (total miles, point count)
  - waypoints_ordered: each waypoint plus ``mile`` along the main track,
    ``track_index`` of the nearest track point, and ``dist_to_track_m``.

The ``mile`` value is what the day-splitting windows in build_trip_data.py key
off, so this must run after any change to the source GPX.
"""
from __future__ import annotations
import json
import math
import pathlib
import sys

_SCRIPTS = pathlib.Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import trip_config as cfg  # noqa: E402

BASE = _SCRIPTS.parent
PLAN = BASE / 'planning'

wpts = json.loads((PLAN / 'route_waypoints.json').read_text(encoding='utf-8'))
tracks = json.loads((PLAN / 'route_tracks.json').read_text(encoding='utf-8'))

main = next((t for t in tracks if t['name'] == cfg.MAIN_TRACK_NAME), None)
if main is None:
    raise SystemExit(
        f'Main track {cfg.MAIN_TRACK_NAME!r} not found in route_tracks.json. '
        f'Available: {[t["name"] for t in tracks]}'
    )
pts = main['points']


def hav_m(a, b):
    R = 6371000.0
    la1, lo1 = math.radians(a[0]), math.radians(a[1])
    la2, lo2 = math.radians(b[0]), math.radians(b[1])
    dlat = la2 - la1
    dlon = lo2 - lo1
    s = math.sin(dlat / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(s))


cum_m = [0.0]
for i in range(1, len(pts)):
    cum_m.append(cum_m[-1] + hav_m(pts[i - 1], pts[i]))
total_mi = cum_m[-1] / 1609.344
print(f'Main track ({main["name"]}): {len(pts)} points, total {total_mi:.1f} mi')

n = len(pts)
for frac in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
    i = min(int(frac * (n - 1)), n - 1)
    p = pts[i]
    print(f'  {int(frac * 100):3d}% (mi {cum_m[i] / 1609.344:6.2f}): {p[0]:.5f},{p[1]:.5f}')


def nearest(pt, pts_list, cum):
    best_i = 0
    best_d = float('inf')
    for i, tp in enumerate(pts_list):
        d = hav_m(pt, tp)
        if d < best_d:
            best_d = d
            best_i = i
    return best_i, best_d, cum[best_i] / 1609.344


enriched = []
for w in wpts:
    i, d_m, mi = nearest((w['lat'], w['lon']), pts, cum_m)
    enriched.append({**w, 'mile': round(mi, 3), 'track_index': i,
                     'dist_to_track_m': round(d_m, 1)})

enriched.sort(key=lambda x: x['mile'])

on_route = [e for e in enriched if e['dist_to_track_m'] <= 250]
near_route = [e for e in enriched if 250 < e['dist_to_track_m'] <= 1500]
far = [e for e in enriched if e['dist_to_track_m'] > 1500]
print(f'\nWaypoints on-track (<=250 m): {len(on_route)}')
print(f'Waypoints near-track (250-1500 m): {len(near_route)}')
print(f'Waypoints far-from-track (>1500 m): {len(far)}')

(PLAN / 'route_analysis.json').write_text(
    json.dumps(
        {
            'track_name': main['name'],
            'track_miles': round(total_mi, 2),
            'track_points': len(pts),
            'waypoints_ordered': enriched,
        },
        indent=2,
        ensure_ascii=False,
    ),
    encoding='utf-8',
)

print('\nOrdered waypoints along main track (mile | dist_m | sym | name):')
for e in enriched:
    flag = '  ' if e['dist_to_track_m'] <= 250 else ('~ ' if e['dist_to_track_m'] <= 1500 else '* ')
    print(f'  {e["mile"]:6.2f} | {e["dist_to_track_m"]:7.1f} | {flag}{(e["sym"] or ""):14s} | {e["name"]}')
