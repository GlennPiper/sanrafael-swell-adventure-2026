"""Alternate itinerary B (reverse, V1).

Run the Swell west -> east (Temple / Sinbad side first, Buckhorn / Black Dragon
last). Variant V1 is the default: stay-overs reach Moab / Sand Flats the
evening of May 6 after any catch-up miles. V2 (extra Swell night May 6,
Moab May 7) is a drop-in alternative the group can pick on the ground.

Day split summary:
  May 1: Meet Boise -> overnight Bonneville (same as main).
  May 2: Travel + stage at Temple Mtn Townsite (or Goblin Valley dispersed).
  May 3: Day 1 meaty reverse: Temple Mtn -> Dutchman -> Head of Sinbad ->
         WHW + tactical slots -> Behind-the-Reef W to Tomsich camp.
  May 4: Day 2 Tomsich -> Reds / Lucky Strike -> Eagle Canyon cluster ->
         Eva Conover -> Wedge camp.
  May 5: Day 3 Wedge -> Buckhorn -> Black Dragon camp (near I-70 exit).
  May 6: Early-leavers pavement by ~09:30; stay-overs I-70 E to Moab / Sand Flats cluster.
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
    black_dragon_stage,
    bonneville_may1_camps,
    may1_meet_synthetic_pois,
    sand_flats_moab_camps,
    temple_mtn_staging,
    tomsich_camps,
    wedge_overlook_camps,
)


PLAN = _BASE / 'planning'


DAYS = [
    {
        'id': 'altB_may1_bonneville',
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
        'camp_key': 'altB_may1_bonneville',
        'synthetic_pois': may1_meet_synthetic_pois(),
    },
    {
        'id': 'altB_day0_travel',
        'label': 'May 2 (Sat) - Travel + Stage (Temple Mtn side)',
        'date_iso': '2026-05-02',
        'title': 'Bonneville area -> Temple Mountain Townsite (staging)',
        'type': 'travel',
        'descr': 'Bonneville / Wendover -> Green River -> S on Hwy 24 -> Temple Mountain Townsite (FCFS) '
                 'or Goblin Valley dispersed. NOT Black Dragon staging.',
        'miles': 310,
        'driving_hours_est': 5.0,
        'camp_key': 'altB_day0_travel',
    },
    {
        'id': 'altB_day1_swell',
        'label': 'May 3 (Sun) - Day 1: Temple Mtn -> Tomsich (MEATY)',
        'date_iso': '2026-05-03',
        'title': 'Day 1 (reverse, meaty): Temple Mtn -> Dutchman -> BTR W -> Tomsich',
        'type': 'overland',
        'descr': 'Longest driving + hike day of the trip while everyone is fresh: '
                 'Temple Mtn -> Dutchman Arch -> Head of Sinbad -> Tunnel -> North Temple '
                 'Wash -> Wild Horse Window -> 1-2 slot hikes (Chute / Crack per group) '
                 '-> Behind-the-Reef (full traverse) -> camp Tomsich Butte.',
        'miles': 86,
        'driving_hours_est': 7.5,
        'track_segments': [{'mi_lo': 141.0, 'mi_hi': 226.0, 'reverse': True}],
        'camp_key': 'altB_day1_swell',
    },
    {
        'id': 'altB_day2_swell',
        'label': 'May 4 (Mon) - Day 2: Tomsich -> Wedge',
        'date_iso': '2026-05-04',
        'title': 'Day 2 (reverse): Tomsich -> Hondu / Reds -> Lucky Strike -> '
                 'Eagle Canyon cluster -> Eva Conover -> Wedge',
        'type': 'overland',
        'descr': 'Tomsich -> Hondu Arch / mine POIs -> Reds Canyon -> Lucky Strike Mine '
                 '-> Loan Warrior Petroglyph -> Swasey\'s Cabin -> Icebox -> Eagle Canyon '
                 'cluster -> Eva Conover -> Drips -> River crossing -> Fuller Bottom -> '
                 'camp Wedge Overlook.',
        'miles': 73,
        'driving_hours_est': 7.0,
        'track_segments': [{'mi_lo': 68.0, 'mi_hi': 141.0, 'reverse': True}],
        'camp_key': 'altB_day2_swell',
    },
    {
        'id': 'altB_day3_swell',
        'label': 'May 5 (Tue) - Day 3: Wedge -> Black Dragon camp',
        'date_iso': '2026-05-05',
        'title': 'Day 3 (reverse): Wedge -> Buckhorn -> Black Dragon camp',
        'type': 'overland',
        'descr': 'Wedge -> Dinosaur Footprint -> Buckhorn Petroglyphs -> Buckhorn Wash '
                 '-> Split Rock -> Red Canyon -> Swinging Bridge -> Sinkhole -> Black '
                 'Dragon Canyon -> Black Dragon Petroglyph. Camp at Black Dragon '
                 'dispersed (near I-70 Exit 147) for minimal May 6 trail + 09:30 pavement.',
        'miles': 68,
        'driving_hours_est': 5.5,
        'track_segments': [{'mi_lo': 0.0, 'mi_hi': 68.0, 'reverse': True}],
        'camp_key': 'altB_day3_swell',
    },
    {
        'id': 'altB_day4_moab_transit',
        'label': 'May 6 (Wed) - Split at Black Dragon; stay-overs I-70 E to Moab',
        'date_iso': '2026-05-06',
        'title': 'Early-leavers pavement; stay-overs I-70 E to Moab / Sand Flats cluster (V1)',
        'type': 'transit',
        'descr': 'Early-leavers: Black Dragon camp -> I-70 Exit 147 W -> on pavement '
                 'by 09:30 target -> home routing. Stay-overs (V1): pick up anything '
                 'skipped on Day 1 (extra slot, BTR segment), then I-70 E to Moab / '
                 'Sand Flats cluster camp same evening.',
        'miles': 140,
        'driving_hours_est': 3.0,
        'camp_key': 'altB_day4_moab_transit',
    },
    {
        'id': 'altB_day5_moab',
        'label': 'May 7 (Thu) - Moab Day 1',
        'date_iso': '2026-05-07',
        'title': 'Moab - Day 1 (activities TBD)',
        'type': 'moab',
        'descr': 'Sand Flats base camp + activities TBD (Arches, biking, SR 279, etc.).',
        'camp_key': 'altB_day5_moab',
    },
    {
        'id': 'altB_day6_moab',
        'label': 'May 8 (Fri) - Moab Day 2',
        'date_iso': '2026-05-08',
        'title': 'Moab - Day 2 (activities TBD)',
        'type': 'moab',
        'descr': 'Full Moab day.',
        'camp_key': 'altB_day6_moab',
    },
    {
        'id': 'altB_day7_moab',
        'label': 'May 9 (Sat) - Moab Day 3',
        'date_iso': '2026-05-09',
        'title': 'Moab - Day 3 (activities TBD)',
        'type': 'moab',
        'descr': 'Final Moab day. Prep for departure.',
        'camp_key': 'altB_day7_moab',
    },
    {
        'id': 'altB_day8_return',
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
    'altB_may1_bonneville':   bonneville_may1_camps(),
    'altB_day0_travel':       temple_mtn_staging(),
    'altB_day1_swell':        tomsich_camps(),
    'altB_day2_swell':        wedge_overlook_camps(),
    'altB_day3_swell':        black_dragon_stage(),
    'altB_day4_moab_transit': sand_flats_moab_camps(),
    'altB_day5_moab':         {'inherit': 'altB_day4_moab_transit'},
    'altB_day6_moab':         {'inherit': 'altB_day4_moab_transit'},
    'altB_day7_moab':         {'inherit': 'altB_day4_moab_transit'},
}


SCHEDULE_DEFAULTS = {
    'altB_day1_swell': {'break_camp': '07:30', 'moving_mph': 14},
    'altB_day2_swell': {'break_camp': '08:30', 'moving_mph': 15},
    'altB_day3_swell': {'break_camp': '08:30', 'moving_mph': 20},
}


INTRO_HTML = (
    '<div class="info">'
    '<strong>Alternate B - Reverse (Sinbad-first), Variant V1.</strong> '
    'Runs the Swell <strong>west -> east</strong>: Temple Mtn / Sinbad side first, '
    'Buckhorn / Black Dragon last. Hardest day (Day 1) is handled while the group is '
    'fresh. Day 3 ends near the highway at Black Dragon so <strong>early-leavers</strong> '
    'hit pavement by 09:30 on May 6 with minimal Swell miles. <strong>V1 stay-overs</strong> '
    'head I-70 E to Moab / Sand Flats the same evening. Planning notes: '
    '<a href="planning/trip-itinerary-alt-b.md">trip-itinerary-alt-b.md</a> '
    '&middot; <a href="overland-alternates.html">Alt overview</a>. '
    'Fuel / resupply narrative in <a href="fuel-plan.html">Fuel plan</a> is still written '
    'forward -- read it east-to-west for this alt.'
    '</div>'
)


def build() -> pathlib.Path:
    route = load_route(PLAN)
    hw = load_highway_tracks(PLAN)
    days_spec = []
    for day in DAYS:
        d = dict(day)
        if d['id'] == 'altB_may1_bonneville':
            d['synthetic_track_points'] = hw.get('may1_boise_bonneville') or []
        elif d['id'] == 'altB_day0_travel':
            d['synthetic_track_points'] = hw.get('may2_bonneville_temple_mtn') or []
        elif d['id'] == 'altB_day4_moab_transit':
            d['synthetic_track_points'] = hw.get('green_river_to_sand_flats') or []
        elif d['id'] == 'altB_day8_return':
            d['synthetic_track_points'] = hw.get('sand_flats_to_boise_federal_way') or []
        days_spec.append(d)
    payload = build_payload(
        days_spec=days_spec,
        camp_data=CAMPS,
        schedule_defaults=SCHEDULE_DEFAULTS,
        route=route,
        trip_meta={
            'title': '2026 SRS Adventure + Moab - Alt B (reverse, V1)',
            'dates': '2026-05-01 through 2026-05-10',
            'route_gpx_source': 'san-rafael-swell-adv-route-2025.gpx',
            'route_total_miles': round(route['total_mi'], 2),
            'main_track_points': len(route['main_points']),
            'variant': 'B-V1',
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
    out_path = PLAN / 'trip_data_alt_b.json'
    write_payload(payload, out_path)
    print(f'Wrote {out_path} ({out_path.stat().st_size / 1024:.1f} KB)')
    print_payload_summary(payload, label='Alternate B')
    return out_path


if __name__ == '__main__':
    build()
