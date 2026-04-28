"""Shared library for building a consolidated trip_data JSON payload.

This module factors out the pieces previously embedded in
``scripts/build_trip_data.py`` so the main itinerary AND each alternate
itinerary (A / B / D) can share POI metadata, scheduling defaults, track
slicing, and POI minute heuristics.

Public entry points:

* ``load_route(plan_dir)`` -- one-time load of ``route_analysis.json`` +
  ``route_tracks.json`` into a dict used by every subsequent call.
* ``build_payload(...)`` -- turns a ``days_spec`` list (same shape as the
  current ``DAYS`` with optional ``track_segments`` for alternates) plus
  camp data + schedule defaults into the JSON payload written to disk.

POI catalog (``POI_STATUS``, ``POI_SPUR_OVERRIDES``, ``default_minutes``) is
defined once here and shared by both main and alternates -- the alternates
just re-key the same POI facts onto new day boundaries.
"""
from __future__ import annotations
import json
import math
import pathlib
from typing import Any


# ---------------------------------------------------------------------------
# POI catalog
# ---------------------------------------------------------------------------
# Explicit POI status map from planning/poi_decisions.md (manual transcription)
# status: primary | backup | skip | conditional | hike_candidate
POI_STATUS: dict[str, tuple[str, str]] = {
    # Day 0 / May 2 staging POIs (Black Dragon arrival) and bonuses
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
    'River crossing':                      ('primary',  'Fuller Bottom ford of the San Rafael River (Upper San Rafael River WMA, BLM Fuller Bottom road = NF-3516 / BLM 6767, becomes Little Wedge Road / BLM 629 south of the crossing). Added per group request -- water crossings desirable for overlanders.'),
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
}


# Per-POI "spur miles saved if skipped" overrides. These are round-trip miles
# that would be avoided if the stop is un-checked in the scheduler.
POI_SPUR_OVERRIDES: dict[str, float] = {
    'DP - Red Canyon':                15.3,
    'DP - Hidden Splendor Overlook':  19.7,
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


# Day-0 staging bonus POIs (pre-mile-0 waypoints we expose on the travel day).
DAY0_STAGE_NAMES: set[str] = {'DP - Petroglyph Canyon Panel', 'DP - Spirit Arch'}
# Waypoints we want to suppress entirely (not surfaced on any day).
SUPPRESS_NAMES: set[str] = {'San Rafael Reef Viewpoint'}


def default_minutes(name: str, sym: str, status: str, note: str) -> int:
    """Stop-time default seeds for the itinerary scheduler inputs."""
    n = (name or '').lower()
    s = (sym or '').lower()
    nl = (note or '').lower()
    if 'wild horse window' in n:
        return 90
    if 'little wild horse canyon trail' in n:   return 120
    if 'little wild horse slot' in n:           return 0
    if 'dp - crack canyon' == n:
        return 210
    if 'dp - chute canyon' == n:
        return 150
    if 'eva conover' in n:                      return 60
    if 'behind the reef' in n:                  return 75
    if 'tomsich butte' in n:                    return 45
    if 'lucky strike' in n:                     return 45
    if 'icebox' in n:                           return 30
    if 'loan warrior' in n or 'lone warrior' in n:
        return 35
    if 'tunnel / freeway' in n:                 return 10
    if 'buckhorn wash petroglyphs' in n:        return 30
    if 'wedge overlook' in n:                   return 30
    if 'little grand canyon' in n:              return 20
    if 'head of sinbad' in n:                   return 25
    if 'drive-by' in nl or 'drive by' in nl:    return 5
    if s in ('mine', 'cave', 'building-24'):    return 30
    if s == 'natural-spring':                   return 15
    if s in ('cliff', 'stone', 'arch', 'bridge', 'petroglyph'): return 20
    if s in ('binoculars', 'attraction'):       return 15
    if s == 'water':                            return 15
    if s == 'off-road':                         return 30
    return 20


# ---------------------------------------------------------------------------
# Route loading + geometry helpers
# ---------------------------------------------------------------------------
def _haversine_m(a, b):
    R = 6371000.0
    la1, lo1 = math.radians(a[0]), math.radians(a[1])
    la2, lo2 = math.radians(b[0]), math.radians(b[1])
    dlat = la2 - la1
    dlon = lo2 - lo1
    s = math.sin(dlat / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(s))


def load_highway_tracks(planning_dir: pathlib.Path) -> dict[str, Any]:
    """Load optional OSRM polylines for May 1–2 highway legs (``planning/highway_tracks.json``)."""
    p = planning_dir / 'highway_tracks.json'
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding='utf-8'))


