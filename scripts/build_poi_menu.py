"""Build a POI triage menu grouped by proposed day splits.

Day splits chosen for collaborative review:
  Day 1: mi 0   - 68   (Black Dragon -> Wedge Overlook)
  Day 2: mi 68  - 140  (Wedge -> Tomsich Butte / Reds Canyon)
  Day 3: mi 140 - 200  (Tomsich -> Temple Mtn area)
  Day 4 (May 6 AM): mi 200 - 225 (Temple Mtn -> Sinbad/Dutchman, then split)

Outputs planning/poi_menu.md.
"""
from __future__ import annotations
import json
import pathlib
import textwrap

BASE = pathlib.Path(__file__).resolve().parent.parent
PLAN = BASE / 'planning'
analysis = json.loads((PLAN / 'route_analysis.json').read_text(encoding='utf-8'))

wpts = analysis['waypoints_ordered']

DAYS = [
    ('Day 1 (May 3)', 0.0, 68.0, 'Black Dragon Canyon -> Wedge Overlook'),
    ('Day 2 (May 4)', 68.0, 140.0, 'Wedge Overlook -> Tomsich Butte / Reds Canyon'),
    ('Day 3 (May 5)', 140.0, 200.0, 'Tomsich Butte -> Temple Mountain area'),
    ('Day 4 AM (May 6)', 200.0, 226.0, 'Temple Mountain -> Head of Sinbad / Dutchman Arch (then split)'),
]

# Classify waypoints into "POIs" (worth considering as stops) vs campsites vs logistics.
# Everything starting "DP -" is a Discovery Point from the trip narrative. We also keep
# notable named attractions even without DP prefix.
POI_KEEP_SYMS = {'petroglyph', 'stone', 'cliff', 'attraction', 'mine', 'cave', 'bridge',
                 'water', 'binoculars', 'off-road', 'building-24', 'natural-spring', 'city-24', 'known-route'}

# Time estimates by sym (rough; can be tuned)
TIME_EST = {
    'petroglyph':       '20-40 min (short walk, respect the panel)',
    'bridge':           '5-10 min (photo stop)',
    'water':            '5-15 min (river/drainage)',
    'binoculars':       '15-30 min (overlook stop)',
    'cliff':            '15-60 min (canyon feature)',
    'stone':            '15-60 min (arch/formation; some require a walk)',
    'cave':             '15-30 min (short walk)',
    'attraction':       '15-45 min (general point of interest)',
    'mine':             '20-45 min (explore carefully)',
    'building-24':      '15-30 min (old structure)',
    'natural-spring':   '10-20 min',
    'off-road':         'ongoing (trail-head / trail section)',
    'known-route':      'ongoing (trail-head / route marker)',
    'city-24':          'logistics stop',
    'fuel-24':          'logistics: fuel',
    'toilets-24':       'logistics: toilets',
}

