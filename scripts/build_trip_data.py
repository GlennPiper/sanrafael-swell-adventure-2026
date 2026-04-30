"""Build a single consolidated trip_data.json consumed by HTML and GPX generators.

Inputs:
  planning/route_analysis.json  (waypoints ordered by mile, with track projection)
  planning/route_tracks.json    (raw polylines by track name)

Output:
  planning/trip_data.json

The heavy lifting (POI catalog, track slicing, payload assembly) lives in
``scripts/trip_core.py`` so alternate itineraries under ``scripts/alts/`` can
share the same POI metadata and scheduler defaults while defining their own
day boundaries.
"""
from __future__ import annotations
import pathlib
import sys

_SCRIPTS = pathlib.Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from alts.common import bonneville_may1_camps, may1_meet_synthetic_pois  # noqa: E402

from trip_core import (
    build_payload,
    load_highway_tracks,
    load_route,
    print_payload_summary,
    write_payload,
)
from moab_layers import apply_moab_trails  # noqa: E402

BASE = pathlib.Path(__file__).resolve().parent.parent
PLAN = BASE / 'planning'


# ---------------------------------------------------------------------------
# Day split windows (miles)
# ---------------------------------------------------------------------------
DAYS = [
    {
        'id': 'may1_boise_bonneville',
        'label': 'May 1 (Fri) - Meet + Bonneville overnight',
        'date_iso': '2026-05-01',
        'title': 'Boise meet -> Bonneville Salt Flats area',
        'type': 'travel',
        'descr': (
            'Meet at Albertsons / Sinclair on Federal Way (Boise). Gather noon–1:00 PM; '
            'depart by 1:00 PM. I-84 E toward Wendover; overnight dispersed near Bonneville '
            'Salt Flats (site TBD — see camps below).'
        ),
        'mi_lo': None,
        'mi_hi': None,
        'miles': 340,
        'driving_hours_est': 5.5,
        'synthetic_pois': may1_meet_synthetic_pois(),
    },
    {
        'id': 'day0_travel',
        'label': 'May 2 (Sat) - Travel + Stage',
        'date_iso': '2026-05-02',
        'title': 'Bonneville area -> Black Dragon Canyon',
        'type': 'travel',
        'descr': (
            'Continue from the Bonneville / Wendover corridor via I-80 / I-15 / I-70. '
            'Fuel in Green River. Stage at Black Dragon Canyon dispersed for Day 1 Swell '
            'kick-off.'
        ),
        'mi_lo': None,
        'mi_hi': None,
        'miles': 280,
        'driving_hours_est': 5.0,
    },
    {
        'id': 'day1_swell',
        'label': 'May 3 (Sun) - Day 1: Black Dragon -> Wedge',
        'date_iso': '2026-05-03',
        'title': 'Day 1: Black Dragon Canyon -> Wedge Overlook',
        'type': 'overland',
        'descr': 'Classic intro day: Black Dragon petroglyphs, drive through Buckhorn Wash, hit the iconic pictograph panel, end the day at the Wedge rim.',
        'mi_lo': 0.0,
        'mi_hi': 68.0,
        'miles': 68,
        'driving_hours_est': 5.5,
    },
    {
        'id': 'day2_swell',
        'label': 'May 4 (Mon) - Day 2: Wedge -> Tomsich / Reds',
        'date_iso': '2026-05-04',
        'title': 'Day 2: Wedge -> Eagle Canyon -> Reds Canyon',
        'type': 'overland',
        'descr': 'Meatiest day: Fuller Bottom, Dutch Flat, Eva Conover rocks, Eagle Canyon bridges, Reds Canyon scenery, Tomsich Butte mine and Hondu Arch.',
        'mi_lo': 68.0,
        'mi_hi': 140.0,
        'miles': 72,
        'driving_hours_est': 7.5,
    },
    {
        'id': 'day3_swell',
        'label': 'May 5 (Tue) - Day 3: Reds -> Temple Mtn',
        'date_iso': '2026-05-05',
        'title': 'Day 3: Tomsich Butte -> Behind-the-Reef -> Temple Mtn',
        'type': 'overland',
        'descr': 'Technical day: Hidden Splendor, Miner\'s Cabin, then the slow Behind-the-Reef trail. Default hike: Wild Horse Window. Backup slots: Chute / Crack / full LWH-Bell loop — see slot-canyon-guide.html (PWA). Camp at Temple Mtn.',
        'mi_lo': 140.0,
        'mi_hi': 200.0,
        'miles': 60,
        'driving_hours_est': 6.5,
    },
    {
        'id': 'day4_swell',
        'label': 'May 6 (Wed AM) - Day 4 AM: Temple Mtn -> Sinbad',
        'date_iso': '2026-05-06',
        'title': 'Day 4 AM: Temple Mtn -> Head of Sinbad / Dutchman Arch',
        'type': 'overland',
        'descr': 'Short half-day: North Temple Wash narrows, under-the-freeway tunnel (height check!), Head of Sinbad pictograph, Dutchman Arch. Then group splits - some head home to Boise, others continue to Moab.',
        'mi_lo': 200.0,
        'mi_hi': 226.0,
        'miles': 26,
        'driving_hours_est': 3.0,
    },
    {
        'id': 'day4_moab_transit',
        'label': 'May 6 (Wed PM) - Transit to Moab',
        'date_iso': '2026-05-06',
        'title': 'Head of Sinbad -> I-70 E -> Moab',
        'type': 'transit',
        'descr': 'Exit route, fuel at Green River, drive to Moab / Sand Flats; claim clustered FCFS sites '
                 '(multiple adjoining pads — double-up vehicles where site size allows).',
        'mi_lo': None,
        'mi_hi': None,
        'miles': 70,
        'driving_hours_est': 1.5,
    },
    {
        'id': 'day5_moab',
        'label': 'May 7 (Thu) - Moab Day 1',
        'date_iso': '2026-05-07',
        'title': 'Moab Day 1 — Hell’s Revenge Tip-Toe (RR4W 37)',
        'type': 'moab',
        'descr': (
            'Primary trail: Hell’s Revenge — Tip-Toe Trip (RR4W trail id 37, Sand Flats fee area). '
            'Optional slickrock warm-up: Baby Lion’s Back this morning or Wed May 6 evening — see moab-trails.html#baby-lion. '
            'Sand Flats day-use + camping fees at the booth; cluster FCFS pads in camp block below. '
            'Map orange line is RR4W-published geometry (decimated for this page) — navigate with judgment; '
            'load trip-plan.gpx in Gaia/onX if basemap tiles are offline.'
        ),
        'mi_lo': None,
        'mi_hi': None,
        'miles': None,
        'driving_hours_est': None,
    },
    {
        'id': 'day6_moab',
        'label': 'May 8 (Fri) - Moab Day 2',
        'date_iso': '2026-05-08',
        'title': 'Moab Day 2 — Wipe-Out Hill (RR4W 44)',
        'type': 'moab',
        'descr': (
            'Primary trail: Wipe-Out Hill (RR4W trail id 44). Sand Flats / Moab-area fees as posted; '
            'see camp block for Sand Flats cluster. Map line is RR4W geometry for planning — use live '
            'maps + GPX in the field.'
        ),
        'mi_lo': None,
        'mi_hi': None,
        'miles': None,
        'driving_hours_est': None,
    },
    {
        'id': 'day7_moab',
        'label': 'May 9 (Sat) - Moab Day 3',
        'date_iso': '2026-05-09',
        'title': 'Moab Day 3 — Top of the World (RR4W 38)',
        'type': 'moab',
        'descr': (
            'Primary trail: Top of the World (RR4W trail id 38; Potash / SR 279 approach). '
            'Last full Moab day — pack for Sunday departure. RR4W route on map; verify closures and '
            'group comfort with exposure before committing.'
        ),
        'mi_lo': None,
        'mi_hi': None,
        'miles': None,
        'driving_hours_est': None,
    },
    {
        'id': 'day8_return',
        'label': 'May 10 (Sun) - Return to Boise',
        'date_iso': '2026-05-10',
        'title': 'Sand Flats (Moab) -> Boise (Federal Way meet)',
        'type': 'travel',
        'descr': 'Early departure from Sand Flats cluster; I-70 W -> Salina -> I-15 N -> I-84 W -> '
                 'Boise-area finish at the same Federal Way meet point as May 1 (~670 mi).',
        'mi_lo': None,
        'mi_hi': None,
        'miles': 670,
        'driving_hours_est': 10.5,
    },
]