def load_route(plan_dir: pathlib.Path) -> dict[str, Any]:
    """Load route_analysis.json + route_tracks.json and precompute cum_mi."""
    analysis = json.loads((plan_dir / 'route_analysis.json').read_text(encoding='utf-8'))
    tracks = json.loads((plan_dir / 'route_tracks.json').read_text(encoding='utf-8'))

    main_track = next(t for t in tracks if t['name'] == 'San Rafael Swell Adventure Route')
    freeway_access = next((t for t in tracks if t['name'] == 'Freeway Access'), None)
    devils_racetrack = next((t for t in tracks if t['name'] == 'Devils Racetrack Alternate Route'), None)

    pts = main_track['points']
    cum_mi = [0.0]
    for i in range(1, len(pts)):
        cum_mi.append(cum_mi[-1] + _haversine_m(pts[i - 1], pts[i]) / 1609.344)

    ordered = analysis['waypoints_ordered']
    by_name: dict[str, list[dict]] = {}
    for w in ordered:
        nm = w.get('name') or ''
        by_name.setdefault(nm, []).append(w)

    return {
        'main_track': main_track,
        'main_points': pts,
        'cum_mi': cum_mi,
        'freeway_access': freeway_access,
        'devils_racetrack': devils_racetrack,
        'ordered': ordered,
        'by_name': by_name,
        'total_mi': analysis['track_miles'],
    }


def slice_track(route: dict[str, Any], mi_lo: float | None, mi_hi: float | None) -> list[list[float]]:
    """Return main-track points whose cumulative-mile values fall in [mi_lo, mi_hi]."""
    if mi_lo is None or mi_hi is None:
        return []
    pts = route['main_points']
    cum_mi = route['cum_mi']
    i_lo = next((i for i, m in enumerate(cum_mi) if m >= mi_lo), 0)
    i_hi = next((i for i, m in enumerate(cum_mi) if m >= mi_hi), len(cum_mi) - 1)
    return pts[i_lo:i_hi + 1]


def build_day_track(route: dict[str, Any], segments: list[dict]) -> list[list[float]]:
    """Concatenate track slices (optionally reversed) into one day polyline.

    ``segments`` is a list of ``{'mi_lo': ..., 'mi_hi': ..., 'reverse': bool}``.
    Duplicate boundary points between consecutive segments are elided.
    """
    out: list[list[float]] = []
    for seg in segments:
        sliced = slice_track(route, seg.get('mi_lo'), seg.get('mi_hi'))
        if seg.get('reverse'):
            sliced = list(reversed(sliced))
        if out and sliced and tuple(sliced[0]) == tuple(out[-1]):
            sliced = sliced[1:]
        out.extend(sliced)
    return out


# ---------------------------------------------------------------------------
# POI assembly
# ---------------------------------------------------------------------------
def _waypoint_to_poi(w: dict, route: dict, day_mile: float, status_info: tuple[str, str] | None) -> dict | None:
    """Convert a raw waypoint into the POI dict consumed by HTML/GPX builders.

    ``day_mile`` is the mile-along-driven-day value used by the scheduler
    (monotonically increasing from 0 at the day's start, regardless of whether
    the day runs forward or reverse along the master track).
    """
    nm = w.get('name') or ''
    if status_info is None:
        sym = w.get('sym') or ''
        if sym == 'campsite-24':
            return None
        if sym in ('fuel-24', 'city-24', 'toilets-24'):
            status = 'logistics'
            note = sym
        else:
            status = 'unclassified'
            note = ''
    else:
        status, note = status_info
    return {
        'name': nm,
        'lat': w['lat'], 'lon': w['lon'], 'ele': w.get('ele'),
        'mile': round(day_mile, 2),
        'dist_to_track_m': round(w.get('dist_to_track_m', 0), 1),
        'sym': w.get('sym'),
        'status': status,
        'note': note,
        'desc': (w.get('desc') or '').strip(),
        'spur_mi': POI_SPUR_OVERRIDES.get(nm, 0.0),
    }


