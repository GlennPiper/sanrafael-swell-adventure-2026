"""Build a campsite selection menu that aligns with the locked POI flow.

Rules for ranking:
- For each day, look at candidates within a 'target mile window' near end-of-day POI.
- Prefer on-track (dist_to_track_m <= 250) sites so the whole group can stage easily.
- Prefer clusters of numbered sites (Buckhorn, Wedge, Temple Mtn) for group capacity.
- Surface designated sites (by name) vs truly dispersed.
"""
from __future__ import annotations
import json
import pathlib

BASE = pathlib.Path(__file__).resolve().parent.parent
PLAN = BASE / 'planning'
analysis = json.loads((PLAN / 'route_analysis.json').read_text(encoding='utf-8'))
wpts = analysis['waypoints_ordered']
camps = [w for w in wpts if (w.get('sym') or '') == 'campsite-24']

# Target windows per day (end-of-day buckets). We'll also include a "staging" bucket for May 2.
DAYS = {
    'May 2 (staging)':     {'mi_lo': 28.0,  'mi_hi': 70.0,  'desc': 'Arrive Boise->Swell entrance. Stage near route start so Day 1 kicks off immediately.'},
    'May 3 (end Day 1)':   {'mi_lo': 57.0,  'mi_hi': 66.0,  'desc': 'Wedge Overlook cluster (numbered sites).'},
    'May 4 (end Day 2)':   {'mi_lo': 115.0, 'mi_hi': 130.0, 'desc': 'Eagle Canyon Arch / Loan Warrior / Family Butte area.'},
    'May 5 (end Day 3)':   {'mi_lo': 194.0, 'mi_hi': 200.0, 'desc': 'Temple Mountain area (final Swell camp). Also near Wild Horse Window trailhead.'},
}

out = []
out.append('# San Rafael Swell - Campsite Selection Menu')
out.append('')
out.append('Bucketed by the end-of-day arrival window for each camping night. Candidates are ordered by mile; on-track (<= 250 m) called out.')
out.append('')
out.append('Legend:')
out.append('- `(mi)` = miles along route')
out.append('- `off m` = distance from nearest point on main track (0-50 m = on the track; 50-250 m = short spur; >250 m = noticeable detour)')
out.append('- "numbered" = part of a BLM-designated site cluster (Buckhorn Draw, Wedge Overlook, Temple Mountain) - each site typically fits 2-3 vehicles.')
out.append('')
out.append('---')
out.append('')

# Additional "May 2 staging" candidate we already know about: San Rafael (Swinging Bridge) Campground.
# It appears in the waypoint list at mi 28.8 as 'San Rafael Bridge Campground'.
# It is 30 min off I-70 and a logical first-night stop.

for day, cfg in DAYS.items():
    mi_lo, mi_hi, desc = cfg['mi_lo'], cfg['mi_hi'], cfg['desc']
    cands = [w for w in camps if mi_lo <= w['mile'] < mi_hi]
    out.append(f'## {day} - window mi {mi_lo:g}..{mi_hi:g}')
    out.append('')
    out.append(f'**Context:** {desc}')
    out.append('')

    if not cands:
        out.append('_No campsite waypoints in this window; may need to widen._')
        out.append('')
        continue

    out.append('| Mi | Off m | Name | Notes |')
    out.append('|---:|---:|---|---|')
    for c in cands:
        name = (c.get('name') or '').replace('|', '\\|')
        notes = []
        if c['dist_to_track_m'] <= 50:
            notes.append('on-track')
        elif c['dist_to_track_m'] <= 250:
            notes.append('short spur')
        else:
            notes.append('detour')
        if 'Buckhorn' in name or 'Wedge' in name or 'Temple' in name:
            notes.append('numbered/designated')
        if 'Group' in name:
            notes.append('GROUP SITE')
        out.append(f'| {c["mile"]:.1f} | {c["dist_to_track_m"]:.0f} | {name} | {", ".join(notes) or "-"} |')
    out.append('')
    out.append('---')
    out.append('')

(PLAN / 'campsite_menu.md').write_text('\n'.join(out), encoding='utf-8')
print(f'Wrote {PLAN / "campsite_menu.md"}')