TIME_OVERRIDE = {
    'DP - Black Dragon Canyon':            '30-60 min (drive through; stops for petroglyphs)',
    'DP - Black Dragon Petroglyph':        '20-40 min (short walk to the panel)',
    'DP - Buckhorn Wash Petroglyphs':      '30-45 min (famous 130-ft panel; BLM restoration)',
    'DP - Old San Rafael Swinging Bridge': '10-20 min (drive-by + photo)',
    'DP - Dinosaur Footprint':             '10-20 min (interpretive stop)',
    'DP - Wedge Overlook':                 '30-60 min (Little Grand Canyon overlook)',
    'DP - Little Grand Canyon':            'same as Wedge Overlook (combined)',
    'DP - Eagle Canyon Overlook':          '15-30 min (overlook)',
    'DP - Eagle Canyon Bridges':           '15-30 min (I-70 bridges view from below)',
    'DP - Eagle Canyon Trail':             'ongoing (route-segment, rocks, full-size caution)',
    'DP - Eagle Canyon Arch':              '30-60 min (short walk)',
    'DP - The Icebox':                     '20-40 min (short walk into cool grotto)',
    "DP - Swasey's Cabin":                 '15-30 min (historic cabin)',
    'DP - Loan Warrior Petroglyph':        '20-40 min (short hike)',
    'DP - Tomsich Butte Uranium Mine':     '30-60 min (mine ruins + equipment)',
    'DP - Hondu Arch':                     '20-40 min (view from viewpoint; inside Muddy Creek Wilderness)',
    'DP - Hidden Splendor Overlook':       '20-30 min (overlook)',
    'DP - Behind the Reef trail':          'ongoing (slow technical section; hours on trail)',
    'DP - Chute Canyon':                   '~2.5 hours typical partial hike (tactical default; full canyon longer)',
    'DP - Crack Canyon':                   '~3.5 hours typical ~5 mi RT + obstacle (tactical default)',
    'DP - Wild Horse Window Arch':         '3-5 hours (2.8 mi hike to the window/bridge)',
    'DP - Temple Wash Petroglpyhs':        '20-30 min (roadside)',
    'DP - North Temple Wash':              'drive-through (scenic narrows)',
    'DP - Head of Sinbad Petroglyph':      '30-45 min (short walk; BLM gates/fence)',
    'DP - Dutchman Arch':                  '15-30 min (short walk)',
    'DP - The Sinkhole':                   '20-30 min (overlook the collapse)',
    'DP - Red Canyon':                     '15-30 min (scenic stop)',
    'DP - Split Rock':                     '5-10 min (drive-by photo)',
    'DP - Buckhorn Wash':                  'ongoing (the canyon drive itself)',
    'DP - Petroglyph Canyon Panel':        '30-45 min (if visited - it is off-route to the east near mile 0)',
    'DP - Spirit Arch':                    '20-40 min (if visited - off-route near mile 0)',
    'DP - Eva Conover Trail':              'ongoing (blue trail, rocks, views)',
    'DP - Reds Canyon':                    'ongoing (graded dirt; scenic, many campsites)',
    'DP - Miner\u2019s Cabin':             '15-30 min (historic structure)',
    "DP - Miner's Cabin":                  '15-30 min (historic structure)',
    'DP - San Rafael River':               '10-15 min (river, possible crossing)',
    'Hamburger Rocks':                     '15-30 min (rock formations)',
    'Goblin Valley State Park':            '1-3 hours if visited (entry fee; side trip off route)',
    'Little Wild Horse Slot Canyon':       '3-6 hours if hiked (popular slot canyon)',
    'Little Wild Horse Canyon Trail':      'trail-head marker',
    'Chute Canyon Trailhead':              'trail-head marker',
    'Crack Canyon Trailhead':              'trail-head marker',
    'Wild Horse Window Trailhead':         'trail-head marker',
    'Coal Wash':                           '15-20 min (wash crossing / photo)',
    'DP - The Drips':                      '10-15 min (natural spring)',
    'The Twin Priests':                    '15-30 min (spires, off-route)',
    'Hondu Arch Viewpoint':                '15-30 min (viewpoint)',
    'Temple Mountain Viewpoint':           '15-30 min (viewpoint)',
    'Calf Canyon':                         '15-30 min (canyon feature)',
    'Horizon Arch':                        '20-40 min (off-route arch)',
    'Copper Globe Mine':                   '20-40 min (historic mine)',
    'Lucky Strike Mine':                   '20-40 min (historic mine)',
    'Old Mining Sites':                    '15-30 min (generic)',
    'Wild Horse Canyon':                   '15-30 min (scenic)',
    'Tunnel / Freeway Underpass':          '10-20 min (the famous I-70 underpass; HEIGHT CHECK for tall rigs)',
    'Freeway Access':                      'ongoing (optional bypass for tall rigs)',
}


def t_est(w):
    n = (w.get('name') or '').strip()
    if n in TIME_OVERRIDE:
        return TIME_OVERRIDE[n]
    return TIME_EST.get(w.get('sym') or '', '-')


