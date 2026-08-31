"""Single source of truth for trip identity.

Everything in this file is trip-specific. The rest of the pipeline reads from
here, so retargeting the app to a new route and new dates means editing this
module plus the day/camp/POI tables in ``build_trip_data.py`` -- not hunting
hardcoded strings through the HTML builders.

See README.md ("Retargeting to a new trip") for the full checklist.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Identity / branding
# ---------------------------------------------------------------------------
TRIP_TITLE = 'Washington Cascades Adventure Route'
TRIP_SUBTITLE = 'Gifford Pinchot National Forest loop'
TRIP_DATES_HUMAN = 'September 8-13, 2026'
TRIP_DATE_START = '2026-09-08'
TRIP_DATE_END = '2026-09-13'

# Short prefix used for JS globals and localStorage keys (window.__WCA_*).
# Keep it short, uppercase, and unique per trip so a browser that cached the
# previous trip's PWA can't collide with this one.
JS_PREFIX = 'WCA'

# Apple/Android home-screen short name (12 chars or so before truncation).
PWA_SHORT_NAME = 'WA Cascades'
PWA_TITLE = 'WA Cascades'

META_DESCRIPTION = (
    'Offline-first trip app for the September 8-13, 2026 Washington Cascades '
    'Adventure Route: a 325-mile Gifford Pinchot National Forest loop with '
    'daily itinerary, maps, campgrounds, fuel planning, weather and fire/closure tracking.'
)

# ---------------------------------------------------------------------------
# Source route
# ---------------------------------------------------------------------------
ROUTE_GPX_FILENAME = 'wa-cascades-adv-route-2025.gpx'
# <trk><name> of the track that defines route mileage. Waypoints are projected
# onto this track to get their "mile" value.
MAIN_TRACK_NAME = 'Washington Cascades Adventure Route'
# Tracks present in the source GPX that we deliberately do not use.
IGNORED_TRACK_NAMES = ('Pimlico Road / FS 7807',)

ROUTE_SOURCE_CREDIT = 'original route GPX'

# ---------------------------------------------------------------------------
# Offline map tiles
# ---------------------------------------------------------------------------
# Route bbox is lat 45.715..46.678, lon -122.009..-121.474. Padded west and
# north to keep Mount St Helens, Mount Rainier and the Randle/Packwood fuel
# stops on the offline basemap.
TILE_BBOX = {
    'lat_min': 45.55,
    'lat_max': 46.95,
    'lon_min': -122.45,
    'lon_max': -121.20,
}
TILE_ZOOMS = [7, 8, 9]
TILE_USER_AGENT = (
    'WashingtonCascadesTripBuilder/1.0 '
    '(personal trip planning; https://openstreetmap.org/copyright)'
)

# Fallback map centre when a day has no track points (roughly Takhlakh Lake).
MAP_FALLBACK_CENTER = (46.278, -121.598)
MAP_FALLBACK_ZOOM = 10

# ---------------------------------------------------------------------------
# Weather / alerts
# ---------------------------------------------------------------------------
NWS_ALERT_AREA = 'WA'
NWS_ALERT_LABEL = 'Live NWS Washington alerts'
NWS_OFFICE_LINKS = [
    ('NWS Portland (south Cascades / Gorge)', 'https://www.weather.gov/pqr'),
    ('NWS Seattle (Rainier / north)', 'https://www.weather.gov/sew'),
]

# ---------------------------------------------------------------------------
# Group
# ---------------------------------------------------------------------------
# people_estimated is an assumption pending a final head count; vehicles is
# the number the trip is actually planned around.
GROUP_COUNTS = {
    'vehicles': 6,
    'people_estimated': 12,
    'people_confirmed': False,
}

# ---------------------------------------------------------------------------
# Start / end logistics
# ---------------------------------------------------------------------------
MEET_POINT = {
    'name': 'Sinclair Stinker Station, Nampa, ID',
    'address': '1902 N Franklin Blvd, Nampa, ID 83687',
    'lat': 43.6013,
    'lon': -116.5645,
    'gather_time': '8:00 AM MDT',
    'depart_time': '8:15 AM MDT',
}

# Route mile 0 (Carson, WA) -- where the loop begins.
ROUTE_START = {'lat': 45.71518, 'lon': -121.82814, 'label': 'Carson, WA (Wind River Rd)'}
# Route end (Triangle Pass) -- the loop closes ~20 road miles from Carson.
ROUTE_END = {'lat': 45.78484, 'lon': -121.73885, 'label': 'Triangle Pass'}

# ---------------------------------------------------------------------------
# Emergency / agency contacts (public numbers only -- never participant info)
# ---------------------------------------------------------------------------
EMERGENCY_CONTACTS = [
    {'label': 'Emergency (all areas)', 'value': '911', 'tel': 'tel:911'},
    {'label': 'Skamania County Sheriff (Gorge, Wind River, south forest)',
     'value': '(509) 427-9490', 'tel': 'tel:+15094279490'},
    {'label': 'Lewis County dispatch, non-emergency (Randle, Packwood, Cispus)',
     'value': '(360) 740-1105', 'tel': 'tel:+13607401105'},
    {'label': 'Mt Adams Ranger District (Trout Lake)',
     'value': '(509) 395-3402', 'tel': 'tel:+15093953402'},
    {'label': 'Cowlitz Valley Ranger District (Randle)',
     'value': '(360) 497-1103', 'tel': 'tel:+13604971103'},
    {'label': 'Gifford Pinchot National Forest HQ',
     'value': '(360) 891-5000', 'tel': 'tel:+13608915000'},
]

HOSPITALS = [
    {'name': 'Arbor Health - Morton Hospital (ER, critical access)',
     'detail': '521 Adams Ave, Morton WA - nearest ER to Randle, Packwood and the Cispus corridor',
     'value': '(360) 496-5112', 'tel': 'tel:+13604965112',
     'lat': 46.5590, 'lon': -122.2760},
    {'name': 'Skyline Hospital (ER, critical access)',
     'detail': '211 Skyline Dr, White Salmon WA - nearest ER to the Gorge, Carson and Trout Lake',
     'value': '(509) 493-1101', 'tel': 'tel:+15094931101',
     'lat': 45.7300, 'lon': -121.4880},
    {'name': 'Arbor Health - Packwood Clinic (clinic, not an ER)',
     'detail': 'Weekday clinic hours only - call ahead',
     'value': '(360) 496-3777', 'tel': 'tel:+13604963777',
     'lat': 46.6080, 'lon': -121.6720},
    {'name': 'Arbor Health - Randle Clinic (clinic, not an ER)',
     'detail': 'Weekday clinic hours only - call ahead',
     'value': '(360) 497-3333', 'tel': 'tel:+13604973333',
     'lat': 46.5320, 'lon': -121.9570},
]

# Areas where cell coverage is unreliable. Rendered on the reference page.
CELL_DEAD_ZONES = [
    'Wind River / Panther Creek corridor (mi 0-20) - patchy, none above the High Bridge',
    'Indian Heaven / Sawtooth Berry Fields (mi 44-60) - essentially none',
    'Babyshoe Pass and the Midway High Lakes (mi 60-92) - none',
    'Upper Cispus / Walupt Lake (mi 95-141) - none',
    'High Rock Lookout spur (mi 170-185) - none until back on US 12',
    'Burley Mountain / Pinto Rock / Elk Pass (mi 230-265) - none',
    'Lewis River / Curly Creek (mi 270-300) - none',
    'Usable signal: Carson, Trout Lake (detour), Packwood, Randle, US 12 corridor',
]

SATELLITE_COMMS_NOTE = (
    'The group carries satellite communication. Confirm before departure who has a device, '
    'share the check-in schedule, and load the emergency contacts above into it. '
    'Assume no cellular coverage anywhere between Carson and Packwood.'
)

# ---------------------------------------------------------------------------
# Permits and passes
# ---------------------------------------------------------------------------
PERMITS_NOTE = [
    ('Northwest Forest Pass',
     'Required to park at most developed Gifford Pinchot trailheads, including High Rock, '
     'Council Bluff, Langfield Falls and Falls Creek. $5/day or $30/year per vehicle. '
     'An America the Beautiful interagency pass also covers it. Every vehicle that parks '
     'at a trailhead needs its own pass displayed.'),
    ('Campground fees',
     'Reservable Gifford Pinchot campgrounds are booked through Recreation.gov. '
     'First-come sites take cash or card at the fee tube depending on the site. '
     'Bring small bills.'),
    ('Wilderness',
     'No permit is needed for day hiking the trails on this route. Goat Rocks and Indian '
     'Heaven wilderness areas border the route, and self-issue permits apply if anyone '
     'walks in overnight.'),
    ('Dispersed camping',
     'Free on most Gifford Pinchot roads outside developed campgrounds and posted closures. '
     'Use existing sites, camp 100+ ft from water, and check current fire restrictions '
     'before any campfire.'),
]