def pois_for_segments(
    route: dict[str, Any],
    segments: list[dict],
    poi_status: dict[str, tuple[str, str]],
    suppress_names: set[str] | None = None,
    extra_status: dict[str, tuple[str, str]] | None = None,
    use_day_mi: bool = True,
) -> list[dict]:
    """Collect POIs covered by a list of mile segments in driven order.

    When ``use_day_mi`` is True (default; used by alternates including any
    reverse/multi-segment days), each POI's ``mile`` is recalculated as
    mile-along-the-day -- starting at 0 for the first segment and accumulating
    across segments -- so the HTML scheduler's ``mile - prevMile`` leg math
    stays correct regardless of master-track direction.

    When ``use_day_mi`` is False, POIs keep their absolute ``mile`` as
    measured along the master track (legacy behavior used by the main
    forward-only trip so its trip_data.json remains byte-identical to the
    pre-refactor output).
    """
    suppress_names = suppress_names or set()
    extra_status = extra_status or {}
    out: list[dict] = []
    seen: set[tuple[str, float]] = set()
    running_day_mi = 0.0
    for seg in segments:
        mi_lo = seg.get('mi_lo')
        mi_hi = seg.get('mi_hi')
        if mi_lo is None or mi_hi is None:
            continue
        seg_len = max(0.0, mi_hi - mi_lo)
        reverse = bool(seg.get('reverse'))
        in_win = []
        for w in route['ordered']:
            mi = w.get('mile')
            if mi is None:
                continue
            if not (mi_lo <= mi < mi_hi):
                continue
            in_win.append(w)
        in_win.sort(key=lambda w: -(w['mile']) if reverse else (w['mile']))
        for w in in_win:
            nm = w.get('name') or ''
            if nm in suppress_names:
                continue
            raw_mi = w['mile']
            if use_day_mi:
                off = (mi_hi - raw_mi) if reverse else (raw_mi - mi_lo)
                emit_mi = running_day_mi + off
            else:
                emit_mi = raw_mi
            key = (nm, round(emit_mi, 2))
            if key in seen:
                continue
            seen.add(key)
            status_info = extra_status.get(nm) or poi_status.get(nm)
            poi = _waypoint_to_poi(w, route, emit_mi, status_info)
            if poi is not None:
                out.append(poi)
        running_day_mi += seg_len
    return out


# ---------------------------------------------------------------------------
# Day payload assembly
# ---------------------------------------------------------------------------
def _resolve_camp(camp_spec: Any, camp_data: dict[str, Any] | None) -> Any:
    """Expand ``{'inherit': key}`` to the referenced camp dict."""
    if isinstance(camp_spec, dict) and 'inherit' in camp_spec:
        ref = camp_spec['inherit']
        if camp_data and ref in camp_data:
            return camp_data[ref]
    return camp_spec


