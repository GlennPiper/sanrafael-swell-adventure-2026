"""Build a single consolidated trip_data.json consumed by HTML and GPX generators.

Inputs:
  planning/route_analysis.json  (waypoints ordered by mile, with track projection)
  planning/route_tracks.json    (raw polylines by track name)

Output:
  planning/trip_data.json
"""
from __future__ import annotations
import json
import math
import pathlib

BASE = pathlib.Path(__file__).resolve().parent.parent
PLAN = BASE / 'planning'

analysis = json.loads((PLAN / 'route_analysis.json').read_text(encoding='utf-8'))
tracks = json.loads((PLAN / 'route_tracks.json').read_text(encoding='utf-8'))

main_track = next(t for t in tracks if t['name'] == 'San Rafael Swell Adventure Route')
freeway_access = next((t for t in tracks if t['name'] == 'Freeway Access'), None)
devils_racetrack = next((t for t in tracks if t['name'] == 'Devils Racetrack Alternate Route'), None)

ORDERED = analysis['waypoints_ordered']
TOTAL_MI = analysis['track_miles']

# Build a quick lookup by name (original GPX names) and by name-and-mile for duplicates.
by_name = {}
for w in ORDERED:
    nm = w.get('name') or ''
    by_name.setdefault(nm, []).append(w)

def find(name):
    """Find a waypoint by exact name; returns first match or None."""
    lst = by_name.get(name)
    return lst[0] if lst else None

# ---------------------------------------------------------------------------
# Day split windows (miles)
# ---------------------------------------------------------------------------
DAYS = [
    {
        'id': 'day0_travel',
        'label': 'May 2 (Sat) - Travel + Stage',
        'date_iso': '2026-05-02',
        'title': 'Boise, ID -> Black Dragon Canyon',
        'type': 'travel',
        'descr': 'Long travel day from Boise via I-84 -> I-15 -> I-70. Fuel in Green River. Stage at Black Dragon Canyon dispersed to be ready for Day 1 kick-off.',
        'mi_lo': None,
        'mi_hi': None,
        'miles': 620,
        'driving_hours_est': 9.5,
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
        'descr': 'Exit route, fuel at Green River, drive to Moab. Check in at Ken\'s Lake Group Site B (reserved).',
        'mi_lo': None,
        'mi_hi': None,
        'miles': 70,
        'driving_hours_est': 1.5,
    },
    {
        'id': 'day5_moab',
        'label': 'May 7 (Thu) - Moab Day 1',
        'date_iso': '2026-05-07',
        'title': 'Moab - Day 1 (activities TBD)',
        'type': 'moab',
        'descr': 'Move to Dead Horse Point SP Wingate site. Activities TBD (Arches, Canyonlands Island in the Sky, SR 279 petroglyphs, Hell\'s Revenge, Fins-n-Things, Slickrock, etc.)',
        'mi_lo': None,
        'mi_hi': None,
        'miles': None,
        'driving_hours_est': None,
    },
    {
        'id': 'day6_moab',
        'label': 'May 8 (Fri) - Moab Day 2',
        'date_iso': '2026-05-08',
        'title': 'Moab - Day 2 (activities TBD)',
        'type': 'moab',
        'descr': 'Full Moab day. Activities TBD.',
        'mi_lo': None,
        'mi_hi': None,
        'miles': None,
        'driving_hours_est': None,
    },
    {
        'id': 'day7_moab',
        'label': 'May 9 (Sat) - Moab Day 3',
        'date_iso': '2026-05-09',
        'title': 'Moab - Day 3 (activities TBD)',
        'type': 'moab',
        'descr': 'Final Moab day. Activities TBD. Prep for departure.',
        'mi_lo': None,
        'mi_hi': None,
        'miles': None,
        'driving_hours_est': None,
    },
    {
        'id': 'day8_return',
        'label': 'May 10 (Sun) - Return to Boise',
        'date_iso': '2026-05-10',
        'title': 'Moab -> Boise',
        'type': 'travel',
        'descr': 'Early departure; Moab -> I-70 W -> Salina -> I-15 N -> I-84 W -> Boise. ~670 mi.',
        'mi_lo': None,
        'mi_hi': None,
        'miles': 670,
        'driving_hours_est': 10.5,
    },
]

