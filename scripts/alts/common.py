"""Shared camp/pin data reused across alternate itineraries.

The alternates re-purpose several main-trip camp specs and add a few new
ones (Temple Mountain Townsite used as staging on May 2 for reverse-direction
options, the Crack-trailhead dispersed cluster used by Option D May 3, and
a primary-promoted Family Butte used by Options A and D as a Day-2 end
camp). Keeping these in one place keeps the alt modules compact.
"""
from __future__ import annotations

from copy import deepcopy

# Fuel + realtime payloads mirror the main trip so the Reference-parity
# sections (fuel table + live NWS links) still render on alt pages.
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


REALTIME_LINKS = [
    {'cat': 'Weather', 'label': 'NWS Green River', 'url': 'https://forecast.weather.gov/MapClick.php?lat=38.9953&lon=-110.1599'},
    {'cat': 'Weather', 'label': 'NWS Wedge Overlook area', 'url': 'https://forecast.weather.gov/MapClick.php?lat=39.0985&lon=-110.7850'},
    {'cat': 'Weather', 'label': 'NWS Temple Mountain', 'url': 'https://forecast.weather.gov/MapClick.php?lat=38.6530&lon=-110.6680'},
    {'cat': 'Weather', 'label': 'NWS Moab', 'url': 'https://forecast.weather.gov/MapClick.php?lat=38.5733&lon=-109.5498'},
    {'cat': 'Weather', 'label': 'NWS Dead Horse Point', 'url': 'https://forecast.weather.gov/MapClick.php?lat=38.4710&lon=-109.7450'},
    {'cat': 'Weather', 'label': 'NWS SLC active warnings (Swell)', 'url': 'https://www.weather.gov/slc/WWA'},
    {'cat': 'Weather', 'label': 'NWS GJT hazards (Moab)',          'url': 'https://www.weather.gov/gjt/hazards'},
    {'cat': 'Weather', 'label': 'NWS SLC flash-flood info',        'url': 'https://www.weather.gov/slc/flashflood'},
    {'cat': 'Roads', 'label': 'UDOT Traveler Info', 'url': 'https://www.udottraffic.utah.gov/'},
    {'cat': 'Roads', 'label': 'UDOT Region 4 news', 'url': 'https://udot.utah.gov/connect/category/region-four'},
    {'cat': 'Fire/Smoke', 'label': 'Utah Fire Info (official)', 'url': 'https://utahfireinfo.gov/'},
    {'cat': 'Water', 'label': 'USGS San Rafael River near Green River', 'url': 'https://waterdata.usgs.gov/monitoring-location/09328500/'},
    {'cat': 'Emergency', 'label': 'Emery County Sheriff (non-emerg)', 'url': 'tel:+14353812404'},
    {'cat': 'Emergency', 'label': 'Grand County Sheriff (Moab)', 'url': 'tel:+14352598115'},
    {'cat': 'Emergency', 'label': 'UT Highway Patrol (I-70)', 'url': 'tel:+18018873800'},
]


GROUP_COUNTS = {'overland': 11, 'moab': 7}


# ---------------------------------------------------------------------------
# Shared camp specs
# ---------------------------------------------------------------------------

def black_dragon_stage() -> dict:
    """Day-0 staging at Black Dragon (same as main day0_travel)."""
    return {
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
                     'from the trail start. 09:30-pavement-friendly for early leavers exiting Day 1.',
            'access': 'I-70 Exit 145 (Black Dragon); pull onto the flats just past the cattleguard.',
        },
        'tertiary': {
            'name': 'San Rafael Reef View Area (BLM pullout on I-70)',
            'lat': 38.92111, 'lon': -110.43187,
            'status': 'tertiary',
            'kind': 'dispersed',
            'cost': 'Free (BLM)',
            'facilities': 'None',
            'notes': 'Signed BLM view area ~1 mi SW of Black Dragon trailhead.',
            'access': 'I-70 EB between Exit 129 and Exit 145; "San Rafael Reef View Area" pullout.',
        },
    }