def build_payload(
    *,
    days_spec: list[dict],
    camp_data: dict[str, Any],
    schedule_defaults: dict[str, dict],
    route: dict[str, Any],
    trip_meta: dict[str, Any],
    group_counts: dict[str, int],
    fuel_plan: dict[str, Any],
    realtime_links: list[dict[str, str]],
    generated_at: str,
    day0_stage_names: set[str] | None = None,
    suppress_names: set[str] | None = None,
    poi_status: dict[str, tuple[str, str]] | None = None,
    alternate_tracks: dict[str, Any] | None = None,
    intro_html: str | None = None,
    include_alternate_tracks: bool = True,
) -> dict[str, Any]:
    """Build a full trip-data payload from a days-spec + camp + schedule set.

    ``days_spec`` items mirror the original ``DAYS`` list with optional fields:
      * ``track_segments``: list of ``{mi_lo, mi_hi, reverse}``. If present,
        takes precedence over the legacy ``mi_lo/mi_hi`` scalar fields when
        both POIs and the track polyline are computed.
      * ``poi_names_override``: optional explicit list of POI names for the
        day. Short-circuits the mile-window POI extraction.
      * ``synthetic_pois`` / ``synthetic_track_points``: injected POIs or
        lat/lon polylines (e.g. May 1–2 highway legs); not copied verbatim into
        output day dicts — polylines become ``track_points``.
    """
    poi_status = poi_status or POI_STATUS
    day0_stage_names = day0_stage_names or set()
    suppress_names = suppress_names or set()

    out_days: list[dict] = []
    for d in days_spec:
        d_copy = {k: v for k, v in d.items() if k not in (
            'track_segments', 'poi_names_override', 'poi_extra_status', 'synthetic_pois',
            'synthetic_track_points',
        )}

        # Determine the segment set: explicit > legacy mi_lo/mi_hi.
        # `legacy_window` signals the main-trip forward-only case where we
        # synthesized a single segment from scalar mi_lo/mi_hi; in that mode
        # POIs keep their absolute master-track mileage so trip_data.json
        # stays byte-identical to the pre-refactor output.
        segments = d.get('track_segments')
        legacy_window = False
        if not segments and d.get('mi_lo') is not None and d.get('mi_hi') is not None:
            segments = [{'mi_lo': d['mi_lo'], 'mi_hi': d['mi_hi'], 'reverse': False}]
            legacy_window = True
        segments = segments or []

        # POIs.
        if d.get('synthetic_pois') is not None:
            d_copy['pois'] = [dict(p) for p in d['synthetic_pois']]
        elif d['id'] == 'day0_travel' or d.get('include_day0_staging_pois'):
            # Day-0 staging days only surface the pre-mile-0 bonus POIs,
            # tagged as backup (light blue "bonus if arrive with daylight").
            poi_list = []
            for w in route['ordered']:
                if (w.get('name') or '') in day0_stage_names:
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
        elif d.get('poi_names_override') is not None:
            # Explicit POI list: emit them in the given order, renumbering
            # ``mile`` as day-mile (0, 1, 2, ...) so the scheduler leg math
            # still works. Callers use this for Moab / transit days that
            # don't map onto the main track.
            names = d['poi_names_override']
            poi_list = []
            for idx, nm in enumerate(names):
                w_list = route['by_name'].get(nm)
                if not w_list:
                    continue
                w = w_list[0]
                status_info = (d.get('poi_extra_status') or {}).get(nm) or poi_status.get(nm)
                poi = _waypoint_to_poi(w, route, float(idx), status_info)
                if poi is not None:
                    poi_list.append(poi)
            d_copy['pois'] = poi_list
        else:
            d_copy['pois'] = pois_for_segments(
                route, segments, poi_status,
                suppress_names=day0_stage_names | suppress_names,
                extra_status=d.get('poi_extra_status'),
                use_day_mi=not legacy_window,
            )

        # Track polyline for this day (Swell segments, or optional highway polyline).
        synth = d.get('synthetic_track_points')
        if synth:
            d_copy['track_points'] = [[float(p[0]), float(p[1])] for p in synth]
        elif segments:
            d_copy['track_points'] = build_day_track(route, segments)
        else:
            d_copy['track_points'] = []

        # Camp selection.
        camp_key = d.get('camp_key', d['id'])
        camp_spec = _resolve_camp(camp_data.get(camp_key), camp_data)
        d_copy['camps'] = camp_spec or None

        # Schedule annotations (only for days that opt into it).
        sched = schedule_defaults.get(d['id'])
        if sched and d_copy['track_points']:
            first_pt = d_copy['track_points'][0]
            # ``mi_lo`` here is day-mile = 0 when using the new
            # segment-based model (POIs are already renumbered), or the
            # legacy raw-mile offset for the main trip.
            if d.get('track_segments'):
                mi_lo = 0.0
            else:
                mi_lo = d.get('mi_lo') or 0.0
            d_copy['schedule'] = {
                'break_camp_time': sched['break_camp'],
                'moving_mph':      sched['moving_mph'],
                'start_lat':       first_pt[0],
                'start_lon':       first_pt[1],
                'mi_lo':           mi_lo,
            }
            for p in d_copy['pois']:
                p['default_minutes'] = default_minutes(p['name'], p.get('sym'), p['status'], p.get('note'))
                p['default_checked'] = DEFAULT_CHECKED_BY_STATUS.get(p['status'], False)

        out_days.append(d_copy)

    payload: dict[str, Any] = {
        'trip': trip_meta,
        'group_counts': group_counts,
        'days': out_days,
        'alternate_tracks': (
            {
                'devils_racetrack': route.get('devils_racetrack'),
                'freeway_access': route.get('freeway_access'),
            }
            if include_alternate_tracks else {}
        ),
        'fuel': fuel_plan,
        'realtime_links': realtime_links,
        'generated_at': generated_at,
    }
    if alternate_tracks is not None:
        payload['alternate_tracks'] = alternate_tracks
    if intro_html:
        payload['intro_html'] = intro_html
    return payload


def write_payload(payload: dict[str, Any], out_path: pathlib.Path) -> None:
    """Write a payload to disk in the same pretty-printed format as before."""
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')


def print_payload_summary(payload: dict[str, Any], label: str) -> None:
    days = payload.get('days') or []
    print(f'{label}: {len(days)} days')
    for d in days:
        pois = d.get('pois') or []
        tp = d.get('track_points') or []
        print(f"  {d['id']:22s} {d['label']:55s} pois={len(pois):3d} track_pts={len(tp):5d}")
