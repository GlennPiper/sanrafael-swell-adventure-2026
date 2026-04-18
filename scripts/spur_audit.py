"""Detect out-and-back "spurs" in the GPX track and report how much driving
would be saved if each POI were skipped.

Algorithm
---------
For each primary / hike-candidate POI:
  1. Project the POI to the nearest track point (its "anchor" index and mile).
  2. Walk the track outward in both directions from the anchor, looking for the
     first pair of indices (i_in, i_out) with i_in < anchor < i_out whose
     geographic positions are within SPUR_PINCH_M metres of each other.
     That's the "mouth" of the spur.
  3. Spur_mi = track distance from i_in to i_out (one continuous run).
  4. If no such pair is found within SEARCH_MI of the anchor, we declare the
     POI "not a spur" (spur_mi = 0).

This is a simple heuristic -- good for the classic out-and-back case. It can
mis-detect on loops or braided tracks, which is why we only trust it for POIs
that are already known to be on spurs.
"""
import json, math, pathlib

BASE = pathlib.Path(__file__).resolve().parent.parent
TRIP = json.loads((BASE / 'planning' / 'trip_data.json').read_text(encoding='utf-8'))
TRACKS = json.loads((BASE / 'planning' / 'route_tracks.json').read_text(encoding='utf-8'))

SPUR_PINCH_M = 60.0    # two track points within 60 m -> same geographic spot
SEARCH_MI    = 25.0    # don't walk more than 25 mi from the anchor looking

_R = 6371000.0

def _hv_m(a, b):
    la1, lo1 = math.radians(a[0]), math.radians(a[1])
    la2, lo2 = math.radians(b[0]), math.radians(b[1])
    d = math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
    return 2 * _R * math.asin(math.sqrt(d))

# Load the unified main track (same one analyze_route.py uses for POI miles)
main = next(t for t in TRACKS if t['name'] == 'San Rafael Swell Adventure Route')
pts = main['points']

cum_mi = [0.0]
for i in range(1, len(pts)):
    cum_mi.append(cum_mi[-1] + _hv_m(pts[i-1], pts[i]) / 1609.344)

print(f"Loaded track: {len(pts)} points, {cum_mi[-1]:.1f} total miles")
print()

def nearest_index_by_mile(target_mi):
    """Find the track index whose cumulative mile is closest to target_mi."""
    # binary-ish search via linear scan (cheap enough)
    best_i, best_d = 0, abs(cum_mi[0] - target_mi)
    for i, m in enumerate(cum_mi):
        d = abs(m - target_mi)
        if d < best_d:
            best_d, best_i = d, i
    return best_i

def detect_spur(anchor_idx):
    """
    Scan outward from anchor_idx. Find the *widest* pair (i_in, i_out) with
    i_in < anchor < i_out and track points within SPUR_PINCH_M of each other,
    provided the scan stays within SEARCH_MI of the anchor.
    Returns (i_in, i_out, spur_mi) or (None, None, 0.0).
    """
    anchor_mi = cum_mi[anchor_idx]
    # Indices that are within SEARCH_MI on each side
    lo, hi = anchor_idx, anchor_idx
    while lo > 0 and anchor_mi - cum_mi[lo-1] < SEARCH_MI:
        lo -= 1
    while hi < len(pts)-1 and cum_mi[hi+1] - anchor_mi < SEARCH_MI:
        hi += 1

    # Look for the largest-span pinch pair
    best = (None, None, 0.0)
    # Sparse scan: step through candidates to keep this O(window^2 / step^2)
    step = 3
    for i in range(lo, anchor_idx, step):
        for j in range(hi, anchor_idx, -step):
            if j <= i:
                break
            if _hv_m(pts[i], pts[j]) <= SPUR_PINCH_M:
                span = cum_mi[j] - cum_mi[i]
                if span > best[2]:
                    best = (i, j, span)
                break  # any j farther out for this i will be smaller span? not
                       # quite true but this keeps the scan tight; we break
                       # because we want the farthest j that pinches (we're
                       # iterating j from far to near, so the FIRST pinch is
                       # the farthest).
    return best

# --- Audit ---
pois_of_interest = []
for d in TRIP['days']:
    for p in (d.get('pois') or []):
        if p.get('status') not in ('primary', 'hike_candidate', 'conditional'):
            continue
        pois_of_interest.append((d['id'], p))

print(f"Auditing {len(pois_of_interest)} primary/hike/conditional POIs for spurs...\n")
print(f"{'Day':<13} {'Mile':>7}  {'Off':>5}  {'Spur':>6}  {'Status':<14} POI")
print("-" * 100)
rows = []
for day_id, p in pois_of_interest:
    mile = p.get('mile')
    if mile is None:
        continue
    anchor = nearest_index_by_mile(mile)
    i_in, i_out, spur_mi = detect_spur(anchor)
    off_m = p.get('dist_to_track_m') or 0
    rows.append((day_id, mile, off_m, spur_mi, p['status'], p['name'], i_in, i_out))

# Print, sorted by day then mile
rows.sort(key=lambda r: (r[0], r[1]))
for day_id, mile, off_m, spur_mi, status, name, i_in, i_out in rows:
    marker = ' *' if spur_mi >= 2.0 else ''
    print(f"{day_id:<13} {mile:>7.1f}  {off_m:>4.0f}m  {spur_mi:>5.1f}mi  {status:<14} {name}{marker}")

print()
print("POIs with spur >= 2.0 mi are flagged with *")
print()

# Zoom in on the two POIs the user called out
print("=" * 72)
print("User-flagged POIs")
print("=" * 72)
targets = [
    ('DP - Red Canyon', 'day1_swell'),
    ('DP - Hidden Splendor Overlook', 'day3_swell'),
    ('DP - Reds Canyon', 'day2_swell'),             # cross-check: same name, Day 2
    ('Lucky Strike Mine', 'day2_swell'),            # potential same-spur neighbor of Reds
]
for name, day_id in targets:
    for d, p in pois_of_interest:
        if d == day_id and p['name'] == name:
            mile = p.get('mile')
            anchor = nearest_index_by_mile(mile)
            i_in, i_out, spur_mi = detect_spur(anchor)
            if i_in is not None:
                print(f"\n{name} (Day {day_id}, mile {mile:.2f})")
                print(f"  Anchor idx = {anchor}")
                print(f"  Spur mouth = idx {i_in} .. idx {i_out}")
                print(f"  Mouth mile = {cum_mi[i_in]:.2f} .. {cum_mi[i_out]:.2f}")
                print(f"  Spur length (in->apex->out) = {spur_mi:.2f} mi")
                print(f"  Savings if skipped @ 20 mph = {spur_mi / 20 * 60:.0f} min")
                print(f"  Mouth close-pair: {_hv_m(pts[i_in], pts[i_out]):.0f} m apart")
            else:
                print(f"\n{name}: no spur detected within {SEARCH_MI} mi.")
            break
