"""Alternate itinerary A (forward, 4-day Swell lighten; Variant V2).

Day split summary:
  May 2: Travel + stage at Black Dragon (same as main).
  May 3: Day 1 Black Dragon -> Wedge (same as main).
  May 4: Day 2 lightened -> camp at Family Butte (~mi 127).
  May 5: Day 3 Family Butte -> Reds -> Tomsich -> Hidden Splendor ->
         BTR traverse (no tactical slots) -> Temple Mtn camp.
  May 6: Day 4 stay-over slots (Chute/Crack) + Sinbad cluster; extra
         Swell night (Temple Mtn / Goblin). Early-leavers peel off AM.
  May 7: Travel to Moab (Ken's Lake), easy afternoon trail.

Reuses main-trip POI catalog via trip_core.POI_STATUS.
"""
from __future__ import annotations
import pathlib
import sys

_BASE = pathlib.Path(__file__).resolve().parent.parent.parent
_SCRIPTS = _BASE / 'scripts'
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from trip_core import (  # noqa: E402
    DAY0_STAGE_NAMES,
    SUPPRESS_NAMES,
    build_payload,
    load_route,
    print_payload_summary,
    write_payload,
)
from alts.common import (  # noqa: E402
    FUEL_PLAN_SUMMARY,
    GROUP_COUNTS,
    REALTIME_LINKS,
    black_dragon_stage,
    family_butte_primary_camps,
    kens_lake_camps,
    stayover_sinbad_camps,
    temple_mtn_camps,
    wedge_overlook_camps,
)


PLAN = _BASE / 'planning'

# Mile anchors sourced from planning/route_analysis.json:
#   Loan Warrior Petroglyph ............ mi 118.45
#   Family Butte Dispersed ............. mi 127.06
#   Reds Canyon ........................ mi 133.98
#   Tomsich Butte Uranium Mine ......... mi 141.42
#   Hidden Splendor Overlook ........... mi 156.42
#   Miner's Cabin / BTR trail .......... mi 184.8
#   North Temple Wash (Day-4 AM start) . mi 200.20
# The Family Butte split is placed at mi 127.5 so it captures everything
# through Loan Warrior on Day 2 and starts Day 3 at Reds Canyon.
DAY2_A_END_MI = 127.5