def wedge_overlook_camps() -> dict:
    """Wedge Overlook designated cluster + east-rim + Buckhorn fallback."""
    return {
        'primary': {
            'name': 'Wedge Overlook Campsite #5 (GPX) - cluster anchor (#3/#4/#5/#6/#7)',
            'lat': 39.12445, 'lon': -110.75133,
            'status': 'primary',
            'kind': 'designated_dispersed',
            'cost': '$15/site honor system',
            'facilities': 'None',
            'notes': 'First-come only. Tight #3-#7 cluster on the west rim. Scout ahead '
                     'during any Buckhorn stop; claim 3-4 adjacent sites for the group.',
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
                'notes': 'East-side rim site. Good sunrise exposure but farther from the iconic overlook.',
                'access': 'Wedge Rd east spur',
            },
            {
                'name': 'Wedge Overlook Camp #2 (GPX) - east-rim site',
                'lat': 39.11221, 'lon': -110.73341,
                'status': 'secondary',
                'kind': 'designated_dispersed',
                'cost': '$15/site honor system',
                'facilities': 'None',
                'notes': 'East-side rim site midway between #1 and the overlook.',
                'access': 'Wedge Rd east spur',
            },
            {
                'name': 'Wedge Overlook Campsite #8 (GPX) - southern outlier',
                'lat': 39.11674, 'lon': -110.75523,
                'status': 'secondary',
                'kind': 'designated_dispersed',
                'cost': '$15/site honor system',
                'facilities': 'None',
                'notes': 'Extends the cluster if we need one extra site, or stand-alone backup.',
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
            'notes': '32 sites + 7 group sites. First-come. ~8 km S of Wedge.',
            'access': 'Buckhorn Draw Rd',
        },
    }


def tomsich_camps() -> dict:
    """Tomsich Butte end-of-day camp (used as B Day 1 arrival)."""
    return {
        'primary': {
            'name': 'Tomsich Butte Camp (GPX)',
            'lat': 38.68282, 'lon': -110.98900,
            'status': 'primary',
            'kind': 'dispersed',
            'cost': 'Free (BLM)',
            'facilities': 'None',
            'notes': 'Open flat area near the uranium mine ruins and Hondu Arch trailhead.',
            'access': 'Tomsich Butte Rd at the mine area',
        },
        'secondary': {
            'name': 'Dispersed Camp near Tomsich (GPX "Camp")',
            'lat': 38.69237, 'lon': -110.99904,
            'status': 'secondary',
            'kind': 'dispersed',
            'cost': 'Free (BLM)',
            'facilities': 'None',
            'notes': 'Adjacent GPX-marked camp spot ~1 km NW of Tomsich Butte Camp.',
            'access': 'Tomsich Butte Rd',
        },
        'tertiary': {
            'name': 'Family Butte Dispersed Camping (GPX) - east fallback',
            'lat': 38.76868, 'lon': -110.83217,
            'status': 'tertiary',
            'kind': 'dispersed',
            'cost': 'Free (BLM)',
            'facilities': 'None',
            'notes': '~15 km NE of Tomsich. Use if the Tomsich area is crowded.',
            'access': 'Family Butte Rd spur',
        },
    }


def temple_mtn_camps() -> dict:
    """Temple Mtn Townsite + East Campground + track-end dispersed."""
    return {
        'primary': {
            'name': 'Temple Mountain Townsite - Site 1 (Group Site) (GPX)',
            'lat': 38.65606, 'lon': -110.66015,
            'status': 'primary',
            'kind': 'developed_fcfs',
            'cost': '$50/night',
            'facilities': 'Vault toilets, fire rings, tables, large shade structure',
            'notes': 'Group-capacity site; first-come only. Tuesday night very likely open.',
            'access': 'Temple Mtn Rd, Townsite Campground complex',
        },
        'secondary': {
            'name': 'Temple Mount East Campground (GPX)',
            'lat': 38.65770, 'lon': -110.66224,
            'status': 'secondary',
            'kind': 'developed_fcfs',
            'cost': '$15/site',
            'facilities': 'Vault toilets',
            'notes': '10-site loop, first-come. Split group across several sites if group site is taken.',
            'access': 'Temple Mtn Rd, E of the Townsite',
        },
        'tertiary': {
            'name': 'Dispersed "Camp" near track end (GPX)',
            'lat': 38.66075, 'lon': -110.64263,
            'status': 'tertiary',
            'kind': 'dispersed',
            'cost': 'Free (BLM)',
            'facilities': 'None',
            'notes': 'Primitive dispersed; closest GPX-marked camp to Behind-the-Reef exit.',
            'access': 'On-route near Temple Mtn area',
        },
    }


