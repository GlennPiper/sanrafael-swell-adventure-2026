"""Attach RR4W trail geometry + metadata to Moab day rows before ``build_payload``."""
from __future__ import annotations

import copy
import json
import pathlib
from typing import Any

_BASE = pathlib.Path(__file__).resolve().parent.parent
_GEOMETRY_PATH = _BASE / 'planning' / 'moab_rr4w_geometry.json'

# day_id -> RR4W trail id string (must exist in moab_rr4w_geometry.json)
VARIANT_DAY_TRAIL: dict[str, dict[str, str]] = {
    'main': {
        'day5_moab': '37',
        'day6_moab': '44',
        'day7_moab': '38',
    },
    'altA': {
        'altA_day6_moab': '37',
        'altA_day7_moab': '44',
    },
    'altB': {
        'altB_day5_moab': '37',
        'altB_day6_moab': '44',
        'altB_day7_moab': '38',
    },
    'altD': {
        'altD_day5_moab': '37',
        'altD_day6_moab': '44',
        'altD_day7_moab': '38',
    },
}


def load_moab_geometry(path: pathlib.Path | None = None) -> dict[str, Any]:
    p = path or _GEOMETRY_PATH
    if not p.is_file():
        raise FileNotFoundError(f'Missing {p}; run py -3 scripts/import_rr4w_moab_kml.py')
    return json.loads(p.read_text(encoding='utf-8'))


def _moab_trail_public(blob: dict) -> dict[str, Any]:
    meta = blob.get('trail_meta') or {}
    return {
        'rr4w_id': blob['rr4w_id'],
        'rr4w_url': blob['rr4w_url'],
        'kml_url': blob.get('kml_url'),
        'downloaded_at': blob.get('downloaded_at'),
        'geometry_source_gpx': blob.get('geometry_source_gpx'),
        'display_name': meta.get('display_name'),
        'moab_trails_anchor': meta.get('moab_trails_anchor'),
        'rating': meta.get('rating'),
        'length_mi': meta.get('length_mi'),
        'tires_min': meta.get('tires_min'),
        'notes': meta.get('notes'),
    }


def apply_moab_trails(
    days_spec: list[dict],
    variant_key: str,
    geometry: dict[str, Any] | None = None,
) -> list[dict]:
    """Return a new list of day dicts with synthetic_* + moab_trail applied (does not mutate input)."""
    geom = geometry if geometry is not None else load_moab_geometry()
    trails = geom.get('trails') or {}
    day_map = VARIANT_DAY_TRAIL.get(variant_key) or {}
    out: list[dict] = []
    for day in days_spec:
        d = copy.deepcopy(day)
        tid = day_map.get(d['id'])
        if not tid or tid not in trails:
            out.append(d)
            continue
        blob = trails[tid]
        tp = blob.get('track_points') or []
        d['synthetic_track_points'] = [[float(p[0]), float(p[1])] for p in tp]
        d['synthetic_pois'] = [copy.deepcopy(p) for p in (blob.get('pois') or [])]
        d['moab_trail'] = _moab_trail_public(blob)
        out.append(d)
    return out