DAYS = [
    {
        'id': 'altA_day0_travel',
        'label': 'May 2 (Fri) - Travel + Stage (Black Dragon)',
        'date_iso': '2026-05-02',
        'title': 'Boise, ID -> Black Dragon Canyon',
        'type': 'travel',
        'descr': 'Same as main plan: travel via I-84 / I-15 / I-70; fuel in Green River; '
                 'stage at Black Dragon dispersed.',
        'miles': 620,
        'driving_hours_est': 9.5,
        'camp_key': 'altA_day0_travel',
        'include_day0_staging_pois': True,
    },
    {
        'id': 'altA_day1_swell',
        'label': 'May 3 (Sat) - Day 1: Black Dragon -> Wedge',
        'date_iso': '2026-05-03',
        'title': 'Day 1: Black Dragon Canyon -> Wedge Overlook',
        'type': 'overland',
        'descr': 'Unchanged vs main plan: classic intro day through Black Dragon, Buckhorn '
                 'Wash + petroglyph panel, finish at the Wedge rim.',
        'miles': 68,
        'driving_hours_est': 5.5,
        'track_segments': [{'mi_lo': 0.0, 'mi_hi': 68.0, 'reverse': False}],
        'camp_key': 'altA_day1_swell',
    },
    {
        'id': 'altA_day2_swell',
        'label': 'May 4 (Sun) - Day 2: Wedge -> Family Butte (SHORT)',
        'date_iso': '2026-05-04',
        'title': 'Day 2 (lightened): Wedge -> Eagle Canyon -> Family Butte',
        'type': 'overland',
        'descr': 'Shortened Day 2 (~50 mi vs ~72 on main): Wedge -> River Crossing -> Drips '
                 '-> Eva Conover -> Eagle Canyon cluster -> Icebox -> Swaseys -> Loan Warrior '
                 '-> camp Family Butte. Reds + Lucky Strike + Tomsich + Hondu pushed to Day 3.',
        'miles': 60,
        'driving_hours_est': 5.5,
        'track_segments': [{'mi_lo': 68.0, 'mi_hi': DAY2_A_END_MI, 'reverse': False}],
        'camp_key': 'altA_day2_swell',
    },
    {
        'id': 'altA_day3_swell',
        'label': 'May 5 (Mon) - Day 3: Family Butte -> Temple Mtn (BTR, no slots)',
        'date_iso': '2026-05-05',
        'title': 'Day 3: Family Butte -> Reds / Tomsich / Hondu -> Hidden Splendor -> '
                 'BTR traverse -> Temple Mtn camp',
        'type': 'overland',
        'descr': 'Drive Reds Canyon + Lucky Strike + Tomsich Butte mine + Hondu + Hidden '
                 'Splendor + Miners Cabin + Behind-the-Reef traverse (do not schedule '
                 'Chute / Crack / LWH mid-day -- drive past) -> Temple Mtn camp. Optional '
                 'evening carpool to Wild Horse Window from camp.',
        'miles': 75,
        'driving_hours_est': 7.0,
        'track_segments': [{'mi_lo': DAY2_A_END_MI, 'mi_hi': 200.0, 'reverse': False}],
        'camp_key': 'altA_day3_swell',
    },
    {
        'id': 'altA_day4_stayover',
        'label': 'May 6 (Tue) - Day 4: Shared AM + stay-over slot hikes + Sinbad',
        'date_iso': '2026-05-06',
        'title': 'Day 4: Temple Mtn -> Chute / Crack (stay-overs) -> Sinbad cluster '
                 '-> extra Swell night',
        'type': 'overland',
        'descr': 'Whole group breakfast ~07:30 + shared send-off (Temple Wash Petroglyphs '
                 'or carpool Wild Horse Window if not done May 5 evening). ~09:00-09:15 '
                 'group split at Temple Mtn or Hwy 24: early-leavers take Hwy 24 N -> I-70 W '
                 'to Boise (on pavement by 09:30 target). Stay-overs head W on Behind-the-Reef '
                 'to Chute + Crack trailheads (tactical; flood check), then return E -> Tunnel '
                 '-> Head of Sinbad -> Dutchman Arch -> stop short for an extra Swell night.',
        'miles': 35,
        'driving_hours_est': 4.5,
        # Covers Temple Mtn -> North Temple Wash -> Tunnel -> Head of Sinbad -> Dutchman.
        # Chute / Crack trailheads sit at mi ~190-192 so include the ~10 mi of BTR needed
        # to reach them by starting this day's slice 10 mi west of Temple Mtn.
        'track_segments': [{'mi_lo': 190.0, 'mi_hi': 226.0, 'reverse': False}],
        'camp_key': 'altA_day4_stayover',
    },
    {
        'id': 'altA_day5_moab_transit',
        'label': 'May 7 (Wed) - Transit to Moab + easy afternoon',
        'date_iso': '2026-05-07',
        'title': 'Head of Sinbad area -> I-70 E -> Moab / Ken\'s Lake; optional Fins N Things',
        'type': 'transit',
        'descr': 'Morning I-70 E to Moab / Ken\'s Lake. Afternoon recovery trail: '
                 'planned Fins N Things (BLM Sand Flats); confirm permits/fees on arrival.',
        'miles': 120,
        'driving_hours_est': 2.5,
        'camp_key': 'altA_day5_moab_transit',
    },
    {
        'id': 'altA_day6_moab',
        'label': 'May 8 (Thu) - Moab Day 1',
        'date_iso': '2026-05-08',
        'title': 'Moab - Day 1 (activities TBD)',
        'type': 'moab',
        'descr': 'Arches / Canyonlands / SR 279 petroglyphs / slickrock -- activities TBD.',
        'camp_key': 'altA_day6_moab',
    },
    {
        'id': 'altA_day7_moab',
        'label': 'May 9 (Fri) - Moab Day 2',
        'date_iso': '2026-05-09',
        'title': 'Moab - Day 2 (activities TBD)',
        'type': 'moab',
        'descr': 'Full Moab day.',
        'camp_key': 'altA_day7_moab',
    },
    {
        'id': 'altA_day8_return',
        'label': 'May 10 (Sat) - Return to Boise',
        'date_iso': '2026-05-10',
        'title': 'Moab -> Boise',
        'type': 'travel',
        'descr': 'Moab -> I-70 W -> Salina -> I-15 N -> I-84 W -> Boise (~670 mi).',
        'miles': 670,
        'driving_hours_est': 10.5,
    },
]