def temple_mtn_staging() -> dict:
    """Reverse-direction (B/D) Day 0 staging: Temple Mtn + Goblin Valley."""
    base = temple_mtn_camps()
    out = {
        'primary': dict(base['primary'], notes=base['primary']['notes']
                        + ' Used Friday May 1 night as staging for reverse-direction alternates.'),
        'secondary': dict(base['secondary']),
        'tertiary': {
            'name': 'Goblin Valley SP (reservable individual sites)',
            'lat': 38.57340, 'lon': -110.70300,
            'status': 'tertiary',
            'kind': 'developed_reserved',
            'cost': '$35-40/night',
            'facilities': 'Toilets, water, showers',
            'notes': 'Reservation strongly recommended on weekends. Use when Temple Mtn FCFS '
                     'sites are full on arrival Friday night.',
            'access': 'Hwy 24 -> Goblin Valley Rd W',
            'reserve_url': 'https://utahstateparks.reserveamerica.com',
        },
    }
    return out


def family_butte_primary_camps() -> dict:
    """Family Butte dispersed promoted to primary (A Day 2 / D Day 2 end)."""
    return {
        'primary': {
            'name': 'Family Butte Dispersed Camping (GPX)',
            'lat': 38.76868, 'lon': -110.83217,
            'status': 'primary',
            'kind': 'dispersed',
            'cost': 'Free (BLM)',
            'facilities': 'None (no toilets, no water)',
            'notes': 'GPX-marked open dispersed area, room for 6-8 vehicles. '
                     'First-come; group may need to spill to nearby Reds Canyon Rd pull-offs '
                     'if the butte fills up. Scout on arrival.',
            'access': 'Family Butte Rd spur, mid-route (NE of Tomsich)',
        },
        'secondary': {
            'name': 'Reds Canyon Rd dispersed pullouts (nearby overflow)',
            'lat': 38.75500, 'lon': -110.87500,
            'status': 'secondary',
            'kind': 'dispersed',
            'cost': 'Free (BLM)',
            'facilities': 'None',
            'notes': 'Scattered BLM pullouts along Reds Canyon Rd W/NW of Family Butte. '
                     'Use if the Family Butte dispersed area is full; fan out the group.',
            'access': 'Reds Canyon Rd',
        },
        'tertiary': {
            'name': 'Tomsich Butte Camp (push on to Day-3 start)',
            'lat': 38.68282, 'lon': -110.98900,
            'status': 'tertiary',
            'kind': 'dispersed',
            'cost': 'Free (BLM)',
            'facilities': 'None',
            'notes': 'Last-resort: push through to the main-trip Day-2 end camp. '
                     'Makes Day 3 short and Day 2 long.',
            'access': 'Tomsich Butte Rd at the mine area',
        },
    }


def crack_canyon_camps() -> dict:
    """Option D Day-1 cluster near Crack / Chute trailheads."""
    return {
        'primary': {
            'name': 'Dispersed Camping near Crack Canyon trailhead',
            'lat': 38.64423, 'lon': -110.73771,
            'status': 'primary',
            'kind': 'dispersed',
            'cost': 'Free (BLM)',
            'facilities': 'None (no toilets, no water)',
            'notes': 'Signed BLM dispersed camping pocket. '
                     'First-come; scout on arrival. Daylight arrival strongly preferred.',
            'access': 'Behind-the-Reef Rd S of Crack Canyon TH',
        },
        'secondary': {
            'name': 'Crack Canyon Trailhead (pockets near TH)',
            'lat': 38.64610, 'lon': -110.73390,
            'status': 'secondary',
            'kind': 'dispersed',
            'cost': 'Free (BLM)',
            'facilities': 'None',
            'notes': 'Small pullouts within walking distance of the Crack Canyon TH. '
                     'Useful backup if the main dispersed pocket fills.',
            'access': 'Crack Canyon TH road spur',
        },
        'tertiary': {
            'name': 'Camp Site waypoint (38.66000, -110.73253)',
            'lat': 38.66000, 'lon': -110.73253,
            'status': 'tertiary',
            'kind': 'dispersed',
            'cost': 'Free (BLM)',
            'facilities': 'None',
            'notes': 'GPX "Camp" waypoint ~1.8 km N of the primary; last-resort if both '
                     'closer options are full or unworkable. Scout before splitting the group.',
            'access': 'Behind-the-Reef Rd',
        },
    }


