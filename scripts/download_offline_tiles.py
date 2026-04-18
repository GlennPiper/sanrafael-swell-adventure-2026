"""Download OpenStreetMap raster tiles for the full trip area and cache them in
planning/offline_tiles/{z}/{x}/{y}.png. Also download Leaflet's minified JS +
CSS into planning/vendor/leaflet/ so the map can render fully offline (the tile
cache is useless if leaflet.js itself can't load).

build_deliverables.py then base64-embeds the tiles and inlines the Leaflet
assets into trip-itinerary.html so the page works with zero internet.

Usage:
    py scripts/download_offline_tiles.py

Idempotent: skips tiles/assets that already exist locally. Respects OSM's
tile-usage policy (1 req/sec, descriptive User-Agent, attribution rendered in
the map). Re-run if the bbox changes or you want to refresh stale tiles.
"""
from __future__ import annotations
import math
import pathlib
import time
import urllib.request
import urllib.error


BASE = pathlib.Path(__file__).resolve().parent.parent
TILE_DIR = BASE / 'planning' / 'offline_tiles'
VENDOR_DIR = BASE / 'planning' / 'vendor' / 'leaflet'
TILE_DIR.mkdir(parents=True, exist_ok=True)
VENDOR_DIR.mkdir(parents=True, exist_ok=True)

# Leaflet assets to inline into the HTML so the map engine itself works offline.
LEAFLET_VERSION = '1.9.4'
LEAFLET_ASSETS = [
    (f'https://unpkg.com/leaflet@{LEAFLET_VERSION}/dist/leaflet.js',  'leaflet.js'),
    (f'https://unpkg.com/leaflet@{LEAFLET_VERSION}/dist/leaflet.css', 'leaflet.css'),
]

# Trip bounding box with generous buffer (covers Swell + Moab + Dead Horse +
# fuel stations at Hanksville / Castle Dale / Green River / Emery).
BBOX = {
    'lat_min': 38.25,
    'lat_max': 39.35,
    'lon_min': -111.30,
    'lon_max': -109.10,
}
# Zoom levels to cache. z=7 gives a state-level overview; z=9 shows towns and
# the main roads within the Swell. Higher zooms explode tile count fast.
ZOOMS = [7, 8, 9]

TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
# OSM policy: identify with a descriptive UA including contact info / project.
USER_AGENT = 'SanRafaelTripBuilder/1.0 (personal trip planning; https://openstreetmap.org/copyright)'
RATE_LIMIT_S = 1.1  # ~1 tile/sec, OSM-polite


def lonlat_to_tile(lon: float, lat: float, z: int) -> tuple[int, int]:
    """Web-Mercator tile coords for a given lon/lat/zoom."""
    lat_rad = math.radians(lat)
    n = 2 ** z
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return x, y


def tile_range(bbox: dict, z: int) -> tuple[range, range]:
    """Return the (x_range, y_range) tiles covering the bbox at zoom z."""
    x0, y1 = lonlat_to_tile(bbox['lon_min'], bbox['lat_min'], z)  # SW -> x min, y max
    x1, y0 = lonlat_to_tile(bbox['lon_max'], bbox['lat_max'], z)  # NE -> x max, y min
    return range(min(x0, x1), max(x0, x1) + 1), range(min(y0, y1), max(y0, y1) + 1)


def fetch(url: str, dest: pathlib.Path) -> bool:
    """Download a single tile; return True on new download, False on skip/fail."""
    if dest.exists() and dest.stat().st_size > 0:
        return False  # already cached
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
            dest.write_bytes(data)
            return True
    except urllib.error.HTTPError as e:
        print(f'  HTTP {e.code} for {url}')
    except Exception as e:  # noqa: BLE001 (diagnostic only)
        print(f'  ERROR {e} for {url}')
    return False


def main() -> None:
    # Leaflet assets first (tiny, one-time)
    print('Leaflet assets:')
    for url, fname in LEAFLET_ASSETS:
        dest = VENDOR_DIR / fname
        if fetch(url, dest):
            kb = dest.stat().st_size / 1024
            print(f'  Downloaded {fname} ({kb:.1f} KB)')
        else:
            kb = dest.stat().st_size / 1024 if dest.exists() else 0
            print(f'  Skipped    {fname} ({kb:.1f} KB, already cached)')
    print()

    total_planned = 0
    total_downloaded = 0
    total_skipped = 0
    for z in ZOOMS:
        xs, ys = tile_range(BBOX, z)
        n_z = len(xs) * len(ys)
        total_planned += n_z
        print(f'Zoom {z}: {len(xs)} cols x {len(ys)} rows = {n_z} tiles'
              f' (x {xs.start}-{xs.stop - 1}, y {ys.start}-{ys.stop - 1})')
        for x in xs:
            for y in ys:
                dest = TILE_DIR / str(z) / str(x) / f'{y}.png'
                url = TILE_URL.format(z=z, x=x, y=y)
                if fetch(url, dest):
                    total_downloaded += 1
                    time.sleep(RATE_LIMIT_S)  # only when we actually hit the network
                else:
                    total_skipped += 1

    on_disk = sum(1 for _ in TILE_DIR.rglob('*.png'))
    disk_kb = sum(p.stat().st_size for p in TILE_DIR.rglob('*.png')) / 1024
    print()
    print(f'Planned:     {total_planned}')
    print(f'Downloaded:  {total_downloaded} (new this run)')
    print(f'Skipped:     {total_skipped} (already cached or errored)')
    print(f'On disk:     {on_disk} tiles, {disk_kb:.1f} KB total')
    print(f'Location:    {TILE_DIR}')


if __name__ == '__main__':
    main()