# ---------------------------------------------------------------------------
# Campsite plan (hand-curated from campsite_plan.md)
# ---------------------------------------------------------------------------
CAMPSITES = {
    # NOTE: All Swell overnight coordinates below are SNAPPED to actual
    # `<sym>campsite-24</sym>` waypoints in san-rafael-swell-adv-route-2025.gpx.
    'may1_boise_bonneville': bonneville_may1_camps(),
    'day0_travel': {  # May 2 night -- stage for Day 1 kickoff at Black Dragon
        'primary': {
            'name': 'Black Dragon Canyon - "Camp site" (GPX-verified)',
            'lat': 38.93141, 'lon': -110.42163,
            'status': 'primary',
            'kind': 'dispersed',
            'cost': 'Free (BLM)',
            'facilities': 'None (no toilets, no water)',
            'notes': 'GPX waypoint "Camp site" 0.80 km from Day-1 track start. '
                     'Camp under cottonwoods; NO camping in the canyon interior (petroglyph zone).',
            'access': 'I-70 mm 147 westbound; gated side road on N side; sandy, high-clearance recommended.',
        },
        'secondary': {
            'name': 'Black Dragon Trailhead Flats (BLM dispersed, highway-adjacent)',
            'lat': 38.92676, 'lon': -110.41852,
            'status': 'secondary',
            'kind': 'dispersed',
            'cost': 'Free (BLM)',
            'facilities': 'None (no toilets, no water; highway noise)',
            'notes': 'Open BLM flats right off I-70 at the Black Dragon exit, only 221 m '
                     'from the Day-1 trail start. Use when primary is full, when anyone arrives '
                     'after dark, or when the group wants to consolidate staging right at the '
                     'trailhead. Lower ambiance than the primary (closer to freeway) but dead '
                     'simple to find, and large enough for the full 11-rig group.',
            'access': 'I-70 Exit 145 (Black Dragon); pull onto the flats just past the cattleguard.',
        },
        'tertiary': {
            'name': 'San Rafael Reef View Area (BLM pullout on I-70)',
            'lat': 38.92111, 'lon': -110.43187,
            'status': 'tertiary',
            'kind': 'dispersed',
            'cost': 'Free (BLM)',
            'facilities': 'None (no toilets, no water; freeway-adjacent, expect noise)',
            'notes': 'Signed BLM view area on the south side of I-70 ~1 mi SW of the Black Dragon '
                     'trailhead (Day-1 track start is ~0.85 mi / 1.35 km NE). Open flats large '
                     'enough to spread the group; use when both primary and secondary options '
                     'are full or when late arrivals want a well-known landmark pullout. '
                     'Negligible backtrack in the morning -- just hop back on I-70 eastbound to '
                     'Exit 145 Black Dragon and start Day 1. Scout on arrival for the flattest '
                     'line-up; no designated pads.',
            'access': 'I-70 eastbound between Exit 129 and Exit 145; signed "San Rafael Reef '
                      'View Area" pullout on the S side of the interstate.',
        },
    },
    'day1_swell': {  # May 3 night -- Wedge Overlook (Day-1 track end 39.09642, -110.75111)
        'primary': {
            'name': 'Wedge Overlook Campsite #5 (GPX) - cluster anchor (#3/#4/#5/#6/#7)',
            'lat': 39.12445, 'lon': -110.75133,
            'status': 'primary',
            'kind': 'designated_dispersed',
            'cost': '$15/site honor system',
            'facilities': 'None (no toilets, no water; very windy -- tie everything down)',
            'notes': 'First-come only. The 8 Wedge sites are spread along the rim road; '
                     '#3 (39.12423,-110.74498), #4 (39.12748,-110.74781), #5 (39.12445,-110.75133), '
                     '#6 (39.12254,-110.75204), #7 (39.12563,-110.75521) form a tight cluster. '
                     'Scout ahead during Buckhorn Wash stop mid-afternoon; claim 3-4 adjacent sites for the group. '
                     '2.3-3.5 km N of track end at the overlook viewpoint.',
            'access': 'Wedge Rd spur off Buckhorn Draw Rd',
            'cluster_members': [
                {'name': 'Wedge Overlook Campsite #3', 'lat': 39.12423, 'lon': -110.74498},
                {'name': 'Wedge Overlook Campsite #4', 'lat': 39.12748, 'lon': -110.74781},
                {'name': 'Wedge Overlook Campsite #6', 'lat': 39.12254, 'lon': -110.75204},
                {'name': 'Wedge Overlook Campsite #7', 'lat': 39.12563, 'lon': -110.75521},
            ],
        },
        'secondary': [
            {
                'name': 'Wedge Overlook Camp #1 (GPX) - east-rim site',
                'lat': 39.10857, 'lon': -110.70223,
                'status': 'secondary',
                'kind': 'designated_dispersed',
                'cost': '$15/site honor system',
                'facilities': 'None',
                'notes': 'East-side rim site, ~4.4 km E of the overlook. Designated Wedge '
                         'site -- can be occupied on its own if the cluster is taken; good '
                         'sunrise exposure but farthest from the iconic overlook viewpoint.',
                'access': 'Wedge Rd east spur (continue past the east-rim turn-off)',
            },
            {
                'name': 'Wedge Overlook Camp #2 (GPX) - east-rim site',
                'lat': 39.11221, 'lon': -110.73341,
                'status': 'secondary',
                'kind': 'designated_dispersed',
                'cost': '$15/site honor system',
                'facilities': 'None',
                'notes': 'East-side rim site ~2 km WSW of #1, roughly midway between the '
                         'east spur and the overlook. Also stands alone; pairs well with #1 '
                         'if two rigs split east while the main group pushes the cluster.',
                'access': 'Wedge Rd east spur',
            },
            {
                'name': 'Wedge Overlook Campsite #8 (GPX) - southern outlier',
                'lat': 39.11674, 'lon': -110.75523,
                'status': 'secondary',
                'kind': 'designated_dispersed',
                'cost': '$15/site honor system',
                'facilities': 'None',
                'notes': 'Southernmost Wedge site, on the same rim road as the #3-#7 '
                         'cluster but ~900 m SSE. Use it to extend the cluster if we need '
                         'one extra site, or as a standalone backup if the cluster is full.',
                'access': 'Wedge Rd spur, ~900 m before the main overlook turn-off',
            },
        ],
        'tertiary': {
            'name': 'Buckhorn Draw Campsite 1 (GPX) - developed loop',
            'lat': 39.16753, 'lon': -110.73766,
            'status': 'tertiary',
            'kind': 'developed_fcfs',
            'cost': '$15 ind / $50 group',
            'facilities': 'Vault toilets, fire rings, tables',
            'notes': 'GPX has Buckhorn Draw sites 1, 7, 14, 15, 16, 17, 20, 23, 26, 30, 32. '
                     '32 total sites + 7 group sites. First-come despite Recreation.gov listing. '
                     '~8 km S of Wedge - requires backtrack at end of Day 1.',
            'access': 'Buckhorn Draw Rd, on route near mi 45-50',
        },
    },
    'day2_swell': {  # May 4 night -- Tomsich Butte area (Day-2 track end 38.69753, -110.97621)
        'primary': {
            'name': 'Tomsich Butte Camp (GPX)',
            'lat': 38.68282, 'lon': -110.98900,
            'status': 'primary',
            'kind': 'dispersed',
            'cost': 'Free (BLM)',
            'facilities': 'None (no toilets, no water)',
            'notes': 'GPX waypoint "Tomsich Butte Camp" 1.98 km from track end. '
                     'Open flat area near the uranium mine ruins and Hondu Arch trailhead. '
                     'This is the logical end-of-day-2 camp. First-come / dispersed - Monday night should be open.',
            'access': 'Tomsich Butte Rd at the mine area',
        },
        'secondary': {
            'name': 'Dispersed Camp near Tomsich (GPX "Camp")',
            'lat': 38.69237, 'lon': -110.99904,
            'status': 'secondary',
            'kind': 'dispersed',
            'cost': 'Free (BLM)',
            'facilities': 'None',
            'notes': 'Adjacent GPX-marked camp spot ~1 km NW of Tomsich Butte Camp. '
                     'Use if primary area is crowded; small footprint (2-3 rigs).',
            'access': 'Tomsich Butte Rd, 1 km past primary',
        },
        'tertiary': {
            'name': 'Family Butte Dispersed Camping (GPX) - BAIL EARLY option',
            'lat': 38.76868, 'lon': -110.83217,
            'status': 'tertiary',
            'kind': 'dispersed',
            'cost': 'Free (BLM)',
            'facilities': 'None',
            'notes': 'GPX-marked open dispersed area, room for 6-8 vehicles. '
                     '~15 km NE of Tomsich - use this if Day 2 runs long and you need to bail '
                     'before reaching Tomsich Butte. Day 3 would then start with the Family Butte -> '
                     'Reds Canyon -> Tomsich drive (~20 min) before the usual Day 3 agenda.',
            'access': 'Family Butte Rd spur, mid-route Day 2',
        },
    },
    'day3_swell': {  # May 5 night -- Temple Mountain area (Day-3 track end 38.66431, -110.64746)
        'primary': {
            'name': 'Temple Mountain Townsite - Site 1 (Group Site) (GPX)',
            'lat': 38.65606, 'lon': -110.66015,
            'status': 'primary',
            'kind': 'developed_fcfs',
            'cost': '$50/night',
            'facilities': 'Vault toilets, fire rings, tables, large shade structure',
            'notes': 'GPX waypoint "Site 1 (Group Site)" - the Temple Mtn Townsite Campground group site. '
                     '1.43 km W of track end. First-come only. Tuesday night = very likely open. '
                     'Scout during Behind-the-Reef slow section.',
            'access': 'Temple Mtn Rd, Townsite Campground complex',
        },
        'secondary': {
            'name': 'Temple Mount East Campground (GPX)',
            'lat': 38.65770, 'lon': -110.66224,
            'status': 'secondary',
            'kind': 'developed_fcfs',
            'cost': '$15/site',
            'facilities': 'Vault toilets',
            'notes': 'GPX waypoint "Temple Mount East Campground" - 10-site loop, 1.48 km from track end. '
                     'First-come. Split group across several sites if group site is taken.',
            'access': 'Temple Mtn Rd, E of the Townsite',
        },
        'tertiary': {
            'name': 'Dispersed "Camp" near track end (GPX)',
            'lat': 38.66075, 'lon': -110.64263,
            'status': 'tertiary',
            'kind': 'dispersed',
            'cost': 'Free (BLM)',
            'facilities': 'None',
            'notes': 'GPX waypoint "Camp" - CLOSEST GPX camp to Day-3 track end (0.58 km). '
                     'Primitive dispersed. Multiple other GPX-marked dispersed spots within 3 km '
                     '(e.g. 38.66500,-110.67681; 38.66549,-110.69267).',
            'access': 'On-route near Temple Mtn area',
        },
    },
    'day4_moab_transit': {  # May 6 night — Sand Flats FCFS cluster
        'primary': {
            'name': 'Sand Flats Recreation Area — adjacent FCFS sites (cluster)',
            'lat': 38.57563, 'lon': -109.52401,
            'status': 'primary',
            'kind': 'developed_fcfs',
            'cost': 'Day-use + camping fees collected at booth',
            'facilities': 'Picnic tables, fire rings, pit toilets; haul drinking water',
            'notes': 'No group reservation. Send scouts early afternoon if possible and grab adjoining '
                     'numbered sites on the same loop (or neighboring loops). Up to **two rigs per pad** '
                     'only when pads are large enough—trailers/tow combos usually need dedicated sites.',
            'access': 'Moab: Center/400 East -> Mill Creek Dr -> Sand Flats Rd (~5 mi graded)',
            'reserve_url': 'https://www.recreation.gov/gateways/2160',
        },
        'secondary': {
            'name': 'Dead Horse Point SP - Wingate (electric site)',
            'lat': 38.4710, 'lon': -109.7450,
            'status': 'secondary',
            'kind': 'developed_reserved',
            'cost': '$60/night',
            'facilities': 'Electric, vault toilets, no showers',
            'notes': '150+ sites available May 6. One site fits up to 8.',
            'access': 'Hwy 313 W off Hwy 191',
            'reserve_url': 'https://utahstateparks.reserveamerica.com',
        },
        'tertiary': {
            'name': 'BLM designated dispersed pods (Mill Canyon / Cotter / Dubinky)',
            'lat': 38.6500, 'lon': -109.7700,
            'status': 'tertiary',
            'kind': 'designated_dispersed',
            'cost': 'Free where marked — obey posted waste rules',
            'facilities': 'None (signs only)',
            'notes': 'Last resort north of Hwy 313 / east of Hwy 191; verify brown post sites.',
            'access': 'Spurs off Cotter Mine, Dubinky, Mill Canyon corridors',
        },
    },
    'day5_moab': {
        'primary': {
            'name': 'Sand Flats Recreation Area — cluster camp (renew sites daily FCFS)',
            'lat': 38.57563, 'lon': -109.52401,
            'status': 'primary',
            'kind': 'developed_fcfs',
            'cost': 'Day-use + nightly camping fee per Grand County/Booth',
            'facilities': 'Pit toilets, picnic tables, fire rings; pack water.',
            'notes': 'Preferred Moab hub: neighboring FCFS pads, two vehicles/site when space allows '
                     '(long trailers usually need standalone sites). Overflow loop opens when staffed.',
            'access': 'Same Sand Flats Rd corridor as transit night.',
            'reserve_url': 'https://www.recreation.gov/gateways/2160',
        },
        'secondary': {
            'name': 'Dead Horse Point SP - Wingate (reserved backup)',
            'lat': 38.4710, 'lon': -109.7450,
            'status': 'secondary',
            'kind': 'developed_reserved',
            'cost': '$60/night',
            'facilities': 'Electric, vault toilets',
            'notes': 'Use if Sand Flats is untenable weather / capacity-wise — book ahead if leaning on this.',
            'access': 'Hwy 313 W off Hwy 191',
            'reserve_url': 'https://utahstateparks.reserveamerica.com',
        },
        'tertiary': {
            'name': 'Dead Horse Kayenta loop / Utahraptor Fossil Flats primitive (fee)',
            'lat': 38.4720, 'lon': -109.7440,
            'status': 'tertiary',
            'kind': 'developed_reserved',
            'cost': 'Varies',
            'facilities': 'Electric at Kayenta; primitive at Fossil Flats corridor',
            'notes': 'Split-group backup options north of downtown.',
            'access': 'Hwy 313 or Hwy 191 N',
            'reserve_url': 'https://utahstateparks.reserveamerica.com',
        },
    },
    'day6_moab': {'inherit': 'day5_moab'},
    'day7_moab': {'inherit': 'day5_moab'},
}


