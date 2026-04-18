"""Analyze the main SRS Adventure track: cumulative distance, bounding, and
project every waypoint to its nearest point on the track.

Outputs planning/route_analysis.json:
  - track summary (first/last/bbox/total miles)
  - waypoints_on_track: each waypoint with mile, distance-from-track (m),
    nearest track index, plus source metadata (sym, desc, name).
"""
from __future__ import annotations
import json
import math
import pathlib

BASE = pathlib.Path(__file__).resolve().parent.parent
PLAN = BASE / 'planning'

wpts = json.loads((PLAN / 'route_waypoints.json').read_text(encoding='utf-8'))
tracks = json.loads((PLAN / 'route_tracks.json').read_text(encoding='utf-8'))

main = next(t for t in tracks if t['name'] == 'San Rafael Swell Adventure Route')
pts = main['points']


def hav_m(a, b):
    R = 6371000.0
    la1, lo1 = math.radians(a[0]), math.radians(a[1])
    la2, lo2 = math.radians(b[0]), math.radians(b[1])
    dlat = la2 - la1
    dlon = lo2 - lo1
    s = math.sin(dlat / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(s))


# Cumulative miles along the track
cum_m = [0.0]
for i in range(1, len(pts)):
    cum_m.append(cum_m[-1] + hav_m(pts[i - 1], pts[i]))
total_mi = cum_m[-1] / 1609.344
print(f'Main track: {len(pts)} points, total {total_mi:.1f} mi')

# Coarse bbox windows (every 10% of the track) to show geographic flow
n = len(pts)
for frac in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
    i = min(int(frac * (n - 1)), n - 1)
    p = pts[i]
    print(f'  {int(frac * 100):3d}% (mi {cum_m[i] / 1609.344:6.2f}): {p[0]:.5f},{p[1]:.5f}')


# Project every waypoint to nearest track point (linear scan; ~133 x 11881 = ~1.6M, fine)
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
    enriched.append({**w, 'mile': round(mi, 3), 'track_index': i, 'dist_to_track_m': round(d_m, 1)})

# Sort by mile along route (ascending). Off-route waypoints (>1000 m) still included but flagged.
enriched.sort(key=lambda x: x['mile'])

# How many are "on-route" (<=250 m)?
on_route = [e for e in enriched if e['dist_to_track_m'] <= 250]
near_route = [e for e in enriched if 250 < e['dist_to_track_m'] <= 1500]
far = [e for e in enriched if e['dist_to_track_m'] > 1500]
print(f'\nWaypoints on-track (<=250 m): {len(on_route)}')
print(f'Waypoints near-track (250-1500 m): {len(near_route)}')
print(f'Waypoints far-from-track (>1500 m): {len(far)}')

(PLAN / 'route_analysis.json').write_text(
    json.dumps(
        {
            'track_miles': round(total_mi, 2),
            'track_points': len(pts),
            'waypoints_ordered': enriched,
        },
        indent=2,
        ensure_ascii=False,
    ),
    encoding='utf-8',
)

# Print ordered list (short) for human review
print('\nOrdered waypoints along main track (mile | dist_m | sym | name):')
for e in enriched:
    flag = '  ' if e['dist_to_track_m'] <= 250 else ('~ ' if e['dist_to_track_m'] <= 1500 else '* ')
    print(f'  {e["mile"]:6.2f} | {e["dist_to_track_m"]:7.1f} | {flag}{(e["sym"] or ""):14s} | {e["name"]}')
