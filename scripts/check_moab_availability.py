"""Query Recreation.gov for Moab group and standard campgrounds for May 6-9, 2026."""
from __future__ import annotations
import json
import time
import urllib.request
import collections

TARGET_DATES = ['2026-05-06', '2026-05-07', '2026-05-08', '2026-05-09']

TARGETS = [
    ('251841', 'Goose Island Group Sites (SR 128)'),
    ('251840', "Ken's Lake Group Sites"),
    ('234388', "Ken's Lake Campground"),
    ('251842', 'Big Bend Campground (SR 128)'),
    ('233921', 'Hittle Bottom (SR 128)'),
    ('251843', 'Hal Canyon (SR 128)'),
    ('234385', 'Oak Grove (SR 128)'),
    ('234386', 'Grandstaff Campground (SR 128)'),
    ('232508', 'Devils Garden (Arches NP)'),
    ('234044', 'Willow Flat (Canyonlands Island in Sky)'),
    ('234045', 'Dead Horse Point SP - Kayenta'),
    ('234046', 'Dead Horse Point SP - Wingate'),
    ('251844', 'Jaycee Park (SR 279)'),
    ('251845', 'Williams Bottom (SR 279)'),
    ('251846', 'Gold Bar (SR 279)'),
    ('251847', 'Sand Flats Area A (Grand County)'),
    ('251848', 'Sand Flats Area B'),
    ('251849', 'Sand Flats Area C'),
    ('251850', 'Sand Flats Area D'),
]


def fetch_month(cg_id: str):
    url = f'https://www.recreation.gov/api/camps/availability/campground/{cg_id}/month?start_date=2026-05-01T00%3A00%3A00.000Z'
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    })
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode('utf-8'))


def summarize(cg_id: str, label: str):
    try:
        data = fetch_month(cg_id)
    except Exception as e:
        print(f'-- {label} (id={cg_id}) ERROR: {e}')
        return
    cs = data.get('campsites', {})
    if not cs:
        print(f'-- {label} (id={cg_id}): empty response')
        return
    print(f'\n== {label} (id={cg_id}) - {len(cs)} sites ==')
    per_day = {d: collections.Counter() for d in TARGET_DATES}
    avail_list = {d: [] for d in TARGET_DATES}
    for sid, s in cs.items():
        loop = s.get('loop') or ''
        nm = s.get('site') or sid
        typ = s.get('campsite_type') or ''
        for k, v in s.get('availabilities', {}).items():
            d = k[:10]
            if d in TARGET_DATES:
                per_day[d][v] += 1
                if v == 'Available':
                    avail_list[d].append(f'{loop}/{nm} ({typ})')
    for d in TARGET_DATES:
        line = ', '.join(f'{k}={v}' for k, v in per_day[d].items())
        print(f'  {d}: {line}')
        for e in avail_list[d][:10]:
            print(f'      + {e}')


def main():
    for cg_id, label in TARGETS:
        summarize(cg_id, label)
        time.sleep(2)


if __name__ == '__main__':
    main()