# ---------------------------------------------------------------------------
# Per-day scheduling defaults (only overland days get the on-page scheduler).
# break_camp = HH:MM local; moving_mph = pure driving speed (no stops folded in).
# ---------------------------------------------------------------------------
SCHEDULE_DEFAULTS = {
    'day1_swell': {'break_camp': '09:00', 'moving_mph': 20},
    'day2_swell': {'break_camp': '08:30', 'moving_mph': 15},
    'day3_swell': {'break_camp': '08:30', 'moving_mph': 14},
    'day4_swell': {'break_camp': '09:00', 'moving_mph': 22},
}


# ---------------------------------------------------------------------------
# Fuel plan payload (short version embedded; full is in planning/fuel_plan.md)
# ---------------------------------------------------------------------------
FUEL_PLAN_SUMMARY = {
    'stations': [
        {'name': 'Green River, UT (I-70 Exit 160)', 'lat': 38.9953, 'lon': -110.1599,
         'role': 'Primary fill-up before Day 1 and after Day 4',
         'brands': 'Maverik (24hr), Chevron, Shell, Love\'s, FJ Express'},
        {'name': 'Castle Dale, UT', 'lat': 39.2163, 'lon': -111.0182,
         'role': 'Mid-trip detour (~54 mi RT from Buckhorn Draw)',
         'brands': 'Rocky Mountain Minute Market, Sinclair'},
        {'name': 'Emery, UT', 'lat': 38.9227, 'lon': -111.2535,
         'role': 'Mid-trip detour (~40-50 mi RT via Moore Cutoff Rd)',
         'brands': 'Emery C-Store'},
        {'name': 'Hanksville, UT', 'lat': 38.3722, 'lon': -110.7137,
         'role': 'Day 3-4 detour (~60 mi RT from Temple Mtn)',
         'brands': 'Hollow Mountain (inside a rock!), Whispering Sands'},
        {'name': 'Moab, UT', 'lat': 38.5733, 'lon': -109.5498,
         'role': 'Moab days + pre-return fill',
         'brands': 'Maverik, Chevron, Shell, Sinclair'},
    ],
    'surface_breakdown': {
        'paved_hwy_mi': 0,
        'graded_dirt_mi': 180,
        'rocky_2track_mi': 30,
        'technical_mi': 15,
        'total_mi': 225,
    },
    'mpg_factors': {
        'paved_hwy_65mph': 1.00,
        'paved_local': 0.95,
        'graded_dirt': 0.82,
        'rocky_2track': 0.60,
        'technical_low_range': 0.48,
    },
    'estimated_swell_gallons_16mpg_baseline': 26,
}