CAMPS = {
    'altA_day0_travel':         black_dragon_stage(),
    'altA_day1_swell':          wedge_overlook_camps(),
    'altA_day2_swell':          family_butte_primary_camps(),
    'altA_day3_swell':          temple_mtn_camps(),
    'altA_day4_stayover':       stayover_sinbad_camps(),
    'altA_day5_moab_transit':   kens_lake_camps(),
    'altA_day6_moab':           {'inherit': 'altA_day5_moab_transit'},
    'altA_day7_moab':           {'inherit': 'altA_day5_moab_transit'},
}


SCHEDULE_DEFAULTS = {
    'altA_day1_swell':    {'break_camp': '09:00', 'moving_mph': 20},
    'altA_day2_swell':    {'break_camp': '08:30', 'moving_mph': 16},
    'altA_day3_swell':    {'break_camp': '08:00', 'moving_mph': 14},
    'altA_day4_stayover': {'break_camp': '07:30', 'moving_mph': 18},
}


INTRO_HTML = (
    '<div class="info">'
    '<strong>Alternate A - Forward, 4-day Swell lighten (Variant V2).</strong> '
    'Same direction as the main plan but shortens Day 2 by camping at <strong>Family '
    'Butte</strong> and pushes Reds Canyon / Tomsich / Hondu / Hidden Splendor to Day 3. '
    'Behind-the-Reef is driven without scheduling the tactical slot hikes; those slots '
    '(Chute / Crack / LWH) move to <strong>May 6</strong> for stay-overs along with the '
    'Sinbad cluster. Early-leavers exit <strong>May 6</strong> (~09:15) toward Boise; '
    'stay-overs hold an <em>extra Swell night</em> (Temple Mtn / Goblin) and hit Moab '
    '<strong>May 7</strong> for an easy afternoon trail (Fins N Things). '
    'Planning notes: <a href="planning/trip-itinerary-alt-a.md">trip-itinerary-alt-a.md</a> '
    '&middot; <a href="overland-alternates.html">Alt overview</a>.'
    '</div>'
)


def build() -> pathlib.Path:
    route = load_route(PLAN)
    payload = build_payload(
        days_spec=DAYS,
        camp_data=CAMPS,
        schedule_defaults=SCHEDULE_DEFAULTS,
        route=route,
        trip_meta={
            'title': '2026 SRS Adventure + Moab - Alt A (forward, 4-day, V2)',
            'dates': '2026-05-02 through 2026-05-10',
            'route_gpx_source': 'san-rafael-swell-adv-route-2025.gpx',
            'route_total_miles': round(route['total_mi'], 2),
            'main_track_points': len(route['main_points']),
            'variant': 'A-V2',
        },
        group_counts=GROUP_COUNTS,
        fuel_plan=FUEL_PLAN_SUMMARY,
        realtime_links=REALTIME_LINKS,
        generated_at='2026-04-20',
        intro_html=INTRO_HTML,
        day0_stage_names=DAY0_STAGE_NAMES,
        suppress_names=SUPPRESS_NAMES,
    )
    out_path = PLAN / 'trip_data_alt_a.json'
    write_payload(payload, out_path)
    print(f'Wrote {out_path} ({out_path.stat().st_size / 1024:.1f} KB)')
    print_payload_summary(payload, label='Alternate A')
    return out_path


if __name__ == '__main__':
    build()