# ---------------------------------------------------------------------------
# Explicit POI status map from poi_decisions.md (manual transcription)
# status: primary | backup | skip | conditional | hike_candidate
# ---------------------------------------------------------------------------
POI_STATUS = {
    # Day 0 / May 2 staging POIs and bonuses
    'DP - Petroglyph Canyon Panel':        ('backup',   'Bonus if arrive with daylight on May 2'),
    'DP - Spirit Arch':                    ('backup',   'Bonus if arrive with daylight on May 2'),

    # Day 1
    'DP - Black Dragon Petroglyph':        ('primary',  ''),
    'DP - Black Dragon Canyon':            ('primary',  ''),
    'DP - The Sinkhole':                   ('primary',  ''),
    'DP - Old San Rafael Swinging Bridge': ('primary',  'Drive-by photo only'),
    'DP - San Rafael River':               ('backup',   ''),
    'DP - Red Canyon':                     ('primary',  ''),
    'DP - Split Rock':                     ('primary',  'Drive-by photo only'),
    'DP - Buckhorn Wash':                  ('primary',  'The canyon drive itself'),
    'DP - Buckhorn Wash Petroglyphs':      ('primary',  'Famous 130-ft panel'),
    'DP - Dinosaur Footprint':             ('primary',  ''),
    'DP - Little Grand Canyon':            ('primary',  'Combined with Wedge Overlook'),
    'DP - Wedge Overlook':                 ('primary',  'End-of-day highlight'),
    'Petroglyph Panel Trail':              ('skip',     'Trailhead reference only; Black Dragon Petroglyph is the destination'),
    'Calf Canyon':                         ('skip',     '1.7 km off-route cliff viewpoint; not on plan'),

    # Day 2
    'DP - The Drips':                      ('primary',  'Natural spring, on-route'),
    'River crossing':                      ('primary',  'Early Day-2 river crossing (on-route, 1 m off). Added per group request -- water crossings desirable for overlanders.'),
    'Coal Wash':                           ('backup',   ''),
    'DP - Eva Conover Trail':              ('primary',  'Trail section (blue rating)'),
    'DP - Eagle Canyon Overlook':          ('primary',  ''),
    'DP - Eagle Canyon Bridges':           ('primary',  'I-70 bridges from below'),
    'DP - Eagle Canyon Trail':             ('primary',  'Trail section; full-size caution'),
    'DP - Eagle Canyon Arch':              ('primary',  'Short walk'),
    'DP - The Icebox':                     ('primary',  'Short walk into cool grotto'),
    "DP - Swasey's Cabin":                 ('primary',  'Historic cabin'),
    'DP - Loan Warrior Petroglyph':        ('primary',  'Short hike; panel sits ~1.5 mi off the main trail (spur drive budgeted in stop time)'),
    'DP - Reds Canyon':                    ('primary',  'Scenic drive-through'),
    'Lucky Strike Mine':                   ('primary',  'Mine of interest -- added to the route as a primary stop.'),
    'Copper Globe Mine':                   ('skip',     '4.1 km off-route; Lucky Strike covers mine interest'),
    'The Twin Priests':                    ('skip',     '3.7 km off-route'),
    'Hamburger Rocks':                     ('skip',     '2.1 km off-route'),
    'Horizon Arch':                        ('skip',     '2.2 km off-route'),

    # Day 3
    'DP - Tomsich Butte Uranium Mine':     ('primary',  'Mine ruins + equipment'),
    'Hondu Arch Viewpoint':                ('backup',   ''),
    'DP - Hondu Arch':                     ('primary',  ''),
    'DP - Hidden Splendor Overlook':       ('primary',  ''),
    "DP - Miner's Cabin":                  ('primary',  'Historic structure'),
    "Miner's Cabin":                       ('skip',     'Exact duplicate of DP version -- removed'),
    'DP - Behind the Reef trail':          ('primary',  'Technical trail section - slow'),
    # Day 3 tactical hikes (Hike (tactical) badge; checked by default; uncheck ones you skip)
    'DP - Wild Horse Window Arch':         ('hike_candidate', 'Default Day 3 hike; route author #1 geology; 2 mi RT; BLM not GSVP gate; set up camp before this hike and carpool to the trailhead; see slot-canyon-guide.html + AllTrails WHW'),
    'DP - Chute Canyon':                   ('hike_candidate', 'Tactical slot/wash; easier; wide ~first mi; ~0.8 mi to first narrowing (GCT); partial OAB typical; see slot-canyon-guide.html + AllTrails Crack Canyon Wilderness'),
    'DP - Crack Canyon':                   ('hike_candidate', 'Tactical slot; ~5 mi RT typical (Utah.com); ~10 ft drop ~1 mi in; see slot-canyon-guide.html + AllTrails Crack Canyon Wilderness'),
    'Little Wild Horse Canyon Trail':      ('backup',       'LWH/Bell TH; skip OAB from Behind-the-Reef unless full ~8 mi LWH/Bell loop + party OK scrambling; FLASH FLOOD RISK — slot-canyon-guide.html'),
    'Little Wild Horse Slot Canyon':       ('backup',       'Full LWH/Bell loop waypoint only; same caveats — slot-canyon-guide.html'),
    'DP - Temple Wash Petroglpyphs':       ('primary',  'Roadside panel (GPX name has a typo, kept exact for lookup)'),
    'Wild Horse Window Trailhead':         ('skip',     'Trailhead reference only; Wild Horse Window Arch is the destination hike'),
    # Day 3 skips
    'Goblin Valley State Park':            ('skip',     'Off-route side trip; time budget'),
    'Chute Canyon Trailhead':              ('backup',   'Chute Canyon hike parking — slot-canyon-guide.html'),
    'Crack Canyon Trailhead':              ('backup',   'Crack Canyon hike parking; camping nearby possible — slot-canyon-guide.html'),
    'Wild Horse Canyon':                   ('backup',   'AllTrails Wild Horse Canyon trail; lower priority — slot-canyon-guide.html'),
    'Old Mining Sites':                    ('skip',     'Generic waypoint'),

    # Day 4 AM
    'DP - North Temple Wash':              ('primary',  'Scenic narrows drive-through'),
    'Tunnel / Freeway Underpass':          ('primary',  'HEIGHT CHECK for tall rigs; Freeway Access bypass if too tall'),
    'DP - Head of Sinbad Petroglyph':      ('primary',  ''),
    'DP - Dutchman Arch':                  ('primary',  ''),
    'Temple Mountain Viewpoint':           ('skip',     '2.7 km off-route'),
    'Freeway Access':                      ('skip',     'Alt-route anchor waypoint for tunnel bypass (tall rigs); rendered as alternate track on map'),

    # Camping waypoints (handled separately below)
    # Logistics (fuel / toilets) - not POIs
}