# ---------------------------------------------------------------------------
# Real-time info links (short version; full in realtime_info_sources.md)
# ---------------------------------------------------------------------------
REALTIME_LINKS = [
    {'cat': 'Weather', 'label': 'NWS Green River', 'url': 'https://forecast.weather.gov/MapClick.php?lat=38.9953&lon=-110.1599'},
    {'cat': 'Weather', 'label': 'NWS Wedge Overlook area', 'url': 'https://forecast.weather.gov/MapClick.php?lat=39.0985&lon=-110.7850'},
    {'cat': 'Weather', 'label': 'NWS Temple Mountain', 'url': 'https://forecast.weather.gov/MapClick.php?lat=38.6530&lon=-110.6680'},
    {'cat': 'Weather', 'label': 'NWS Moab', 'url': 'https://forecast.weather.gov/MapClick.php?lat=38.5733&lon=-109.5498'},
    {'cat': 'Weather', 'label': 'NWS Dead Horse Point', 'url': 'https://forecast.weather.gov/MapClick.php?lat=38.4710&lon=-109.7450'},
    {'cat': 'Weather', 'label': 'NWS SLC active warnings (Swell)', 'url': 'https://www.weather.gov/slc/WWA'},
    {'cat': 'Weather', 'label': 'NWS GJT hazards (Moab)',          'url': 'https://www.weather.gov/gjt/hazards'},
    {'cat': 'Weather', 'label': 'NWS nationwide active alerts',    'url': 'https://www.weather.gov/alerts'},
    {'cat': 'Weather', 'label': 'NWS SLC flash-flood info',        'url': 'https://www.weather.gov/slc/flashflood'},
    {'cat': 'Weather', 'label': 'NWS Salt Lake City (Swell)', 'url': 'https://www.weather.gov/slc'},
    {'cat': 'Weather', 'label': 'NWS Grand Junction (Moab)', 'url': 'https://www.weather.gov/gjt'},
    {'cat': 'Weather', 'label': 'Radar KICX (Cedar City / Swell)', 'url': 'https://radar.weather.gov/station/KICX/standard'},
    {'cat': 'Weather', 'label': 'Radar KGJX (Moab)', 'url': 'https://radar.weather.gov/station/KGJX/standard'},
    {'cat': 'Roads', 'label': 'UDOT Traveler Info', 'url': 'https://www.udottraffic.utah.gov/'},
    {'cat': 'Roads', 'label': 'UDOT Region 4 news', 'url': 'https://udot.utah.gov/connect/category/region-four'},
    {'cat': 'Roads', 'label': 'UDOT live cameras map', 'url': 'https://udottraffic.utah.gov/map'},
    {'cat': 'Fire/Smoke', 'label': 'Utah Fire Info (official)', 'url': 'https://utahfireinfo.gov/'},
    {'cat': 'Fire/Smoke', 'label': 'Utah fire restrictions (active)', 'url': 'https://utah-fire-info-utahdnr.hub.arcgis.com/pages/active-fire-restrictions'},
    {'cat': 'Fire/Smoke', 'label': 'InciWeb (all active fires)', 'url': 'https://inciweb.wildfire.gov/'},
    {'cat': 'Fire/Smoke', 'label': 'AirNow Fire & Smoke map', 'url': 'https://fire.airnow.gov/'},
    {'cat': 'Water', 'label': 'USGS San Rafael River near Green River', 'url': 'https://waterdata.usgs.gov/monitoring-location/09328500/'},
    {'cat': 'Water', 'label': 'USGS Muddy Creek near Emery', 'url': 'https://waterdata.usgs.gov/monitoring-location/09330500/'},
    {'cat': 'BLM/Parks', 'label': 'BLM Price Field Office', 'url': 'https://www.blm.gov/office/price-field-office'},
    {'cat': 'BLM/Parks', 'label': 'BLM Moab Field Office', 'url': 'https://www.blm.gov/office/moab-field-office'},
    {'cat': 'BLM/Parks', 'label': 'BLM San Rafael Swell Rec Area', 'url': 'https://www.blm.gov/visit/san-rafael-swell-recreation-area'},
    {'cat': 'BLM/Parks', 'label': 'Recreation.gov alerts', 'url': 'https://www.recreation.gov/alerts'},
    {'cat': 'BLM/Parks', 'label': 'Arches NP conditions', 'url': 'https://www.nps.gov/arch/planyourvisit/conditions.htm'},
    {'cat': 'BLM/Parks', 'label': 'Arches timed-entry', 'url': 'https://www.recreation.gov/timed-entry/10089519'},
    {'cat': 'BLM/Parks', 'label': 'Canyonlands NP conditions', 'url': 'https://www.nps.gov/cany/planyourvisit/conditions.htm'},
    {'cat': 'BLM/Parks', 'label': 'Dead Horse Point SP', 'url': 'https://stateparks.utah.gov/parks/dead-horse/'},
    {'cat': 'Emergency', 'label': 'Emery County Sheriff (non-emerg)', 'url': 'tel:+14353812404'},
    {'cat': 'Emergency', 'label': 'Grand County Sheriff (Moab)', 'url': 'tel:+14352598115'},
    {'cat': 'Emergency', 'label': 'UT Highway Patrol (I-70)', 'url': 'tel:+18018873800'},
]


