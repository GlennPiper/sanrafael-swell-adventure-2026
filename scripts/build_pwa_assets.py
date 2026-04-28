"""Emit the PWA primitives consumed by GitHub Pages:

- ``manifest.webmanifest`` -- Web App Manifest at the workspace root.
- ``service-worker.js``    -- offline-first cache + auto-update plumbing.
- ``robots.txt``           -- search-engine suppression (the trip site is public
  by URL but we don't want it indexed).
- ``assets/qr.png``        -- QR code that resolves to the landing URL (used by
  ``index.html`` and the README install section).

The ``BUILD_VERSION`` baked into ``service-worker.js`` is the cache namespace.
Bumping it forces installed clients to re-download on next visit. We derive it
from ``planning/trip_data.json`` (``generated_at`` + content hash) **and** the
Markdown sources for standalone PWA pages (slot, fuel, overland alternates,
alt itineraries), plus ``river-crossing.html`` and ``moab-camping.html``, so
edits invalidate the cache even when ``trip_data.json`` is unchanged.

The site's public URL is read from the ``SITE_URL`` env var (set by the GitHub
Actions workflow). For local builds we fall back to a sensible
relative-path-only configuration; the manifest's ``start_url`` is left
relative (``./trip-itinerary.html``) so the same artifact works on any host.

QR generation requires the ``qrcode[pil]`` extra; if missing, we skip the QR
write with a warning so local builds without the optional dep still succeed.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib

BASE = pathlib.Path(__file__).resolve().parent.parent
PLAN = BASE / 'planning'
ASSETS = BASE / 'assets'

TRIP_DATA = PLAN / 'trip_data.json'
MANIFEST_OUT = BASE / 'manifest.webmanifest'
SW_OUT = BASE / 'service-worker.js'
ROBOTS_OUT = BASE / 'robots.txt'
QR_OUT = ASSETS / 'qr.png'

APP_NAME = '2026 San Rafael Swell Adventure'
APP_SHORT = 'SRS Trip'
APP_DESC = (
    'Offline trip itinerary, route, camps, and reference for the May 1-10, 2026 '
    'San Rafael Swell + Moab overlanding adventure.'
)
THEME_COLOR = '#0d1117'
BACKGROUND_COLOR = '#0d1117'

SITE_URL = os.environ.get('SITE_URL', '').rstrip('/')


def _build_version() -> str:
    """Cache namespace = trip_data*.json + planning markdown sources for standalone pages.

    Now includes the alternate-itinerary JSON payloads (trip_data_alt_*.json)
    so edits to any alternate route -- new POIs, camp changes, re-split days --
    invalidate installed PWAs even when the main trip_data.json is unchanged.
    """
    raw = TRIP_DATA.read_bytes() if TRIP_DATA.exists() else b'no-data'
    alt_json_names = (
        'trip_data_alt_a.json',
        'trip_data_alt_b.json',
        'trip_data_alt_d.json',
    )
    alt_raw = b''
    for name in alt_json_names:
        p = PLAN / name
        alt_raw += p.read_bytes() if p.exists() else b''
    extra_md_names = (
        'slot-canyon-guide.md',
        'fuel_plan.md',
        'overland_alternates.md',
        'trip-itinerary-alt-a.md',
        'trip-itinerary-alt-b.md',
        'trip-itinerary-alt-d.md',
    )
    extra_raw = b''
    for name in extra_md_names:
        p = PLAN / name
        extra_raw += p.read_bytes() if p.exists() else b''
    # Standalone HTML not emitted from markdown (must bump SW when edited).
    extra_html_names = ('river-crossing.html', 'moab-camping.html')
    for name in extra_html_names:
        p = BASE / name
        extra_raw += p.read_bytes() if p.exists() else b''
    hw_tracks = PLAN / 'highway_tracks.json'
    extra_raw += hw_tracks.read_bytes() if hw_tracks.exists() else b''
    short = hashlib.sha1(raw + alt_raw + extra_raw).hexdigest()[:10]
    try:
        gen = json.loads(raw.decode('utf-8')).get('generated_at', '')
    except Exception:
        gen = ''
    return f'{gen}-{short}' if gen else short


BUILD_VERSION = _build_version()


# Files the service worker pre-caches on install. Anything not in this list will
# still be cached on first online fetch (stale-while-revalidate), so this is
# the "must work offline from the very first launch" set.
PRECACHE = [
    './',
    'index.html',
    'trip-itinerary.html',
    'trip-reference.html',
    'slot-canyon-guide.html',
    'fuel-plan.html',
    'overland-alternates.html',
    'river-crossing.html',
    'moab-camping.html',
    'trip-itinerary-alt-a.html',
    'trip-itinerary-alt-b.html',
    'trip-itinerary-alt-d.html',
    'trip-plan.gpx',
    'trip-plan-alt-a.gpx',
    'trip-plan-alt-b.gpx',
    'trip-plan-alt-d.gpx',
    'manifest.webmanifest',
    'icons/icon-192.png',
    'icons/icon-512.png',
    'icons/icon-512-maskable.png',
    'icons/apple-touch-icon.png',
]


def write_manifest() -> None:
    manifest = {
        'name': APP_NAME,
        'short_name': APP_SHORT,
        'description': APP_DESC,
        'start_url': './trip-itinerary.html',
        'scope': './',
        'display': 'standalone',
        'orientation': 'any',
        'background_color': BACKGROUND_COLOR,
        'theme_color': THEME_COLOR,
        'icons': [
            {
                'src': 'icons/icon-192.png',
                'sizes': '192x192',
                'type': 'image/png',
                'purpose': 'any',
            },
            {
                'src': 'icons/icon-512.png',
                'sizes': '512x512',
                'type': 'image/png',
                'purpose': 'any',
            },
            {
                'src': 'icons/icon-512-maskable.png',
                'sizes': '512x512',
                'type': 'image/png',
                'purpose': 'maskable',
            },
        ],
    }
    MANIFEST_OUT.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding='utf-8',
    )
    print(f'Wrote {MANIFEST_OUT.relative_to(BASE)}')


def write_service_worker() -> None:
    precache_js = json.dumps(PRECACHE, indent=2)
    sw = f"""// Generated by scripts/build_pwa_assets.py -- do not hand-edit.