def flag_row(w, day):
    """Pre-seed a suggested disposition for each POI based on obvious criteria.

    The USER will make the final decision; these are recommendations for review.
    """
    name = w.get('name') or ''
    sym = w.get('sym') or ''
    dist = w.get('dist_to_track_m', 0)

    # Critical POIs from Chuck's narrative
    must = {
        'DP - Black Dragon Petroglyph', 'DP - Black Dragon Canyon',
        'DP - Buckhorn Wash Petroglyphs', 'DP - Buckhorn Wash',
        'DP - Wedge Overlook', 'DP - Little Grand Canyon',
        'DP - Eagle Canyon Bridges', 'DP - Eagle Canyon Overlook', 'DP - Eagle Canyon Arch',
        "DP - Swasey's Cabin",
        'DP - Tomsich Butte Uranium Mine',
        'DP - Head of Sinbad Petroglyph', 'DP - Dutchman Arch',
    }
    nice = {
        'DP - Old San Rafael Swinging Bridge',   # drive-by per user
        'DP - Dinosaur Footprint', 'DP - Split Rock', 'DP - Red Canyon',
        'DP - The Sinkhole', 'DP - The Drips',
        'DP - Eva Conover Trail', 'DP - Eagle Canyon Trail',
        'DP - The Icebox', 'DP - Loan Warrior Petroglyph',
        'DP - Reds Canyon', 'DP - Hondu Arch', 'DP - Hidden Splendor Overlook',
        "DP - Miner's Cabin", 'DP - Behind the Reef trail',
        'DP - North Temple Wash', 'DP - Temple Wash Petroglpyhs',
    }
    long_optional = {
        'DP - Wild Horse Window Arch',
        'DP - Chute Canyon', 'DP - Crack Canyon',
        'Little Wild Horse Slot Canyon', 'Goblin Valley State Park',
    }
    off_route = {
        'DP - Petroglyph Canyon Panel', 'DP - Spirit Arch',
        'The Twin Priests', 'Horizon Arch',
    }

    if name in must:
        return 'PRIMARY (recommend)'
    if name in long_optional:
        return 'OPTIONAL - long hike/side trip (decide)'
    if name in off_route:
        return 'SIDE TRIP - off main route (decide)'
    if name in nice:
        return 'RECOMMENDED - short stop'
    if sym in ('fuel-24', 'city-24', 'toilets-24'):
        return 'LOGISTICS'
    if sym == 'campsite-24':
        return '(campsite, not POI)'
    if dist > 1500:
        return 'FAR from route (skip unless planned side trip)'
    return 'EXTRA - short stop if time'


out = []
out.append('# San Rafael Swell - POI Triage Menu')
out.append('')
out.append('**Purpose:** Review every candidate stop on the route, bucketed by day, and mark each as PRIMARY / BACKUP / SKIP.')
out.append('')
out.append(f'**Total main-track distance:** {analysis["track_miles"]} mi')
out.append('')
out.append('**Legend:**')
out.append('- `(mi)` = miles along the main route from Black Dragon Canyon entry.')
out.append('- `off` = distance in meters from nearest point on the main track (large = side trip or fixup needed).')
out.append('- **Recommend** column = my opening suggestion - YOU override freely.')
out.append('')
out.append('---')
out.append('')

for day_label, mi_lo, mi_hi, descr in DAYS:
    day_wpts = [w for w in wpts if mi_lo <= w['mile'] < mi_hi]
    pois = [w for w in day_wpts if (w.get('sym') or '') in POI_KEEP_SYMS]
    camps = [w for w in day_wpts if (w.get('sym') or '') == 'campsite-24']
    logistics = [w for w in day_wpts if (w.get('sym') or '') in ('fuel-24', 'toilets-24')]

    out.append(f'## {day_label} - mi {mi_lo:g} to {mi_hi:g}  ({descr})')
    out.append('')
    out.append(f'- Leg distance: ~{(mi_hi - mi_lo):.0f} mi')
    out.append(f'- POI candidates: {len(pois)}')
    out.append(f'- Campsite waypoints: {len(camps)}')
    out.append(f'- Logistics waypoints: {len(logistics)}')
    out.append('')

    # POI table
    out.append('### POI candidates')
    out.append('')
    out.append('| Mi | Off (m) | Name | Type | Time estimate | Recommend | Your decision |')
    out.append('|---:|---:|---|---|---|---|---|')
    for w in pois:
        rec = flag_row(w, day_label)
        name = (w.get('name') or '').replace('|', '\\|')
        sym = (w.get('sym') or '').replace('|', '\\|')
        out.append(f'| {w["mile"]:.1f} | {w["dist_to_track_m"]:.0f} | {name} | {sym} | {t_est(w)} | {rec} |  |')
    out.append('')

    # Logistics (fuel, toilets)
    if logistics:
        out.append('### Logistics (fuel / toilets)')
        out.append('')
        out.append('| Mi | Off (m) | Name | Type |')
        out.append('|---:|---:|---|---|')
        for w in logistics:
            out.append(f'| {w["mile"]:.1f} | {w["dist_to_track_m"]:.0f} | {(w.get("name") or "")} | {(w.get("sym") or "")} |')
        out.append('')

    # Campsites summary (name + mi + off-track dist; details go in a separate campsite selection step)
    if camps:
        out.append('### Campsite candidates (for later selection)')
        out.append('')
        out.append('| Mi | Off (m) | Name |')
        out.append('|---:|---:|---|')
        for w in camps:
            out.append(f'| {w["mile"]:.1f} | {w["dist_to_track_m"]:.0f} | {(w.get("name") or "")} |')
        out.append('')

    out.append('---')
    out.append('')

(PLAN / 'poi_menu.md').write_text('\n'.join(out), encoding='utf-8')
print(f'Wrote {PLAN / "poi_menu.md"}')