GROUP_COUNTS = {
    'overland': 11,
    'moab': 7,
}


# Day-0 (travel/staging) gets the pre-mile-0 waypoints (mile 0..2 range + any negatives)
DAY0_STAGE_NAMES = {'DP - Petroglyph Canyon Panel', 'DP - Spirit Arch'}
# Waypoints we want to suppress entirely.
DAY01_SUPPRESS_NAMES = {'San Rafael Reef Viewpoint'}


def _attach_main_highway_tracks(hw: dict, day: dict) -> dict:
    """Merge OSRM polylines from planning/highway_tracks.json onto main-trip day rows."""
    d = dict(day)
    key = {
        'may1_boise_bonneville': 'may1_boise_bonneville',
        'day0_travel': 'may2_bonneville_black_dragon',
        'day4_moab_transit': 'green_river_to_sand_flats',
        'day8_return': 'sand_flats_to_boise_federal_way',
    }.get(d['id'])
    if key:
        d['synthetic_track_points'] = hw.get(key) or []
    return d


def main() -> None:
    route = load_route(PLAN)
    hw = load_highway_tracks(PLAN)
    days_spec: list[dict] = []
    for day in DAYS:
        days_spec.append(_attach_main_highway_tracks(hw, day))
    days_spec = apply_moab_trails(days_spec, 'main')

    payload = build_payload(
        days_spec=days_spec,
        camp_data=CAMPSITES,
        schedule_defaults=SCHEDULE_DEFAULTS,
        route=route,
        trip_meta={
            'title': '2026 San Rafael Swell Adventure + Moab',
            'dates': '2026-05-01 through 2026-05-10',
            'route_gpx_source': 'san-rafael-swell-adv-route-2025.gpx',
            'route_total_miles': round(route['total_mi'], 2),
            'main_track_points': len(route['main_points']),
            'highway_tracks_note': (
                (hw.get('source') or '').strip() or
                'Highway polylines (when present) follow OpenStreetMap via OSRM; not live Google Maps data.'
            ),
        },
        group_counts=GROUP_COUNTS,
        fuel_plan=FUEL_PLAN_SUMMARY,
        realtime_links=REALTIME_LINKS,
        generated_at='2026-04-16',
        day0_stage_names=DAY0_STAGE_NAMES,
        suppress_names=DAY01_SUPPRESS_NAMES,
    )

    out_path = PLAN / 'trip_data.json'
    write_payload(payload, out_path)
    print(f'Wrote {out_path} ({out_path.stat().st_size / 1024:.1f} KB)')
    print_payload_summary(payload, label='Main trip')


if __name__ == '__main__':
    main()
