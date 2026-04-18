"""Query live Recreation.gov campground availability for our trip dates."""
from __future__ import annotations
import json
import pathlib
import time
import urllib.request

TARGET_DATES = ['2026-05-02', '2026-05-03', '2026-05-04', '2026-05-05',
                '2026-05-06', '2026-05-07', '2026-05-08', '2026-05-09']


def fetch_month(cg_id: str):
    url = f'https://www.recreation.gov/api/camps/availability/campground/{cg_id}/month?start_date=2026-05-01T00%3A00%3A00.000Z'
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))


def summarize(cg_id: str, cg_label: str):
    data = fetch_month(cg_id)
    campsites = data.get('campsites', {})
    print(f'\n=== {cg_label} (id={cg_id}) ===')
    print(f'Total sites in feed: {len(campsites)}')

    # Collect all unique status values across target dates
    statuses = {}
    per_day = {d: {} for d in TARGET_DATES}
    for site_id, site in campsites.items():
        avail = site.get('availabilities', {})
        loop = site.get('loop') or ''
        nm = site.get('site') or site_id
        typ = site.get('campsite_type') or ''
        for k, v in avail.items():
            d = k[:10]
            if d in TARGET_DATES:
                statuses[v] = statuses.get(v, 0) + 1
                per_day[d].setdefault(v, []).append(f'{loop} / {nm} ({typ})')

    print(f'Status histogram across target dates: {statuses}')
    for d in TARGET_DATES:
        buckets = per_day[d]
        line = ', '.join(f'{s}={len(lst)}' for s, lst in buckets.items())
        print(f'  {d}: {line}')
        # If anything is Available, show which
        if 'Available' in buckets:
            for e in buckets['Available'][:8]:
                print(f'      + AVAILABLE: {e}')


def main():
    TARGETS = [
        ('202133',    'San Rafael Swinging Bridge'),
        ('10283358',  'Temple Mountain Townsite'),
        ('10283369',  'Buckhorn Draw'),
    ]
    for cg_id, label in TARGETS:
        try:
            summarize(cg_id, label)
        except Exception as e:
            print(f'\n=== {label} (id={cg_id}) ERROR: {e}')
        time.sleep(3)


if __name__ == '__main__':
    main()