def sand_flats_moab_camps() -> dict:
    """Moab arrival camp: clustered first-come sites in Sand Flats (no group reservation)."""
    return {
        'primary': {
            'name': 'Sand Flats Recreation Area — adjacent FCFS sites (cluster)',
            'lat': 38.57563, 'lon': -109.52401,
            'status': 'primary',
            'kind': 'developed_fcfs',
            'cost': 'Day-use pass + per-night camping fee (pay fee station)',
            'facilities': 'Picnic tables, fire rings, pit toilets; no drinking water onsite',
            'notes': 'No group reservation: plan to snag several adjoining sites on the same loop '
                     '(or nearby loops) so the crew stays visual distance. Typical rule is '
                     'up to two vehicles parked at a numbered site **when everything fits**—'
                     'put tow rigs/trailers on their own pads when tandem parking is tight. '
                     'Spring Thu–Sat nights fill quickly; aim to arrive midday when possible.',
            'access': 'From Moab: 400 East -> Mill Creek Dr -> Sand Flats Rd to BLM/co-county booth',
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
            'cost': 'Free where signed — human-waste containment required',
            'facilities': 'No services; numbered posts — see BLM map',
            'notes': '~11–22 mi from Moab depending on spur. Camp only signed sites.',
            'access': 'Hwy 191 / SR 313 corridors north/northwest',
        },
    }


def dead_horse_camps() -> dict:
    return {
        'primary': {
            'name': 'Dead Horse Point SP - Wingate (May 7-9)',
            'lat': 38.4710, 'lon': -109.7450,
            'status': 'primary',
            'kind': 'developed_reserved',
            'cost': '$60/night',
            'facilities': 'Electric, vault toilets, no showers',
            'notes': 'Book 1 site for May 7-9. Max 8 ppl/site.',
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
            'notes': '59+ sites open each night.',
            'access': 'Same park, different loop',
            'reserve_url': 'https://utahstateparks.reserveamerica.com',
        },
        'tertiary': {
            'name': 'BLM designated dispersed (Cotter / Dubinky corridors)',
            'lat': 38.6500, 'lon': -109.7700,
            'status': 'tertiary',
            'kind': 'designated_dispersed',
            'cost': 'varies',
            'facilities': 'Signed dispersed pods — pack out waste per BLM postings',
            'notes': 'Use if Dead Horse Wingate unavailable; stay on posted pods only.',
            'access': 'North of Hwy 313 / Hwy 191 per BLM camping map',
        },
    }


def stayover_sinbad_camps() -> dict:
    """Option A Day 4 stay-over camp (extra Swell night)."""
    return {
        'primary': dict(temple_mtn_camps()['primary'],
                        notes='Stay-overs return here after Chute/Crack tactical hikes + '
                              'Head of Sinbad cluster; good launching point for May 7 '
                              'I-70 E to Moab / Sand Flats + an easy afternoon trail (e.g. Fins N Things).'),
        'secondary': {
            'name': 'Goblin Valley SP (reservable)',
            'lat': 38.57340, 'lon': -110.70300,
            'status': 'secondary',
            'kind': 'developed_reserved',
            'cost': '$35-40/night',
            'facilities': 'Toilets, water, showers',
            'notes': 'Good overnight if Temple Mtn is full; reservation recommended.',
            'access': 'Hwy 24 -> Goblin Valley Rd W',
            'reserve_url': 'https://utahstateparks.reserveamerica.com',
        },
        'tertiary': {
            'name': 'Hwy 24 dispersed pullouts (BLM)',
            'lat': 38.55000, 'lon': -110.71000,
            'status': 'tertiary',
            'kind': 'dispersed',
            'cost': 'Free (BLM)',
            'facilities': 'None',
            'notes': 'Scattered BLM pullouts off Hwy 24 between Temple Mtn Rd and Hanksville. '
                     'Use as last-resort; approximate coords -- scout daylight.',
            'access': 'Hwy 24',
        },
    }