# ---------------------------------------------------------------------------
# Campsite plan (hand-curated from campsite_plan.md)
# ---------------------------------------------------------------------------
CAMPSITES = {
    # NOTE: All Swell overnight coordinates below are SNAPPED to actual
    # `<sym>campsite-24</sym>` waypoints in san-rafael-swell-adv-route-2025.gpx.
    # See docstring of scripts/build_trip_data.py's CAMPSITES section for rationale.
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
            # User-identified highway-side BLM flats at the mouth of Black Dragon.
            # 221 m from the Day-1 track start; ideal overflow/late-arrival spot.
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
            # San Rafael Reef View Area -- signed BLM pullout on the south side of I-70
            # about 1 mi south of the Black Dragon trailhead. User-identified replacement
            # for the old Ranch Exit (14 mi west) option, which was too far from the
            # Day-1 kickoff.
            # Source: https://maps.app.goo.gl/UfmZrtjhDtXHCEjD6
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
        # The Wedge is a designated-site-only area: we MUST camp in a numbered site.
        # Eight sites exist (GPX-verified). Our target is the tight #3-#7 cluster on
        # the west rim; the three outlier sites (#1, #2 east; #8 south) serve as
        # equivalent backups that keep us in designated territory before we bail
        # to Buckhorn Draw.
        'primary': {
            # Pin at Wedge Overlook Campsite #5 (center of the #3-#7 cluster, all within 150 m).
            # cluster_members is consumed by build_deliverables to add the other 4
            # cluster sites as additional primary-tier map markers (no separate cards).
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
        # The Wedge is designated-only, so every remaining numbered site is a
        # valid secondary. All three are at the same price/kind as primary, just
        # further from the western overlook cluster.
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
            # If the entire Wedge rim is full, fall back to Buckhorn Draw (developed FCFS).
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
            # Bail-earlier option: stop at Family Butte Dispersed mid-route on Day 2.
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
    'day4_moab_transit': {  # May 6 night (Ken's Lake)
        'primary': {
            'name': "Ken's Lake Group Site B (RESERVABLE)",
            'lat': 38.4875, 'lon': -109.4248,
            'status': 'primary',
            'kind': 'developed_reserved',
            'cost': '$50/night',
            'facilities': 'Vault toilets, fire grates, shade shelter, picnic tables',
            'notes': 'Site B = 25-person capacity, standard (NOT equestrian). Available May 6 as of 2026-04-16 check.',
            'access': 'Hwy 191 S from Moab ~8 mi, E on Ken\'s Lake Rd',
            'reserve_url': 'https://www.recreation.gov/camping/campgrounds/251840',
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
            'name': 'Willow Springs dispersed',
            'lat': 38.7105, 'lon': -109.7180,
            'status': 'tertiary',
            'kind': 'designated_dispersed',
            'cost': '$15/night honor',
            'facilities': 'Fire rings, vault toilets',
            'notes': 'Walk-up only, 11 mi N of Moab.',
            'access': 'Hwy 191 N from Moab',
        },
    },
    'day5_moab': {
        'primary': {
            'name': 'Dead Horse Point SP - Wingate (ideally same site 3 nights)',
            'lat': 38.4710, 'lon': -109.7450,
            'status': 'primary',
            'kind': 'developed_reserved',
            'cost': '$60/night',
            'facilities': 'Electric, vault toilets, no showers',
            'notes': 'Book 1 site for May 7-9 (3 nights). Max 8 ppl/site; we have 7. ~$180 total.',
            'access': 'Hwy 313 W off Hwy 191',
            'reserve_url': 'https://utahstateparks.reserveamerica.com',
        },
        'secondary': {
            'name': 'Dead Horse Point SP - Kayenta',
            'lat': 38.4715, 'lon': -109.7465,
            'status': 'secondary',
            'kind': 'developed_reserved',
            'cost': '$45-60/night',
            'facilities': 'Vault toilets, no showers',
            'notes': '59+ sites open each night of May 7-9.',
            'access': 'Same park, different loop',
            'reserve_url': 'https://utahstateparks.reserveamerica.com',
        },
        'tertiary': {
            'name': "Ken's Lake non-group + BLM dispersed fallback",
            'lat': 38.4875, 'lon': -109.4248,
            'status': 'tertiary',
            'kind': 'dispersed_fcfs',
            'cost': 'varies',
            'facilities': 'varies',
            'notes': 'Willow Springs / Cotter Mine Rd / Dubinky Wells all within 15 mi.',
            'access': 'Multiple',
        },
    },
    'day6_moab': {'inherit': 'day5_moab'},
    'day7_moab': {'inherit': 'day5_moab'},
}

# ---------------------------------------------------------------------------
# Per-day scheduling defaults (only overland days get the on-page scheduler).
# break_camp = HH:MM local; moving_mph = pure driving speed (no stops folded in).
# Speed bias: Day 2 / Day 3 are slower because of Eva Conover, Behind-the-Reef, etc.
# ---------------------------------------------------------------------------
SCHEDULE_DEFAULTS = {
    'day1_swell': {'break_camp': '09:00', 'moving_mph': 20},
    'day2_swell': {'break_camp': '08:30', 'moving_mph': 15},
    'day3_swell': {'break_camp': '08:30', 'moving_mph': 14},
    'day4_swell': {'break_camp': '09:00', 'moving_mph': 22},
}

# Per-POI "spur miles saved if skipped" overrides. These are round-trip miles
# that would be avoided if the stop is un-checked in the scheduler (e.g., an
# out-and-back detour that the main track drives to reach the POI). Values
# were derived from scripts/_spur_audit.py and hand-reviewed. Only POIs whose
# skip-savings exceed ~20 min at typical moving speed are worth listing here;
# anything smaller is noise at the fidelity we care about.
#
# When adding a new entry: run `py scripts\spur_audit.py`, confirm the spur
# mouth and apex look right against the GPX, and paste the "Spur length" value
# here (rounded to one decimal).
POI_SPUR_OVERRIDES = {
    'DP - Red Canyon':                15.3,  # Day 1 spur, mouth miles 29.04 -> 44.33
    'DP - Hidden Splendor Overlook':  19.7,  # Day 3 spur, mouth miles 146.55 -> 166.28
}

# Stops that get checked by default in the itinerary scheduler.
DEFAULT_CHECKED_BY_STATUS = {
    'primary':         True,
    'hike_candidate':  True,
    'conditional':     True,
    'backup':          False,
    'skip':            False,
    'logistics':       False,
    'unclassified':    False,
}

# Stop-time defaults. Tunable per-stop in the UI; this just seeds the inputs.
def _default_minutes(name, sym, status, note):
    n = (name or '').lower()
    s = (sym or '').lower()
    nl = (note or '').lower()
    # Specific named stops first (times = suggested on-trail dwell for scheduler; see slot-canyon-guide.md)
    if 'wild horse window' in n:
        # Published ~2 mi RT, easy, commonly 1–2 hr — use 90 min as mid estimate
        return 90
    if 'little wild horse canyon trail' in n:   return 120
    if 'little wild horse slot' in n:           return 0   # loop waypoint reference unless full hike
    if 'dp - crack canyon' == n:
        # Utah.com ~5 mi RT + 10 ft choke: ~3–4 hr typical; 210 min = 3.5 hr planner default
        return 210
    if 'dp - chute canyon' == n:
        # Partial OAB to first narrowing (~0.8 mi one-way per GCT) / easy wash — ~2–3 hr; not full 7.7 mi day hike
        return 150
    if 'eva conover' in n:                      return 60  # trail section
    if 'behind the reef' in n:                  return 75  # technical trail
    if 'tomsich butte' in n:                    return 45
    if 'lucky strike' in n:                     return 45
    if 'icebox' in n:                           return 30
    if 'loan warrior' in n or 'lone warrior' in n:
        # Petroglyph panel ~1.5 mi off the main trail; +15 min covers the
        # out-and-back spur drive on top of the ~20 min dwell at the panel.
        return 35
    if 'tunnel / freeway' in n:                 return 10
    if 'buckhorn wash petroglyphs' in n:        return 30
    if 'wedge overlook' in n:                   return 30
    if 'little grand canyon' in n:              return 20
    if 'head of sinbad' in n:                   return 25
    # Drive-by overrides take precedence over symbol defaults
    if 'drive-by' in nl or 'drive by' in nl:    return 5
    # By symbol type
    if s in ('mine', 'cave', 'building-24'):    return 30
    if s == 'natural-spring':                   return 15
    if s in ('cliff', 'stone', 'arch', 'bridge', 'petroglyph'): return 20
    if s in ('binoculars', 'attraction'):       return 15
    if s == 'water':                            return 15
    if s == 'off-road':                         return 30
    return 20


# ---------------------------------------------------------------------------
# Slice the main track for each Swell day
# ---------------------------------------------------------------------------
def _haversine_m(a, b):
    R = 6371000.0
    la1, lo1 = math.radians(a[0]), math.radians(a[1])
    la2, lo2 = math.radians(b[0]), math.radians(b[1])
    dlat = la2 - la1
    dlon = lo2 - lo1
    s = math.sin(dlat / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(s))

pts = main_track['points']
cum_mi = [0.0]
for i in range(1, len(pts)):
    cum_mi.append(cum_mi[-1] + _haversine_m(pts[i - 1], pts[i]) / 1609.344)


def slice_track(mi_lo, mi_hi):
    if mi_lo is None or mi_hi is None:
        return []
    i_lo = next((i for i, m in enumerate(cum_mi) if m >= mi_lo), 0)
    i_hi = next((i for i, m in enumerate(cum_mi) if m >= mi_hi), len(cum_mi) - 1)
    return pts[i_lo:i_hi + 1]


# ---------------------------------------------------------------------------
# Build per-day POI lists
# ---------------------------------------------------------------------------
def pois_for_day(mi_lo, mi_hi):
    if mi_lo is None or mi_hi is None:
        return []
    out = []
    seen = set()  # dedupe by (name, mile rounded)
    for w in ORDERED:
        mi = w.get('mile', -1)
        if mi is None:
            continue
        if not (mi_lo <= mi < mi_hi):
            continue
        nm = w.get('name') or ''
        key = (nm, round(mi, 2))
        if key in seen:
            continue
        seen.add(key)
        status_info = POI_STATUS.get(nm)
        if not status_info:
            # Generic handling: logistics, camps, etc.
            sym = w.get('sym') or ''
            if sym == 'campsite-24':
                continue  # camps handled separately
            if sym in ('fuel-24', 'city-24', 'toilets-24'):
                status = 'logistics'
                note = sym
            else:
                status = 'unclassified'
                note = ''
        else:
            status, note = status_info
        out.append({
            'name': nm,
            'lat': w['lat'], 'lon': w['lon'], 'ele': w.get('ele'),
            'mile': round(mi, 2),
            'dist_to_track_m': round(w.get('dist_to_track_m', 0), 1),
            'sym': w.get('sym'),
            'status': status,
            'note': note,
            'desc': (w.get('desc') or '').strip(),
            'spur_mi': POI_SPUR_OVERRIDES.get(nm, 0.0),
        })
    return out


# Day-0 (travel/staging) gets the pre-mile-0 waypoints (mile 0..2 range + any negatives)
# Actually our two staging POIs (Petroglyph Canyon Panel, Spirit Arch) are at mi 0.4 so they'll
# land in Day 1 window. Move them explicitly to Day 0.
DAY0_STAGE_NAMES = {'DP - Petroglyph Canyon Panel', 'DP - Spirit Arch'}
# Waypoints in the Day-0/Day-1 vicinity we want to suppress entirely (not shown on
# either day). 'San Rafael Reef Viewpoint' sits near I-70 but isn't actually
# accessible from the trip corridor -- drop it everywhere.
DAY01_SUPPRESS_NAMES = {'San Rafael Reef Viewpoint'}
ALL_PAYLOAD_DAYS = []
for d in DAYS:
    d_copy = dict(d)
    if d['id'] == 'day0_travel':
        # Add May 2 bonus POIs
        poi_list = []
        for w in ORDERED:
            if (w.get('name') or '') in DAY0_STAGE_NAMES:
                poi_list.append({
                    'name': w['name'],
                    'lat': w['lat'], 'lon': w['lon'], 'ele': w.get('ele'),
                    'mile': round(w.get('mile', 0), 2),
                    'dist_to_track_m': round(w.get('dist_to_track_m', 0), 1),
                    'sym': w.get('sym'),
                    'status': 'backup',
                    'note': 'May 2 bonus if arrive with daylight',
                    'desc': (w.get('desc') or '').strip(),
                })
        d_copy['pois'] = poi_list
    else:
        d_copy['pois'] = pois_for_day(d['mi_lo'], d['mi_hi'])
        # For Day 1, remove day-0 staging POIs (prevent duplication in Day 1 list)
        # and any globally-suppressed waypoints that live in the same mile window.
        if d['id'] == 'day1_swell':
            d_copy['pois'] = [
                p for p in d_copy['pois']
                if p['name'] not in DAY0_STAGE_NAMES
                and p['name'] not in DAY01_SUPPRESS_NAMES
            ]

    d_copy['track_points'] = slice_track(d.get('mi_lo'), d.get('mi_hi'))
    # campsite for this day (end-of-day camp for overnight days only)
    camp_spec = CAMPSITES.get(d['id'])
    if camp_spec and 'inherit' in camp_spec:
        camp_spec = CAMPSITES.get(camp_spec['inherit'])
    d_copy['camps'] = camp_spec or None

    # Scheduling annotations (only for days with SCHEDULE_DEFAULTS).
    sched = SCHEDULE_DEFAULTS.get(d['id'])
    if sched and d_copy['track_points']:
        first_pt = d_copy['track_points'][0]
        d_copy['schedule'] = {
            'break_camp_time': sched['break_camp'],
            'moving_mph':      sched['moving_mph'],
            'start_lat':       first_pt[0],
            'start_lon':       first_pt[1],
            'mi_lo':           d.get('mi_lo') or 0.0,
        }
        # Annotate scheduled-day POIs (so the UI has per-stop seeds even for backups).
        for p in d_copy['pois']:
            p['default_minutes'] = _default_minutes(p['name'], p.get('sym'), p['status'], p.get('note'))
            p['default_checked'] = DEFAULT_CHECKED_BY_STATUS.get(p['status'], False)

    ALL_PAYLOAD_DAYS.append(d_copy)

# ---------------------------------------------------------------------------
# Fuel plan payload (short version embedded; full is in planning/fuel_plan.md → fuel-plan.html)
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
    # alerts.weather.gov was retired in late 2023 / early 2024; use the office WWA / hazard pages instead.
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
    # The old /fire-restrictions-2/ path silently 302s to the ArcGIS hub root; use the deep-link to the actual restrictions page.
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

# ---------------------------------------------------------------------------
# Group size (counts only -- no names or contact info land in published artifacts)
# ---------------------------------------------------------------------------
GROUP_COUNTS = {
    'overland': 11,
    'moab': 7,
}

# ---------------------------------------------------------------------------
# Emit
# ---------------------------------------------------------------------------
payload = {
    'trip': {
        'title': '2026 San Rafael Swell Adventure + Moab',
        'dates': '2026-05-02 through 2026-05-10',
        'route_gpx_source': 'san-rafael-swell-adv-route-2025.gpx',
        'route_total_miles': round(TOTAL_MI, 2),
        'main_track_points': len(pts),
    },
    'group_counts': GROUP_COUNTS,
    'days': ALL_PAYLOAD_DAYS,
    'alternate_tracks': {
        'devils_racetrack': devils_racetrack,
        'freeway_access': freeway_access,
    },
    'fuel': FUEL_PLAN_SUMMARY,
    'realtime_links': REALTIME_LINKS,
    'generated_at': '2026-04-16',
}

out_path = PLAN / 'trip_data.json'
out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
print(f'Wrote {out_path} ({out_path.stat().st_size / 1024:.1f} KB)')
print(f'Days: {len(ALL_PAYLOAD_DAYS)}')
for d in ALL_PAYLOAD_DAYS:
    pois = d.get('pois') or []
    tp = d.get('track_points') or []
    print(f"  {d['id']:22s} {d['label']:45s} pois={len(pois):3d} track_pts={len(tp):5d}")