// Bump BUILD_VERSION (auto, derived from trip_data.json) to force a refresh on installed clients.

const BUILD_VERSION = {json.dumps(BUILD_VERSION)};
const CACHE_NAME = 'srs-trip-' + BUILD_VERSION;
const PRECACHE = {precache_js};

self.addEventListener('install', (event) => {{
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE)).then(() => self.skipWaiting())
  );
}});

self.addEventListener('activate', (event) => {{
  event.waitUntil((async () => {{
    const keys = await caches.keys();
    await Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)));
    await self.clients.claim();
  }})());
}});

self.addEventListener('message', (event) => {{
  if (event.data && event.data.type === 'SKIP_WAITING') self.skipWaiting();
}});

// Fetch strategy:
// - Navigation requests: network-first with cache fallback (so a fresh visit
//   while online picks up new HTML; offline still works).
// - Other GETs: cache-first with background revalidate; fetched-fresh entries
//   are written back into the cache so subsequent offline opens have them.
self.addEventListener('fetch', (event) => {{
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return; // don't cache cross-origin map tiles

  if (req.mode === 'navigate') {{
    event.respondWith((async () => {{
      try {{
        const fresh = await fetch(req);
        const cache = await caches.open(CACHE_NAME);
        cache.put(req, fresh.clone());
        return fresh;
      }} catch (e) {{
        const cached = await caches.match(req) || await caches.match('index.html');
        if (cached) return cached;
        throw e;
      }}
    }})());
    return;
  }}

  event.respondWith((async () => {{
    const cached = await caches.match(req);
    if (cached) {{
      // Revalidate in the background; ignore failures (offline is fine).
      fetch(req).then((fresh) => {{
        if (fresh && fresh.ok) caches.open(CACHE_NAME).then((c) => c.put(req, fresh));
      }}).catch(() => {{}});
      return cached;
    }}
    try {{
      const fresh = await fetch(req);
      if (fresh && fresh.ok) {{
        const cache = await caches.open(CACHE_NAME);
        cache.put(req, fresh.clone());
      }}
      return fresh;
    }} catch (e) {{
      throw e;
    }}
  }})());
}});
"""
    SW_OUT.write_text(sw, encoding='utf-8')
    print(f'Wrote {SW_OUT.relative_to(BASE)} (BUILD_VERSION={BUILD_VERSION})')


def write_robots() -> None:
    ROBOTS_OUT.write_text(
        'User-agent: *\nDisallow: /\n',
        encoding='utf-8',
    )
    print(f'Wrote {ROBOTS_OUT.relative_to(BASE)}')


def write_qr() -> None:
    if not SITE_URL:
        print('Skipping QR (SITE_URL env var not set; safe for local builds)')
        return
    try:
        import qrcode  # type: ignore
    except ImportError:
        print('Skipping QR (qrcode[pil] not installed; pip install "qrcode[pil]")')
        return
    ASSETS.mkdir(parents=True, exist_ok=True)
    img = qrcode.make(SITE_URL + '/')
    img.save(QR_OUT)
    print(f'Wrote {QR_OUT.relative_to(BASE)} -> {SITE_URL}/')


def main() -> None:
    write_manifest()
    write_service_worker()
    write_robots()
    write_qr()


if __name__ == '__main__':
    main()
