"""Alternate itinerary D (reverse, BTR split, Crack camp D1; Variant V1).

Day split summary:
  May 1: Meet Boise -> overnight Bonneville (same as main).
  May 2: Travel + stage at Temple Mtn Townsite (same as B).
  May 3: Day 1 Temple Mtn -> Dutchman -> Head of Sinbad -> Tunnel -> NTW ->
         Wild Horse Window -> BTR W (Chute/Crack/LWH section) -> camp near
         Crack Canyon trailhead. *No* Hidden Splendor today.
  May 4: Day 2 Crack camp -> BTR west (Miner's Cabin etc.) -> Hidden Splendor
         Overlook -> Tomsich / Hondu -> Reds / Lucky Strike -> Loan Warrior ->
         Swaseys -> Icebox -> Eagle Canyon cluster -> camp Family Butte.
  May 5: Day 3 Family Butte -> Eva Conover -> Drips -> River Crossing ->
         Fuller Bottom -> Wedge Overlook camp.
  May 6: Split at Wedge. Early-leavers N -> Green River Cutoff -> Castle Dale
         -> I-15/I-84 to Boise by 09:30. Stay-overs (V1) N through Buckhorn
         corridor + Black Dragon string -> I-70 E -> Sand Flats cluster same evening.
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
    load_highway_tracks,
    load_route,
    print_payload_summary,
    write_payload,
)
from alts.common import (  # noqa: E402
    FUEL_PLAN_SUMMARY,
    GROUP_COUNTS,
    REALTIME_LINKS,
    bonneville_may1_camps,
    crack_canyon_camps,
    family_butte_primary_camps,
    may1_meet_synthetic_pois,
    sand_flats_moab_camps,
    temple_mtn_staging,
    wedge_overlook_camps,
)


PLAN = _BASE / 'planning'


# Mile anchors (from planning/route_analysis.json, reading the master track
# in its natural forward direction):
#   Buckhorn / Dinosaur Footprint .. mi ~55-60
#   Wedge Overlook ................. mi ~68
#   Eagle Canyon cluster ........... mi ~85-105
#   Family Butte ................... mi 127.06
#   Reds Canyon .................... mi 133.98
#   Tomsich Butte mine ............. mi 141.42
#   Miner's Cabin / BTR west ....... mi 184.8
#   Hidden Splendor Overlook ....... mi 156.42   <-- spur, not on the main
#                                                    track; will surface as
#                                                    a POI on Day 2.
#   North Temple Wash start ........ mi 200.2
#   Wild Horse Window .............. mi ~212
#   Chute / Crack trailheads ....... mi ~190-192 (west end of BTR)
#   Temple Mtn townsite ............ mi ~226 (end of master track)
#
# Day 1 (reverse) runs Temple Mtn -> Chute / Crack: mi 190 .. 226 reversed.
# Day 2 (reverse) runs Crack -> Family Butte: mi 127.5 .. 190 reversed.
# Day 3 (reverse) runs Family Butte -> Wedge: mi 68 .. 127.5 reversed.
# Day 4 (reverse) runs Wedge -> Black Dragon: mi 0 .. 68 reversed
# (only stay-overs drive the full corridor; early-leavers peel off).
DAY1_D_LO_MI = 190.0
DAY1_D_HI_MI = 226.0
DAY2_D_LO_MI = 127.5
DAY2_D_HI_MI = 190.0
DAY3_D_LO_MI = 68.0
DAY3_D_HI_MI = 127.5


DAYS = [
    {
        'id': 'altD_may1_bonneville',
        'label': 'May 1 (Fri) - Meet + Bonneville overnight',
        'date_iso': '2026-05-01',
        'title': 'Boise meet -> Bonneville Salt Flats area',
        'type': 'travel',
        'descr': (
            'Same meet + Bonneville overnight as the main plan (Albertsons / Sinclair Federal Way; '
            'depart by 1:00 PM).'
        ),
        'miles': 340,
        'driving_hours_est': 5.5,
        'camp_key': 'altD_may1_bonneville',
        'synthetic_pois': may1_meet_synthetic_pois(),
    },
    {
        'id': 'altD_day0_travel',
        'label': 'May 2 (Sat) - Travel + Stage (Temple Mtn side)',
        'date_iso': '2026-05-02',
        'title': 'Bonneville area -> Temple Mountain Townsite (staging)',
        'type': 'travel',
        'descr': 'Same as Alt B Day 0 after Bonneville night: Wendover area -> Green River -> '
                 'Hwy 24 S -> Temple Mtn Townsite (FCFS) or Goblin Valley SP.',
        'miles': 310,
        'driving_hours_est': 5.0,
        'camp_key': 'altD_day0_travel',
    },
    {
        'id': 'altD_day1_swell',
        'label': 'May 3 (Sun) - Day 1: Temple Mtn -> Sinbad -> BTR W -> Crack camp',
        'date_iso': '2026-05-03',
        'title': 'Day 1 (reverse, BTR east half): Temple Mtn -> Dutchman -> Sinbad -> '
                 'BTR W to Crack trailhead cluster',
        'type': 'overland',
        'descr': 'Reverse-direction Day 1: Temple Mtn -> Dutchman Arch -> Head of Sinbad '
                 '-> Tunnel -> North Temple Wash -> Temple Wash Petroglyphs -> carpool '
                 'Wild Horse Window -> Behind-the-Reef W (Chute / Crack / LWH section). '
                 'NO Hidden Splendor Overlook today. Camp near Crack Canyon trailhead.',
        'miles': 38,
        'driving_hours_est': 5.5,
        'track_segments': [{'mi_lo': DAY1_D_LO_MI, 'mi_hi': DAY1_D_HI_MI, 'reverse': True}],
        'camp_key': 'altD_day1_swell',
    },
    {
        'id': 'altD_day2_swell',
        'label': 'May 4 (Mon) - Day 2: Crack -> BTR W + HS Overlook -> Family Butte',
        'date_iso': '2026-05-04',
        'title': 'Day 2 (reverse): Crack -> BTR west (Miner\'s Cabin) -> Hidden Splendor '
                 '-> Tomsich / Hondu -> Reds / Lucky Strike -> Loan Warrior / Swaseys / '
                 'Icebox / Eagle Canyon -> Family Butte',
        'type': 'overland',
        'descr': 'Continue Behind-the-Reef west through the Miner\'s Cabin section, run '
                 'out to Hidden Splendor Overlook, then the mid-corridor POI string '
                 '(Tomsich / Hondu / Reds / Lucky Strike / Loan Warrior / Swaseys\' / '
                 'Icebox / Eagle Canyon cluster). End at Family Butte dispersed.',
        'miles': 62,
        'driving_hours_est': 7.0,
        'track_segments': [{'mi_lo': DAY2_D_LO_MI, 'mi_hi': DAY2_D_HI_MI, 'reverse': True}],
        'camp_key': 'altD_day2_swell',
    },
    {
        'id': 'altD_day3_swell',
        'label': 'May 5 (Tue) - Day 3: Family Butte -> Wedge (breather)',
        'date_iso': '2026-05-05',
        'title': 'Day 3 (reverse, breather): Family Butte -> Eva Conover -> Drips -> '
                 'River crossing -> Fuller Bottom -> Wedge Overlook',
        'type': 'overland',
        'descr': 'Short recovery day: Family Butte -> Eva Conover Canyon overlook -> '
                 'Coal Wash (optional) -> The Drips -> River Crossing -> Fuller Bottom '
                 '-> Wedge Overlook (camp at the rim for sunrise).',
        'miles': 45,
        'driving_hours_est': 4.5,
        'track_segments': [{'mi_lo': DAY3_D_LO_MI, 'mi_hi': DAY3_D_HI_MI, 'reverse': True}],
        'camp_key': 'altD_day3_swell',
    },
    {
        'id': 'altD_day4_moab_transit',
        'label': 'May 6 (Wed) - Split at Wedge; stay-overs I-70 E to Moab',
        'date_iso': '2026-05-06',
        'title': 'Early-leavers N exit via Green River Cutoff (09:30 target); '
                 'stay-overs run Buckhorn + Black Dragon string -> Sand Flats cluster (V1)',
        'type': 'transit',
        'descr': 'Shared Wedge sunrise ~07:00. ~07:30-08:00 split. Early-leavers: off '
                 'rim N past "Toilets" waypoint -> E Green River Cutoff Rd -> Hwy 10 '
                 '-> Maverik Castle Dale -> US-6 W -> I-15 N -> I-84 W -> Boise (~30 mi '
                 'graded to pavement, ~75 min; inside the 09:30 target). Stay-overs: N '
                 'from Wedge through Buckhorn corridor (Dinosaur Footprint -> petroglyphs '
                 '-> wash -> Split Rock -> Red Canyon -> Swinging Bridge -> Sinkhole) -> '
                 'Black Dragon Canyon + petroglyph -> I-70 Exit 147 E -> Moab / Sand Flats '
                 'evening.',
        'miles': 140,
        'driving_hours_est': 3.5,
        'track_segments': [{'mi_lo': 0.0, 'mi_hi': 68.0, 'reverse': True}],
        'camp_key': 'altD_day4_moab_transit',
    },
    {
        'id': 'altD_day5_moab',
        'label': 'May 7 (Thu) - Moab Day 1',
        'date_iso': '2026-05-07',
        'title': 'Moab - Day 1 (activities TBD)',
        'type': 'moab',
        'descr': 'Sand Flats base camp + activities TBD.',
        'camp_key': 'altD_day5_moab',
    },
    {
        'id': 'altD_day6_moab',
        'label': 'May 8 (Fri) - Moab Day 2',
        'date_iso': '2026-05-08',
        'title': 'Moab - Day 2 (activities TBD)',
        'type': 'moab',
        'descr': 'Full Moab day.',
        'camp_key': 'altD_day6_moab',
    },
    {
        'id': 'altD_day7_moab',
        'label': 'May 9 (Sat) - Moab Day 3',
        'date_iso': '2026-05-09',
        'title': 'Moab - Day 3 (activities TBD)',
        'type': 'moab',
        'descr': 'Final Moab day. Prep for departure.',
        'camp_key': 'altD_day7_moab',
    },
    {
        'id': 'altD_day8_return',
        'label': 'May 10 (Sun) - Return to Boise',
        'date_iso': '2026-05-10',
        'title': 'Moab -> Boise',
        'type': 'travel',
        'descr': 'Moab -> I-70 W -> Salina -> I-15 N -> I-84 W -> Boise (~670 mi).',
        'miles': 670,
        'driving_hours_est': 10.5,
    },
]


CAMPS = {
    'altD_may1_bonneville':   bonneville_may1_camps(),
    'altD_day0_travel':       temple_mtn_staging(),
    'altD_day1_swell':        crack_canyon_camps(),
    'altD_day2_swell':        family_butte_primary_camps(),
    'altD_day3_swell':        wedge_overlook_camps(),
    'altD_day4_moab_transit': sand_flats_moab_camps(),
    'altD_day5_moab':         {'inherit': 'altD_day4_moab_transit'},
    'altD_day6_moab':         {'inherit': 'altD_day4_moab_transit'},
    'altD_day7_moab':         {'inherit': 'altD_day4_moab_transit'},
}


SCHEDULE_DEFAULTS = {
    'altD_day1_swell': {'break_camp': '08:00', 'moving_mph': 16},
    'altD_day2_swell': {'break_camp': '08:00', 'moving_mph': 14},
    'altD_day3_swell': {'break_camp': '09:00', 'moving_mph': 18},
}


INTRO_HTML = (
    '<div class="info">'
    '<strong>Alternate D - Reverse, BTR split, Crack camp D1 (Variant V1).</strong> '
    'Like B but softens Day 1 by <em>splitting</em> Behind-the-Reef across May 3-4 and '
    'camping near the <strong>Crack Canyon trailhead</strong> instead of pushing all '
    'the way to Tomsich. Hidden Splendor Overlook moves to <strong>May 4</strong>. '
    'May 6 split is at <strong>Wedge</strong> (not Swinging Bridge): early-leavers exit '
    'N via E Green River Cutoff Rd to hit pavement by 09:30; stay-overs run the full '
    'Buckhorn + Black Dragon string and reach Moab / Sand Flats the same evening (V1). '
    'Planning notes: <a href="planning/trip-itinerary-alt-d.md">trip-itinerary-alt-d.md</a> '
    '&middot; <a href="overland-alternates.html">Alt overview</a>.'
    '</div>'
)


def build() -> pathlib.Path:
    route = load_route(PLAN)
    hw = load_highway_tracks(PLAN)
    days_spec = []
    for day in DAYS:
        d = dict(day)
        if d['id'] == 'altD_may1_bonneville':
            d['synthetic_track_points'] = hw.get('may1_boise_bonneville') or []
        elif d['id'] == 'altD_day0_travel':
            d['synthetic_track_points'] = hw.get('may2_bonneville_temple_mtn') or []
        elif d['id'] == 'altD_day4_moab_transit':
            d['synthetic_track_points'] = hw.get('green_river_to_sand_flats') or []
        elif d['id'] == 'altD_day8_return':
            d['synthetic_track_points'] = hw.get('sand_flats_to_boise_federal_way') or []
        days_spec.append(d)
    payload = build_payload(
        days_spec=days_spec,
        camp_data=CAMPS,
        schedule_defaults=SCHEDULE_DEFAULTS,
        route=route,
        trip_meta={
            'title': '2026 SRS Adventure + Moab - Alt D (reverse, BTR split, V1)',
            'dates': '2026-05-01 through 2026-05-10',
            'route_gpx_source': 'san-rafael-swell-adv-route-2025.gpx',
            'route_total_miles': round(route['total_mi'], 2),
            'main_track_points': len(route['main_points']),
            'variant': 'D-V1',
            'highway_tracks_note': (
                (hw.get('source') or '').strip() or
                'Highway polylines (when present) follow OpenStreetMap via OSRM; not live Google Maps data.'
            ),
        },
        group_counts=GROUP_COUNTS,
        fuel_plan=FUEL_PLAN_SUMMARY,
        realtime_links=REALTIME_LINKS,
        generated_at='2026-04-20',
        intro_html=INTRO_HTML,
        day0_stage_names=DAY0_STAGE_NAMES,
        suppress_names=SUPPRESS_NAMES,
    )
    out_path = PLAN / 'trip_data_alt_d.json'
    write_payload(payload, out_path)
    print(f'Wrote {out_path} ({out_path.stat().st_size / 1024:.1f} KB)')
    print_payload_summary(payload, label='Alternate D')
    return out_path


if __name__ == '__main__':
    build()
