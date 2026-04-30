#!/usr/bin/env python3
"""Fetch RR4W KML for Moab trails and write planning/moab_rr4w_geometry.json.

Re-run when RR4W updates a trail, then commit the JSON. Builds stay offline/deterministic.

Usage:
  py -3 scripts/import_rr4w_moab_kml.py
  py -3 scripts/import_rr4w_moab_kml.py --from-dir planning

Trails **37** (Hell's) and **38** (Top of the World) use GPX tracks from
``planning/hell_s_revenge_kmz.gpx`` and ``planning/top-of-the-world-2024.gpx``
when those files exist (Gaia / field recordings); RR4W KML is still used for
trail **44** and for metadata links on 37/38.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import re
import urllib.request
import xml.etree.ElementTree as ET

PLAN = pathlib.Path(__file__).resolve().parent.parent / 'planning'
OUT_PATH = PLAN / 'moab_rr4w_geometry.json'

# Field / Gaia GPX replaces KML-derived polylines for these RR4W ids (full track in JSON; HTML maps decimate).
GPX_TRACK_OVERRIDES: dict[str, pathlib.Path] = {
    '37': PLAN / 'hell_s_revenge_kmz.gpx',
    '38': PLAN / 'top-of-the-world-2024.gpx',
}

TRAILS = {
    '37': {
        'display_name': "Hell's Revenge — Tip-Toe Trip",
        'moab_trails_anchor': 'moab-trails.html#hell-tip-toe',
        'rating': '6 (RR4W Tip-Toe baseline)',
        'length_mi': '~16 total / ~12 off highway (RR4W)',
        'tires_min': '33″+ (RR4W listing)',
        'notes': 'Sand Flats fee area; bypass-heavy weekday flavor of Hell’s Revenge.',
    },
    '44': {
        'display_name': 'Wipe-Out Hill',
        'moab_trails_anchor': 'moab-trails.html#wipe-out-hill',
        'rating': 'RR4W listing',
        'length_mi': 'See RR4W trail page',
        'tires_min': 'See RR4W trail page',
        'notes': 'Tusher / Potash corridor context on moab-trails.html.',
    },
    '38': {
        'display_name': 'Top of the World',
        'moab_trails_anchor': 'moab-trails.html#top-of-the-world',
        'rating': 'RR4W listing',
        'length_mi': 'See RR4W trail page',
        'tires_min': 'See RR4W trail page',
        'notes': 'Potash Rd (SR 279) approach; do not confuse with “Where Eagles Dare” add-on.',
    },
}


def _local(tag: str) -> str:
    if tag.startswith('{'):
        return tag.split('}', 1)[1]
    return tag


def _text(el: ET.Element | None) -> str:
    if el is None or el.text is None:
        return ''
    return el.text.strip()


def _parse_coord_triplets(blob: str) -> list[tuple[float, float]]:
    """KML uses whitespace-separated ``lon,lat,alt`` groups (comma only inside each group)."""
    pts: list[tuple[float, float]] = []
    for triplet in re.split(r'\s+', blob.strip()):
        if not triplet:
            continue
        parts = triplet.split(',')
        if len(parts) < 2:
            continue
        lon, lat = float(parts[0]), float(parts[1])
        pts.append((lat, lon))
    return pts


def _iter_placemarks(root: ET.Element):
    for el in root.iter():
        if _local(el.tag) == 'Placemark':
            yield el


def _placemark_lines_and_point(pm: ET.Element) -> tuple[list[list[tuple[float, float]]], tuple[float, float, str] | None]:
    name = ''
    for ch in pm:
        if _local(ch.tag) == 'name':
            name = _text(ch)
            break
    lines: list[list[tuple[float, float]]] = []
    point: tuple[float, float, str] | None = None
    for ch in pm.iter():
        tag = _local(ch.tag)
        if tag == 'LineString':
            for coord in ch.iter():
                if _local(coord.tag) == 'coordinates':
                    raw = _text(coord)
                    if raw:
                        seg = _parse_coord_triplets(raw)
                        if seg:
                            lines.append(seg)
        if tag == 'Point':
            for coord in ch.iter():
                if _local(coord.tag) == 'coordinates':
                    raw = _text(coord)
                    if raw:
                        tri = _parse_coord_triplets(raw)
                        if tri:
                            lat, lon = tri[0]
                            point = (lat, lon, name or 'Waypoint')
    return lines, point


def _concat_lines(lines: list[list[tuple[float, float]]]) -> list[list[float]]:
    """Naive concat (legacy); prefer ``_build_track_from_kml_segments`` for RR4W exports."""
    out: list[list[float]] = []
    for seg in lines:
        if not seg:
            continue
        if out and seg and (out[-1][0], out[-1][1]) == (seg[0][0], seg[0][1]):
            seg = seg[1:]
        for lat, lon in seg:
            out.append([lat, lon])
    return out


def _haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    r = 6371000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dphi = math.radians(b[0] - a[0])
    dlmb = math.radians(b[1] - a[1])
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(h)))


def _collect_linestring_segments(root: ET.Element) -> list[list[tuple[float, float]]]:
    """Each KML LineString becomes one segment (RR4W often uses many disjoint LineStrings per trail)."""
    segments: list[list[tuple[float, float]]] = []
    for pm in _iter_placemarks(root):
        lines, _pt = _placemark_lines_and_point(pm)
        for ln in lines:
            if len(ln) >= 2:
                segments.append(ln)
    return segments


def _greedy_chain_segments(
    segments: list[list[tuple[float, float]]],
    max_join_m: float = 1200.0,
) -> list[list[float]]:
    """Chain segments by nearest endpoint to reduce bogus long connectors from document order."""
    segs = [list(s) for s in segments if len(s) >= 2]
    if not segs:
        return []
    segs.sort(key=len, reverse=True)
    chain = segs.pop(0)
    out: list[list[float]] = [[float(lat), float(lon)] for lat, lon in chain]
    while segs:
        best_j = -1
        best_rev = False
        best_d = float('inf')
        end = (out[-1][0], out[-1][1])
        for j, seg in enumerate(segs):
            d_fwd = _haversine_m(end, seg[0])
            d_rev = _haversine_m(end, seg[-1])
            if d_fwd < best_d:
                best_d, best_j, best_rev = d_fwd, j, False
            if d_rev < best_d:
                best_d, best_j, best_rev = d_rev, j, True
        if best_j < 0 or best_d > max_join_m:
            break
        seg = segs.pop(best_j)
        if best_rev:
            seg.reverse()
        if out and (out[-1][0], out[-1][1]) == (seg[0][0], seg[0][1]):
            seg = seg[1:]
        for lat, lon in seg:
            out.append([float(lat), float(lon)])
    return out


def _longest_run_without_long_edges(pts: list[list[float]], max_edge_m: float = 700.0) -> list[list[float]]:
    """Split where consecutive vertices jump farther than ``max_edge_m``; keep the longest contiguous run."""
    if len(pts) < 2:
        return pts
    runs: list[list[list[float]]] = []
    cur: list[list[float]] = [pts[0]]
    for i in range(1, len(pts)):
        d = _haversine_m((cur[-1][0], cur[-1][1]), (pts[i][0], pts[i][1]))
        if d > max_edge_m:
            runs.append(cur)
            cur = [pts[i]]
        else:
            cur.append(pts[i])
    runs.append(cur)
    return max(runs, key=len)


def _build_track_from_kml_segments(root: ET.Element) -> list[list[float]]:
    segs = _collect_linestring_segments(root)
    merged = _greedy_chain_segments(segs, max_join_m=1200.0)
    return _longest_run_without_long_edges(merged, max_edge_m=700.0)


def _snap_dist_m(latlon: tuple[float, float], track: list[list[float]]) -> float:
    if not track:
        return 0.0
    best = float('inf')
    for i in range(len(track) - 1):
        a = (track[i][0], track[i][1])
        b = (track[i + 1][0], track[i + 1][1])
        d = min(_haversine_m(latlon, a), _haversine_m(latlon, b))
        best = min(best, d)
    return round(best, 1)


def build_pois_for_trail(
    trail_id: str,
    track: list[list[float]],
    kml_points: list[tuple[float, float, str]],
    meta: dict,
) -> list[dict]:
    pois: list[dict] = []
    used_names: set[str] = set()

    def add_poi(lat: float, lon: float, name: str, map_kind: str, mile: float, status: str = 'primary'):
        d_m = _snap_dist_m((lat, lon), track)
        pois.append({
            'name': name,
            'lat': lat,
            'lon': lon,
            'mile': mile,
            'dist_to_track_m': d_m,
            'sym': 'rr4w-landmark' if map_kind == 'trail_poi' else 'trailhead',
            'status': status,
            'note': f'RR4W trail {trail_id}',
            'desc': '',
            'map_kind': map_kind,
        })

    for lat, lon, nm in kml_points:
        if nm.strip().lower() in ('start', 'trailhead', 'trail head'):
            mk = 'trailhead'
        else:
            mk = 'trail_poi'
        label = nm.strip() or 'Landmark'
        if label in used_names:
            label = f'{label} ({len(used_names)})'
        used_names.add(label)
        add_poi(lat, lon, label, mk, 0.05 * len(pois))

    if not any(p['map_kind'] == 'trailhead' for p in pois) and track:
        lat, lon = track[0][0], track[0][1]
        add_poi(lat, lon, f'{meta["display_name"]} (trailhead, approx.)', 'trailhead', 0.0)

    pois.sort(key=lambda p: (0 if p['map_kind'] == 'trailhead' else 1, p['mile']))
    for i, p in enumerate(pois):
        p['mile'] = round(0.1 * i, 1)
    return pois


def load_kml(path: pathlib.Path) -> ET.Element:
    text = path.read_text(encoding='utf-8', errors='replace')
    return ET.fromstring(text)


def load_gpx_track_and_waypoints(path: pathlib.Path) -> tuple[list[list[float]], list[tuple[float, float, str]]]:
    """All ``trkpt`` in document order; waypoints from ``wpt``."""
    root = load_kml(path)
    track: list[list[float]] = []
    wpts: list[tuple[float, float, str]] = []
    for el in root.iter():
        tag = _local(el.tag)
        if tag == 'trkpt':
            la, lo = el.get('lat'), el.get('lon')
            if la is None or lo is None:
                continue
            lat, lon = float(la), float(lo)
            if track and track[-1][0] == lat and track[-1][1] == lon:
                continue
            track.append([lat, lon])
        elif tag == 'wpt':
            la, lo = el.get('lat'), el.get('lon')
            if la is None or lo is None:
                continue
            name = ''
            for ch in el:
                if _local(ch.tag) == 'name':
                    name = _text(ch)
                    break
            wpts.append((float(la), float(lo), name.strip() or 'Waypoint'))
    # Drop obvious GPS teleports; keep field tracks dense.
    track = _longest_run_without_long_edges(track, max_edge_m=5000.0)
    return track, wpts


def apply_gpx_track_override(tid: str, blob: dict, meta: dict) -> dict:
    path = GPX_TRACK_OVERRIDES.get(tid)
    if not path or not path.is_file():
        return blob
    track, wpts = load_gpx_track_and_waypoints(path)
    if len(track) < 2:
        return blob
    rel = path.relative_to(path.parents[1]).as_posix()
    pois = build_pois_for_trail(tid, track, wpts, meta)
    out = {**blob, 'track_points': track, 'pois': pois}
    out['geometry_source_gpx'] = rel
    return out


def fetch_kml(trail_id: str) -> ET.Element:
    url = f'https://www.rr4w.com/kml/{trail_id}.kml'
    req = urllib.request.Request(url, headers={'User-Agent': 'SRS2026TripPlanImport/1.0'})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
    return ET.fromstring(data.decode('utf-8', errors='replace'))


def parse_kml_tree(root: ET.Element) -> tuple[list[list[float]], list[tuple[float, float, str]]]:
    points: list[tuple[float, float, str]] = []
    for pm in _iter_placemarks(root):
        _lines, pt = _placemark_lines_and_point(pm)
        if pt is not None:
            points.append(pt)
    track = _build_track_from_kml_segments(root)
    return track, points


def trail_blob(trail_id: str, root: ET.Element, downloaded_at: str) -> dict:
    meta = TRAILS[trail_id]
    track, raw_pts = parse_kml_tree(root)
    pois = build_pois_for_trail(trail_id, track, raw_pts, meta)
    return {
        'rr4w_id': int(trail_id),
        'rr4w_url': f'https://www.rr4w.com/trail-details.cfm?trailid={trail_id}',
        'kml_url': f'https://www.rr4w.com/kml/{trail_id}.kml',
        'downloaded_at': downloaded_at,
        'trail_meta': meta,
        'track_points': track,
        'pois': pois,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--from-dir', type=pathlib.Path, help='Read planning/_rr4w_{id}.kml instead of fetching')
    args = ap.parse_args()
    from datetime import datetime, timezone

    downloaded_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    trails_out: dict[str, dict] = {}
    for tid in TRAILS:
        if args.from_dir:
            root = load_kml(args.from_dir / f'_rr4w_{tid}.kml')
        else:
            root = fetch_kml(tid)
        trails_out[tid] = trail_blob(tid, root, downloaded_at)
        trails_out[tid] = apply_gpx_track_override(tid, trails_out[tid], TRAILS[tid])

    payload = {
        'source': (
            'RR4W KML (processed): LineStrings greedy-chained by nearest endpoint, '
            'then longest run with edges capped at 700 m to drop telemetry spikes. '
            'Trails 37 and 38 use GPX field tracks from planning/ when present '
            '(hell_s_revenge_kmz.gpx, top-of-the-world-2024.gpx). '
            'Re-run import_rr4w_moab_kml.py after RR4W or GPX updates.'
        ),
        'trails': trails_out,
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'Wrote {OUT_PATH} ({OUT_PATH.stat().st_size // 1024} KB)')


if __name__ == '__main__':
    main()
