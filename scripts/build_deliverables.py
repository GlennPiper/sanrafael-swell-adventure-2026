"""Generate trip-itinerary.html, trip-reference.html, and trip-plan.gpx from trip_data.json.

All HTML is offline-first: content is usable without internet. Leaflet's JS/CSS are inlined
from planning/vendor/leaflet/ and a low-res OpenStreetMap tile cache is base64-embedded from
planning/offline_tiles/, so the map renders with a pixelated-but-recognizable background even
when the page is viewed fully offline. When online, Esri tiles load on top of the offline
baseline. Run scripts/download_offline_tiles.py once to populate both caches.
"""
from __future__ import annotations
import base64
import html
import json
import pathlib

BASE = pathlib.Path(__file__).resolve().parent.parent
PLAN = BASE / 'planning'
OUT_DIR = BASE
TILE_DIR = PLAN / 'offline_tiles'
VENDOR_DIR = PLAN / 'vendor' / 'leaflet'

data = json.loads((PLAN / 'trip_data.json').read_text(encoding='utf-8'))


# -----------------------------------------------------------------------------
# Load locally-vendored Leaflet JS + CSS (downloaded by
# scripts/download_offline_tiles.py). Inlining them into the HTML makes the
# map work with zero internet -- otherwise the tile cache is useless because
# leaflet.js itself wouldn't load.
# -----------------------------------------------------------------------------
def _read_vendor(name, fallback=''):
    p = VENDOR_DIR / name
    return p.read_text(encoding='utf-8') if p.exists() else fallback


LEAFLET_JS = _read_vendor('leaflet.js')
LEAFLET_CSS = _read_vendor('leaflet.css')


# -----------------------------------------------------------------------------
# Shared PWA <head> block + service-worker registration. Injected into BOTH
# trip-itinerary.html and trip-reference.html so the two pages enroll in the
# same installed PWA (same manifest, same SW). Keeping a single source-of-
# truth here means the manifest link, theme color, and iOS metadata can never
# drift between the two pages.
#
# Both constants are plain strings that get spliced into the f-string HTML
# templates as variable substitutions ({PWA_HEAD} / {PWA_REGISTER_JS}); the
# f-string never reparses their contents, so JS object literals inside them
# do NOT need doubled braces.
# -----------------------------------------------------------------------------
PWA_HEAD = """<meta name="theme-color" content="#0d1117">
<meta name="description" content="Offline trip itinerary, route, camps, and reference for the May 2-10, 2026 San Rafael Swell + Moab overlanding adventure.">
<meta name="robots" content="noindex,nofollow">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" type="image/png" sizes="192x192" href="icons/icon-192.png">
<link rel="icon" type="image/png" sizes="512x512" href="icons/icon-512.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="SRS Trip">
<meta name="mobile-web-app-capable" content="yes">"""


PWA_REGISTER_JS = """<script>
(function(){
  if (!('serviceWorker' in navigator)) return;
  window.addEventListener('load', function(){
    navigator.serviceWorker.register('service-worker.js').then(function(reg){
      reg.addEventListener('updatefound', function(){
        var nw = reg.installing;
        if (!nw) return;
        nw.addEventListener('statechange', function(){
          if (nw.state === 'installed' && navigator.serviceWorker.controller) {
            showUpdateToast(reg);
          }
        });
      });
    }).catch(function(){});
    var refreshing = false;
    navigator.serviceWorker.addEventListener('controllerchange', function(){
      if (refreshing) return;
      refreshing = true;
      window.location.reload();
    });
  });
  function showUpdateToast(reg){
    if (document.getElementById('pwa-update-toast')) return;
    var t = document.createElement('div');
    t.id = 'pwa-update-toast';
    t.setAttribute('role', 'status');
    t.style.cssText = 'position:fixed;left:50%;bottom:20px;transform:translateX(-50%);background:#1f6feb;color:#fff;padding:12px 16px;border-radius:8px;font:14px/1.4 system-ui,sans-serif;z-index:9999;box-shadow:0 4px 14px rgba(0,0,0,.35);max-width:90vw;text-align:center;cursor:pointer';
    t.innerHTML = 'New trip data available. <strong>Tap to reload</strong>.';
    t.addEventListener('click', function(){
      if (reg.waiting) reg.waiting.postMessage({type: 'SKIP_WAITING'});
    });
    document.body.appendChild(t);
  }
})();
</script>"""


# -----------------------------------------------------------------------------
# Load pre-downloaded OSM tiles (see scripts/download_offline_tiles.py) and
# encode them as base64 data URIs keyed by "z/x/y". This lets the Leaflet map
# render a low-res background when the page is viewed offline in the field.
# -----------------------------------------------------------------------------
def load_offline_tiles():
    tiles = {}
    if not TILE_DIR.exists():
        return tiles, 0
    total_bytes = 0
    for p in sorted(TILE_DIR.rglob('*.png')):
        parts = p.relative_to(TILE_DIR).parts
        if len(parts) != 3:
            continue
        z, x, yfile = parts
        y = yfile.rsplit('.', 1)[0]
        raw = p.read_bytes()
        total_bytes += len(raw)
        tiles[f'{z}/{x}/{y}'] = 'data:image/png;base64,' + base64.b64encode(raw).decode('ascii')
    return tiles, total_bytes


OFFLINE_TILES, OFFLINE_TILES_BYTES = load_offline_tiles()


# -----------------------------------------------------------------------------
# Decimate track points for HTML map display. Full precision remains for GPX.
# -----------------------------------------------------------------------------
def decimate(points, every_n):
    if not points:
        return []
    return [p for i, p in enumerate(points) if i % every_n == 0 or i == len(points) - 1]


# Choose decimation per day to keep HTML size reasonable (~80-120 pts per day map).
for d in data['days']:
    n_pts = len(d.get('track_points') or [])
    if n_pts > 0:
        every = max(1, n_pts // 120)
        d['_map_points'] = decimate(d['track_points'], every)
    else:
        d['_map_points'] = []

# Overview track (full trip, decimated hard)
full_track = []
for d in data['days']:
    full_track.extend(d.get('track_points') or [])
every = max(1, len(full_track) // 400) if full_track else 1
overview_track = decimate(full_track, every)


# -----------------------------------------------------------------------------
# Shared helpers
# -----------------------------------------------------------------------------
def esc(s):
    if s is None:
        return ''
    return html.escape(str(s))


STATUS_BADGE = {
    'primary': ('primary', 'Primary'),
    'backup': ('backup', 'Backup'),
    'skip': ('skip', 'Skip'),
    'logistics': ('logistics', 'Logistics'),
    'conditional': ('conditional', 'Conditional'),
    'hike_candidate': ('hike', 'Hike (tactical)'),
    'unclassified': ('unclassified', '--'),
}


def badge_html(status):
    cls, label = STATUS_BADGE.get(status, ('unclassified', status or '--'))
    return f'<span class="badge badge-{cls}">{esc(label)}</span>'


def desc_button_html(name, desc):
    """Return an inline 'notes' icon button that opens the POI description dialog,
    or '' if no description is available. The button is keyed by POI name; the
    dialog script looks up descriptions from an embedded JSON map."""
    if not desc:
        return ''
    return (
        ' <button type="button" class="desc-btn" '
        f'data-desc-name="{esc(name)}" '
        'aria-label="Show description" title="Show description">'
        '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">'
        '<path fill="currentColor" d="M3 1.5h7.293a1 1 0 0 1 .707.293l2.5 2.5a1 1 0 0 1 .293.707V14.5a.5.5 0 0 1-.5.5H3a.5.5 0 0 1-.5-.5v-13a.5.5 0 0 1 .5-.5zM10 2v3h3L10 2zM4.5 7h7v1h-7zm0 2h7v1h-7zm0 2h5v1h-5z"/>'
        '</svg></button>'
    )


def collect_poi_descriptions(data):
    """Return a dict keyed by POI name -> {desc, sym, mile, off_m} gathered from
    every day's POIs. Duplicates across days keep the first occurrence; since
    POI names are unique in the source GPX this is effectively name -> info."""
    out = {}
    for d in data['days']:
        for p in (d.get('pois') or []):
            desc = (p.get('desc') or '').strip()
            if not desc or p['name'] in out:
                continue
            out[p['name']] = {
                'desc': desc,
                'sym':  p.get('sym') or '',
                'mile': p.get('mile'),
                'off':  p.get('dist_to_track_m') or 0,
                'lat':  p.get('lat'),
                'lon':  p.get('lon'),
                'day':  d.get('label') or d.get('id'),
            }
    return out


# Inserted just before </main> in both deliverable HTMLs
POI_DESC_DIALOG_HTML = """
<dialog id="poi-desc-dialog" aria-labelledby="poi-desc-title">
  <div class="dialog-head">
    <div>
      <h3 id="poi-desc-title">--</h3>
      <div class="dialog-sub" id="poi-desc-sub"></div>
    </div>
    <button type="button" class="dialog-close" aria-label="Close">&times;</button>
  </div>
  <div class="dialog-body" id="poi-desc-body">--</div>
</dialog>
"""


# Inserted inside the page's <script> block. {desc_json} is substituted with the
# embedded description map. Uses double braces because the containing template
# is an f-string.
POI_DESC_DIALOG_JS = """
// ----- POI description dialog (offline-first) -----
const POI_DESCRIPTIONS = {desc_json};
(function() {{
  const dlg   = document.getElementById('poi-desc-dialog');
  if (!dlg) return;
  const title = dlg.querySelector('#poi-desc-title');
  const sub   = dlg.querySelector('#poi-desc-sub');
  const body  = dlg.querySelector('#poi-desc-body');
  const close = dlg.querySelector('.dialog-close');

  function escHTML(s) {{
    return String(s == null ? '' : s).replace(/[&<>"']/g,
      c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
  }}
  function render(name) {{
    const info = POI_DESCRIPTIONS[name];
    if (!info) return false;
    title.textContent = name;
    const bits = [];
    if (info.mile != null)
      bits.push('mile <code>' + info.mile.toFixed(1) + '</code>');
    if (info.sym)
      bits.push('type <code>' + escHTML(info.sym) + '</code>');
    if (info.off)
      bits.push(Math.round(info.off) + ' m off-track');
    if (info.lat != null && info.lon != null)
      bits.push('<a href="https://www.google.com/maps/search/?api=1&query=' +
                info.lat + ',' + info.lon + '" target="_blank" rel="noopener">Map It</a>');
    sub.innerHTML = bits.join(' &middot; ');
    const paragraphs = info.desc.split(/\\n\\s*\\n/).map(p => p.trim()).filter(Boolean);
    body.innerHTML = paragraphs.map(p => '<p>' + escHTML(p).replace(/\\n/g, '<br>') + '</p>').join('') +
                     '<div class="src">Source: original route GPX (On The Go Crew).</div>';
    return true;
  }}
  document.addEventListener('click', function(e) {{
    const btn = e.target.closest('.desc-btn');
    if (!btn) return;
    e.preventDefault();
    const name = btn.dataset.descName;
    if (render(name)) dlg.showModal();
  }});
  close.addEventListener('click', () => dlg.close());
  // Click the backdrop (outside the dialog content) to close.
  dlg.addEventListener('click', function(e) {{
    if (e.target === dlg) {{
      const r = dlg.getBoundingClientRect();
      const inside = e.clientX >= r.left && e.clientX <= r.right
                  && e.clientY >= r.top  && e.clientY <= r.bottom;
      if (!inside) dlg.close();
    }}
  }});
}})();
"""


POI_HEADER = (
    '<thead><tr><th>Mi</th><th>Name</th><th>Status</th><th>Type</th>'
    '<th>Note</th><th>Off-track</th><th>Coords</th></tr></thead>'
)
POI_HEADER_SCHEDULED = (
    '<thead><tr><th title="Include in scheduled itinerary">In?</th>'
    '<th>Mi</th><th>Name</th><th>Status</th><th>Type</th>'
    '<th>Note</th><th>Off-track</th><th>Coords</th>'
    '<th title="Estimated time of arrival">ETA</th>'
    '<th title="Estimated time spent at the stop, in minutes">Stop (min)</th></tr></thead>'
)


def poi_row(p, day_id=None, allow_focus=False, scheduled=False, idx=0, day_mph=20):
    lat, lon = p.get('lat'), p.get('lon')
    name_text = esc(p['name'])
    if allow_focus and day_id and lat is not None and lon is not None:
        name_html = (
            f'<a href="#" class="focus-map" data-day="{esc(day_id)}" '
            f'data-lat="{lat}" data-lon="{lon}" '
            f'title="Zoom map to this stop">{name_text}</a>'
        )
    else:
        name_html = name_text
    name_html += desc_button_html(p['name'], p.get('desc'))
    coords_html = ''
    if lat is not None and lon is not None:
        gm = f'https://www.google.com/maps/search/?api=1&query={lat},{lon}'
        coords_html = (
            f'<code>{lat:.5f}, {lon:.5f}</code> &middot; '
            f'<a href="{gm}" target="_blank" rel="noopener">Map It</a>'
        )

    # data-label values surface as row headings in the mobile card layout
    # (see @media (max-width: 720px) in the stylesheet).
    if not scheduled:
        return (
            '<tr>'
            f'<td class="num" data-label="Mile">{p["mile"]:.1f}</td>'
            f'<td class="td-name" data-label="Name">{name_html}</td>'
            f'<td data-label="Status">{badge_html(p["status"])}</td>'
            f'<td data-label="Type">{esc(p.get("sym") or "")}</td>'
            f'<td data-label="Note">{esc(p.get("note") or "")}</td>'
            f'<td class="num" data-label="Off-track" title="distance from main route track">{p.get("dist_to_track_m", 0):.0f} m</td>'
            f'<td class="coords" data-label="Coords">{coords_html}</td>'
            '</tr>'
        )

    # Scheduled-day row: include checkbox, ETA cell, duration input.
    poi_id = f'{day_id}-{idx}'
    default_min = int(p.get('default_minutes', 20))
    default_checked = bool(p.get('default_checked', False))
    checked_attr = ' checked' if default_checked else ''
    spur_mi = float(p.get('spur_mi') or 0.0)
    spur_hint = ''
    if spur_mi > 0:
        # Initial hint uses the day's default mph; the live scheduler recomputes
        # as the mph input changes. Best-effort: the text is a seed, not truth.
        mph_for_hint = max(3, day_mph)
        mins_hint = round(spur_mi / mph_for_hint * 60)
        spur_hint = (
            f'<div class="spur-hint" title="This stop sits at the end of an out-and-back spur. '
            f'Unchecking it subtracts the spur miles from the rest of the day\'s drive time.">'
            f'Spur: ~{spur_mi:.1f} mi &middot; saves ~{mins_hint} min at {mph_for_hint} mph</div>'
        )
    return (
        f'<tr data-poi-id="{esc(poi_id)}" data-mile="{p["mile"]}" '
        f'data-lat="{lat}" data-lon="{lon}" '
        f'data-offtrack="{p.get("dist_to_track_m", 0)}" '
        f'data-spur-mi="{spur_mi}" '
        f'data-status="{esc(p["status"])}" '
        f'data-default-checked="{str(default_checked).lower()}" '
        f'data-default-duration="{default_min}">'
        f'<td class="num td-include" data-label="Include"><input type="checkbox" class="poi-include"{checked_attr}></td>'
        f'<td class="num" data-label="Mile">{p["mile"]:.1f}</td>'
        f'<td class="td-name" data-label="Name">{name_html}{spur_hint}</td>'
        f'<td data-label="Status">{badge_html(p["status"])}</td>'
        f'<td data-label="Type">{esc(p.get("sym") or "")}</td>'
        f'<td data-label="Note">{esc(p.get("note") or "")}</td>'
        f'<td class="num" data-label="Off-track" title="distance from main route track">{p.get("dist_to_track_m", 0):.0f} m</td>'
        f'<td class="coords" data-label="Coords">{coords_html}</td>'
        f'<td class="num poi-eta" data-label="ETA">--</td>'
        f'<td class="num td-duration" data-label="Stop (min)"><input type="number" class="poi-duration" value="{default_min}" min="0" step="5"></td>'
        '</tr>'
    )


def _iter_camp_entries(camps):
    """Yield (tier_key, entry_idx, tier_total, camp_dict) across all camps for a
    day. Each tier value may be a single dict (legacy) or a list of dicts (new
    for days like the Wedge where all backups are equal-tier designated sites).
    entry_idx is 1-based; tier_total is the count within that tier so callers
    can conditionally append an "A/B/C" suffix when there are multiples."""
    if not isinstance(camps, dict):
        return
    for key in ('primary', 'secondary', 'tertiary'):
        val = camps.get(key)
        if not val:
            continue
        items = val if isinstance(val, list) else [val]
        items = [c for c in items if isinstance(c, dict)]
        total = len(items)
        for idx, c in enumerate(items, 1):
            yield key, idx, total, c


def _camp_has_coords(c):
    return isinstance(c, dict) and c.get('lat') and c.get('lon')


def _tier_label(key, idx, total):
    """'Primary', 'Secondary', 'Tertiary' -- append ' A/B/C' only when a tier
    holds multiple equal-rank options."""
    base = key.title()
    if total > 1:
        base += f' {chr(ord("A") + idx - 1)}'
    return base


def camp_block(camps, title='Campsites', day_id=None, allow_focus=False, scheduled=False):
    if not camps:
        return ''
    parts = [f'<h3>{esc(title)}</h3><div class="camp-grid">']
    for key, idx, total, c in _iter_camp_entries(camps):
        reserve = ''
        if c.get('reserve_url'):
            reserve = f' &middot; <a href="{esc(c["reserve_url"])}" target="_blank">Reserve</a>'
        lat, lon = c.get('lat'), c.get('lon')
        gmap = f'https://www.google.com/maps/search/?api=1&query={lat},{lon}' if lat and lon else ''
        gmap_link = f' &middot; <a href="{gmap}" target="_blank">Map It</a>' if gmap else ''
        name_text = esc(c.get("name"))
        if allow_focus and day_id and lat and lon:
            name_html = (
                f'<a href="#" class="focus-map" data-day="{esc(day_id)}" '
                f'data-lat="{lat}" data-lon="{lon}" '
                f'title="Zoom map to this campsite">{name_text}</a>'
            )
        else:
            name_html = name_text
        coords_line = ''
        if lat and lon:
            coords_line = f'<div class="camp-coords">GPS: <code>{lat:.5f}, {lon:.5f}</code></div>'
        eta_line = ''
        camp_data_attrs = ''
        if scheduled and lat and lon:
            eta_line = (
                '<div class="camp-eta">ETA at camp: <strong class="camp-eta-val">--</strong> '
                '<span class="muted">(from last included stop)</span></div>'
            )
            camp_data_attrs = (
                f' data-camp-tier="{key}" data-camp-idx="{idx}" data-day="{esc(day_id) if day_id else ""}"'
                f' data-lat="{lat}" data-lon="{lon}"'
            )
        tier_label = _tier_label(key, idx, total)
        parts.append(
            f'<div class="camp camp-{key}"{camp_data_attrs}>'
            f'<div class="camp-head"><strong>{esc(tier_label)}</strong>: {name_html}</div>'
            f'<div class="camp-meta">{esc(c.get("kind", ""))} &middot; {esc(c.get("cost", ""))}{reserve}{gmap_link}</div>'
            f'{coords_line}'
            f'{eta_line}'
            f'<div><strong>Facilities:</strong> {esc(c.get("facilities", ""))}</div>'
            f'<div><strong>Access:</strong> {esc(c.get("access", ""))}</div>'
            f'<div>{esc(c.get("notes", ""))}</div>'
            '</div>'
        )
    parts.append('</div>')
    return ''.join(parts)


def schedule_controls_html(d):
    """Top-of-day scheduler controls. Renders nothing for unscheduled days."""
    sched = d.get('schedule')
    if not sched:
        return ''
    return (
        f'<div class="schedule-controls" data-day="{esc(d["id"])}" '
        f'data-default-break="{esc(sched["break_camp_time"])}" '
        f'data-default-mph="{sched["moving_mph"]}" '
        f'data-start-lat="{sched["start_lat"]}" '
        f'data-start-lon="{sched["start_lon"]}" '
        f'data-mi-lo="{sched["mi_lo"]}">'
        '<div class="sched-row">'
        f'<label>Break camp <input type="time" class="sched-start" '
        f'value="{esc(sched["break_camp_time"])}"></label>'
        f'<label>Driving speed <input type="number" class="sched-mph" '
        f'value="{sched["moving_mph"]}" min="3" max="80" step="1"> mph</label>'
        '<button type="button" class="sched-reset" title="Restore defaults; clears your localStorage edits for this day">Reset day</button>'
        '</div>'
        '<div class="sched-summary">'
        '<span><strong class="sched-count">--</strong> stops included</span>'
        ' &middot; <span>Stop time: <strong class="sched-stop-time">--</strong></span>'
        ' &middot; <span>Drive time: <strong class="sched-drive-time">--</strong></span>'
        ' &middot; <span>Day total: <strong class="sched-day-total">--</strong></span>'
        ' &middot; <span>Arrival at primary camp: <strong class="sched-camp-eta">--</strong></span>'
        '</div>'
        '<div class="sched-hint muted">'
        'Uncheck a stop to remove it. Edit Stop (min) inline. ETAs assume pure driving '
        'at the speed above plus 2&times; off-route distance to detour to each stop. '
        'Camp ETAs add a straight-line drive from the last included stop with a 1.3&times; winding factor. '
        'Your edits are saved in this browser.'
        '</div>'
        '</div>'
    )


# -----------------------------------------------------------------------------
# Shared CSS (inlined in both HTML files for offline)
# -----------------------------------------------------------------------------
CSS = """
:root{
  --bg:#1b1f23; --panel:#24292f; --text:#e6edf3; --muted:#8b949e;
  --accent:#ff9d45; --border:#30363d;
  --primary:#238636; --backup:#9e6a03; --skip:#57606a;
  --hike:#a371f7; --conditional:#1f6feb; --logistics:#8b949e; --unclassified:#57606a;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:var(--bg);color:var(--text);
  font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
header{padding:16px 24px;background:#0d1117;border-bottom:1px solid var(--border)}
header h1{margin:0 0 4px 0;font-size:22px}
header .meta{color:var(--muted);font-size:13px}
main{max-width:1400px;margin:0 auto;padding:12px}
.tabs{display:flex;flex-wrap:wrap;gap:2px;border-bottom:1px solid var(--border);
  margin-bottom:16px;background:var(--panel);padding:4px;border-radius:6px;}
.tab-btn{background:transparent;color:var(--muted);border:0;padding:9px 14px;cursor:pointer;
  border-radius:4px;font:inherit;font-size:13px;}
.tab-btn:hover{color:var(--text);background:#30363d}
.tab-btn.active{background:var(--accent);color:#000;font-weight:600}
.tab-pane{display:none}
.tab-pane.active{display:block}
.card{background:var(--panel);border:1px solid var(--border);border-radius:8px;
  padding:16px;margin-bottom:16px}
.card h2{margin-top:0;color:var(--accent);border-bottom:1px solid var(--border);padding-bottom:6px}
.card h3{color:var(--accent);margin:18px 0 8px}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--border);vertical-align:top}
th{background:#0d1117;color:var(--muted);font-weight:600;text-transform:uppercase;font-size:11px;letter-spacing:0.5px}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;
  text-transform:uppercase;letter-spacing:0.3px;color:#fff}
.badge-primary{background:var(--primary)}
.badge-backup{background:var(--backup)}
.badge-skip{background:var(--skip);opacity:0.5}
.badge-hike{background:var(--hike)}
.badge-conditional{background:var(--conditional)}
.badge-logistics{background:var(--logistics)}
.badge-unclassified{background:var(--unclassified);opacity:0.6}
.camp-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}
.camp{background:#0d1117;border:1px solid var(--border);border-radius:6px;padding:12px;font-size:13px}
.camp-head{margin-bottom:4px}
.camp-primary{border-left:4px solid var(--primary)}
.camp-secondary{border-left:4px solid var(--backup)}
.camp-tertiary{border-left:4px solid var(--skip)}
.camp-meta{color:var(--muted);font-size:12px;margin-bottom:6px}
.summary-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-bottom:12px}
.summary-stat{background:#0d1117;border:1px solid var(--border);border-radius:6px;padding:10px 12px;}
.summary-stat .val{font-size:20px;font-weight:600;color:var(--accent)}
.summary-stat .lab{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:0.5px}
.map{height:400px;background:#0d1117;border:1px solid var(--border);border-radius:6px;margin:12px 0}
.map-wrap{position:relative;margin:12px 0}
.map-wrap .map{margin:0}
.map-fs-btn{position:absolute;top:10px;right:10px;z-index:1000;display:inline-flex;align-items:center;gap:6px;
  background:rgba(13,17,23,0.85);color:var(--fg);border:1px solid var(--border);border-radius:6px;
  padding:6px 10px;font:600 12px/1 system-ui,sans-serif;cursor:pointer;
  box-shadow:0 2px 6px rgba(0,0,0,0.4)}
.map-fs-btn:hover{background:rgba(31,111,235,0.85);border-color:#1f6feb;color:#fff}
.map-fs-btn .fs-icon{font-size:14px;line-height:1}
.map-fs-btn .fs-icon-exit{display:none}
.map-wrap.is-fullscreen .map-fs-btn .fs-icon-enter{display:none}
.map-wrap.is-fullscreen .map-fs-btn .fs-icon-exit{display:inline}
.map-wrap.is-fullscreen .map-fs-btn .fs-label::before{content:"Exit "}
/* Native :fullscreen pseudo-class makes the wrapper and inner map fill the viewport. */
.map-wrap:fullscreen,.map-wrap:-webkit-full-screen{width:100vw;height:100vh;background:#0d1117;padding:0;border-radius:0}
.map-wrap:fullscreen .map,.map-wrap:-webkit-full-screen .map{width:100%;height:100%;border-radius:0;border:0;margin:0}
.map-wrap:fullscreen .map-fs-btn,.map-wrap:-webkit-full-screen .map-fs-btn{top:14px;right:14px}
/* Fallback "max" mode when the browser denies native fullscreen. */
.map-wrap.is-fullscreen-fallback{position:fixed;inset:0;z-index:10000;width:100vw;height:100vh;margin:0;background:#0d1117;border-radius:0}
.map-wrap.is-fullscreen-fallback .map{width:100%;height:100%;border-radius:0;border:0;margin:0}
.map-wrap.is-fullscreen-fallback .map-fs-btn .fs-icon-enter{display:none}
.map-wrap.is-fullscreen-fallback .map-fs-btn .fs-icon-exit{display:inline}
.map-wrap.is-fullscreen-fallback .map-fs-btn .fs-label::before{content:"Exit "}
.map-offline-notice{padding:40px;color:var(--muted);text-align:center;font-style:italic}
.link-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:6px}
.link-grid a{display:block;background:#0d1117;border:1px solid var(--border);border-radius:4px;
  padding:8px 10px;font-size:13px}
.cat-head{color:var(--accent);margin-top:12px;margin-bottom:6px;font-size:13px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px}
.warn{background:#4d1a00;border:1px solid #c7450c;border-radius:6px;padding:10px 12px;margin:10px 0;color:#ffd7a8}
.info{background:#0b2239;border:1px solid #1f6feb;border-radius:6px;padding:10px 12px;margin:10px 0}
.muted{color:var(--muted)}
.two-col{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:16px}
ul.clean{margin:4px 0;padding-left:20px}
ul.clean li{margin:3px 0}
td.coords{font-size:12px;color:var(--muted);white-space:nowrap}
td.coords code{color:var(--text);font-size:11.5px;background:#0d1117;padding:1px 4px;border-radius:3px}
.camp-coords{font-size:12px;color:var(--muted);margin:4px 0 6px}
.camp-coords code{color:var(--text);background:#1b1f23;padding:1px 4px;border-radius:3px}
a.focus-map{color:var(--text);border-bottom:1px dashed var(--accent);text-decoration:none}
a.focus-map:hover{color:var(--accent);text-decoration:none}
.alerts-banner{padding:10px 14px;margin:10px 0 16px;border-radius:6px;border:1px solid var(--border);font-size:13px}
.alerts-loading{background:#1c2a3a;border-color:#1f6feb;color:var(--muted);font-style:italic}
.alerts-ok{background:#0f2918;border-color:#238636;color:#8be9c0}
.alerts-active{background:#4d1a00;border-color:#c7450c;color:#ffd7a8}
.alerts-offline{background:#202428;border-color:#57606a;color:var(--muted)}
.alerts-banner .alert-list{margin:8px 0 0;padding-left:20px;max-height:320px;overflow-y:auto}
.alerts-banner .alert-list li{margin:6px 0;font-size:12.5px;color:#ffe6c7}
.alerts-banner .alert-desc{color:var(--muted);font-size:12px;margin-top:2px}
.alerts-banner a{color:inherit;text-decoration:underline}
.leaflet-control-attribution{font-size:10px!important}
.schedule-controls{background:#0d1117;border:1px solid var(--border);border-left:4px solid var(--accent);
  border-radius:6px;padding:10px 12px;margin:0 0 14px;font-size:13px}
.schedule-controls .sched-row{display:flex;flex-wrap:wrap;align-items:center;gap:14px;margin-bottom:8px}
.schedule-controls label{display:inline-flex;align-items:center;gap:6px;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:0.4px}
.schedule-controls input[type="time"],.schedule-controls input[type="number"]{
  background:#1b1f23;color:var(--text);border:1px solid var(--border);border-radius:4px;
  padding:4px 6px;font:inherit;font-size:13px;width:84px}
.sched-mph{width:56px!important}
.sched-reset{background:#30363d;color:var(--text);border:1px solid var(--border);border-radius:4px;
  padding:4px 10px;font:inherit;font-size:12px;cursor:pointer}
.sched-reset:hover{background:#3d444c}
.sched-summary{font-size:13px;color:var(--text)}
.sched-summary strong{color:var(--accent)}
.sched-hint{margin-top:6px;font-size:11.5px;line-height:1.4}
input.poi-include{transform:scale(1.15);cursor:pointer}
input.poi-duration{width:56px;background:#1b1f23;color:var(--text);border:1px solid var(--border);
  border-radius:4px;padding:2px 4px;font:inherit;font-size:12px;text-align:right}
td.poi-eta strong{color:var(--accent)}
tr.skipped-row td:not(:first-child){opacity:0.45}
tr.skipped-row td.poi-eta{color:var(--muted)}
.spur-hint{font-size:11.5px;color:#ff9d45;margin-top:3px;font-style:italic;line-height:1.3}
tr.skipped-row .spur-hint{color:#8be9c0;font-style:normal}
tr.skipped-row .spur-hint::before{content:"[Saving] "}
.camp-eta{margin:6px 0;font-size:13px;color:var(--text)}
.camp-eta strong{color:var(--accent)}
.desc-btn{display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;
  margin-left:4px;padding:0;border:1px solid var(--border);border-radius:4px;
  background:#1b1f23;color:var(--muted);cursor:pointer;vertical-align:-3px;
  transition:background 0.1s,color 0.1s,border-color 0.1s}
.desc-btn:hover{background:#1f6feb;border-color:#1f6feb;color:#fff}
.desc-btn:focus-visible{outline:2px solid #1f6feb;outline-offset:1px}
.desc-btn svg{display:block}
#poi-desc-dialog{max-width:640px;width:90vw;padding:0;background:#24292f;color:var(--text);
  border:1px solid var(--border);border-radius:8px;box-shadow:0 12px 48px rgba(0,0,0,0.75)}
#poi-desc-dialog::backdrop{background:rgba(0,0,0,0.82);backdrop-filter:blur(3px)}
#poi-desc-dialog .dialog-head{display:flex;align-items:flex-start;gap:12px;
  padding:14px 16px;border-bottom:1px solid var(--border);background:#161b22}
#poi-desc-dialog .dialog-head h3{margin:0;font-size:16px;flex:1;color:var(--text);line-height:1.3}
#poi-desc-dialog .dialog-head .dialog-close{flex:none;background:transparent;border:0;color:var(--muted);
  font-size:22px;line-height:1;cursor:pointer;padding:0 4px}
#poi-desc-dialog .dialog-head .dialog-close:hover{color:var(--text)}
#poi-desc-dialog .dialog-sub{color:var(--muted);font-size:12px;margin-top:4px}
#poi-desc-dialog .dialog-sub code{font-size:11.5px}
#poi-desc-dialog .dialog-body{padding:14px 16px;max-height:60vh;overflow-y:auto;line-height:1.55;font-size:14px}
#poi-desc-dialog .dialog-body p{margin:0 0 10px}
#poi-desc-dialog .dialog-body p:last-child{margin-bottom:0}
#poi-desc-dialog .dialog-body .src{margin-top:14px;padding-top:10px;border-top:1px dashed var(--border);
  color:var(--muted);font-size:11.5px;font-style:italic}
.leaflet-div-icon.marker-icon{background:transparent!important;border:0!important}
.map-legend{background:rgba(13,17,23,0.88);border:1px solid var(--border);border-radius:6px;
  padding:6px 9px;color:var(--text);font-size:12px;line-height:1.4;backdrop-filter:blur(4px)}
.map-legend .legend-row{display:flex;align-items:center;gap:8px;margin:2px 0}
.map-legend .legend-swatch{display:inline-flex;align-items:center;justify-content:center;width:18px}
.map-legend .legend-dot{display:inline-block;width:12px;height:12px;border-radius:50%;
  box-shadow:0 1px 2px rgba(0,0,0,0.6)}
.map-legend .legend-line{display:inline-block;width:16px;height:3px;border-radius:2px}
.map-legend svg{display:block}

/* ----------------------------------------------------------------
 * Mobile / narrow-screen layout (phones up to ~iPhone Pro Max).
 * Key change: POI "stops" tables collapse into stacked cards since
 * 7-10 columns will not fit on a 375-430px wide screen. Each <td>
 * exposes its column name via the data-label attribute, which we
 * surface with a ::before pseudo-element. No JS changes required.
 * ---------------------------------------------------------------- */
@media (max-width:720px){
  /* Page chrome: tighter header + main padding */
  header{padding:10px 14px}
  header h1{font-size:18px}
  header .meta{font-size:12px}
  main{padding:8px}
  .card{padding:12px}
  .card h2{font-size:17px}
  .card h3{font-size:14px;margin-top:14px}

  /* Tab strip: single horizontally scrollable row instead of 3 wrap rows.
     Subtle right-edge mask hints that more tabs exist off-screen. */
  .tabs{flex-wrap:nowrap;overflow-x:auto;-webkit-overflow-scrolling:touch;
    scrollbar-width:thin;padding-bottom:2px;gap:1px;
    mask-image:linear-gradient(to right,#000 calc(100% - 20px),transparent);
    -webkit-mask-image:linear-gradient(to right,#000 calc(100% - 20px),transparent)}
  .tab-btn{flex:none;white-space:nowrap;padding:8px 11px;font-size:12px}

  /* POI tables: table -> stacked cards. We hide the <thead>, convert each
     <tr> into a card, and each <td> becomes a "Label: value" row using
     the data-label attribute. .td-name is promoted to a card title and
     .td-include / .td-duration float to the top-right as controls. */
  table.stops-table,
  table.stops-table tbody,
  table.stops-table tr,
  table.stops-table td{display:block;width:100%}
  table.stops-table{font-size:14px;border-collapse:separate}
  table.stops-table thead{display:none}
  table.stops-table tr{background:#0d1117;border:1px solid var(--border);
    border-radius:8px;padding:10px 12px;margin-bottom:10px;position:relative}
  table.stops-table td{padding:3px 0;border:0;text-align:left;white-space:normal}
  table.stops-table td.num{text-align:left}
  table.stops-table td::before{content:attr(data-label) ": ";color:var(--muted);
    font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:0.4px;
    margin-right:6px;display:inline-block}
  /* Prominent card title (Name). No label prefix. */
  table.stops-table td.td-name{font-size:16px;font-weight:600;line-height:1.35;
    margin:0 0 6px;padding-right:52px /* reserve space for .td-include float */ }
  table.stops-table td.td-name::before{display:none}
  table.stops-table td.td-name .focus-map{color:var(--text)}
  /* Checkbox floats to top-right corner of the card for easy thumb reach. */
  table.stops-table td.td-include{position:absolute;top:10px;right:12px;
    width:auto;padding:0;margin:0}
  table.stops-table td.td-include::before{display:none}
  table.stops-table td.td-include input{transform:scale(1.4)}
  /* Duration input stays inline with its label, but a touch bigger. */
  table.stops-table td.td-duration input{width:72px;font-size:14px;padding:4px 6px}
  /* Empty cells (no value) -> hide entirely on mobile to reduce noise. */
  table.stops-table td:empty{display:none}
  /* Coord cell wraps naturally on mobile. */
  table.stops-table td.coords{white-space:normal}
  table.stops-table td.coords code{white-space:nowrap}
  /* Spur hint sits under the name title, no extra indent. */
  table.stops-table td.td-name .spur-hint{margin-top:4px}

  /* Other tables (fuel stations, quick-ref) stay tabular
     but get a little denser. */
  table:not(.stops-table){font-size:12px}
  table:not(.stops-table) th,
  table:not(.stops-table) td{padding:5px 6px}

  /* Grids: let cards flow one-per-row at narrower widths. */
  .camp-grid{grid-template-columns:1fr}
  .summary-grid{grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px}
  .summary-stat{padding:8px 10px}
  .summary-stat .val{font-size:17px}

  /* Schedule controls: tighter gap, wrap label+input pairs together. */
  .schedule-controls{padding:8px 10px}
  .schedule-controls .sched-row{gap:10px;margin-bottom:6px}
  .schedule-controls label{font-size:11px}

  /* Map a touch shorter so more route-context fits above the fold. */
  .map{height:300px}
}

@media print{
  .tabs,.tab-btn{display:none}
  .tab-pane{display:block!important;page-break-before:always}
  .tab-pane:first-child{page-break-before:auto}
  body{background:#fff;color:#000}
  .card{background:#fff;border-color:#ccc;page-break-inside:avoid}
}
"""


# -----------------------------------------------------------------------------
# Day-Tabbed ITINERARY HTML
# -----------------------------------------------------------------------------
def build_itinerary_html():
    days = data['days']

    # Tab buttons
    tabs = []
    panes = []

    for i, d in enumerate(days):
        active = ' active' if i == 0 else ''
        tabs.append(
            f'<button class="tab-btn{active}" data-tgt="pane-{d["id"]}">{esc(d["label"])}</button>'
        )

        # POIs split by status for visibility
        pois = d.get('pois') or []
        primary = [p for p in pois if p['status'] in ('primary', 'hike_candidate', 'conditional')]
        backup = [p for p in pois if p['status'] == 'backup']
        skipped = [p for p in pois if p['status'] == 'skip']
        logistics = [p for p in pois if p['status'] == 'logistics']

        summary_stats = []
        if d.get('miles') is not None:
            summary_stats.append(('Miles', f'{d["miles"]}'))
        if d.get('driving_hours_est') is not None:
            summary_stats.append(('Drive hrs (est)', f'{d["driving_hours_est"]}'))
        summary_stats.append(('POI stops', f'{len(primary)} primary, {len(backup)} backup'))
        stat_html = ''.join(
            f'<div class="summary-stat"><div class="val">{esc(v)}</div><div class="lab">{esc(l)}</div></div>'
            for l, v in summary_stats
        )

        # A day qualifies for an embedded map if it has either a drivable
        # track OR at least one mappable marker (POI / camp). This lets
        # travel-staging days (e.g. Day 0) show their bonus stops and camp
        # options on the map even without a recorded track.
        def _has_coords(x):
            return isinstance(x, dict) and x.get('lat') and x.get('lon')

        day_has_map = (
            bool(d.get('_map_points'))
            or any(_has_coords(p) for p in pois)
            # Each tier may hold a dict OR a list of dicts; walk via the shared helper.
            or any(_camp_has_coords(c) for _, _, _, c in _iter_camp_entries(d.get('camps') or {}))
        )
        is_scheduled = bool(d.get('schedule'))

        # POI tables.
        # On scheduled days we merge primary + backup + hike_candidate into one
        # mile-sorted table with checkboxes and ETAs. On unscheduled days
        # (travel/transit/Moab) we keep the original split tables.
        poi_tables = []
        if is_scheduled:
            merged = sorted(
                [p for p in pois if p['status'] in ('primary', 'hike_candidate', 'conditional', 'backup')],
                key=lambda p: p['mile'],
            )
            if merged:
                poi_tables.append('<h3>Stops (primary + bonus, in route order)</h3>')
                poi_tables.append(f'<table class="stops-table">{POI_HEADER_SCHEDULED}<tbody>')
                day_mph = int((d.get('schedule') or {}).get('moving_mph') or 20)
                for i, p in enumerate(merged):
                    poi_tables.append(poi_row(p, day_id=d['id'], allow_focus=day_has_map,
                                              scheduled=True, idx=i, day_mph=day_mph))
                poi_tables.append('</tbody></table>')
        else:
            if primary:
                poi_tables.append('<h3>Primary Stops</h3>')
                poi_tables.append(f'<table class="stops-table">{POI_HEADER}<tbody>')
                poi_tables.extend(poi_row(p, day_id=d['id'], allow_focus=day_has_map) for p in primary)
                poi_tables.append('</tbody></table>')
            if backup:
                poi_tables.append('<h3>Backup / Bonus Stops</h3>')
                poi_tables.append(f'<table class="stops-table">{POI_HEADER}<tbody>')
                poi_tables.extend(poi_row(p, day_id=d['id'], allow_focus=day_has_map) for p in backup)
                poi_tables.append('</tbody></table>')

        # Hike-candidate warning for Day 3
        hike_warn = ''
        if any(p.get('status') == 'hike_candidate' for p in pois):
            hike_warn = (
                '<div class="warn"><strong>Day 3 hike decision:</strong> Two hikes kept as primary candidates '
                '(Wild Horse Window and Little Wild Horse Canyon narrows). Pick tactically on the day. '
                'See the reference doc for full side-by-side comparison and decision matrix. '
                'CRITICAL: Check flash-flood forecast before entering Little Wild Horse Canyon.'
                '</div>'
            )

        # Camps block
        camps = d.get('camps')
        camps_html = (
            camp_block(camps, day_id=d['id'], allow_focus=day_has_map, scheduled=is_scheduled)
            if camps else ''
        )

        # Schedule controls bar (only on scheduled days)
        sched_html = schedule_controls_html(d)

        # Map container
        map_id = f'map-{d["id"]}'
        has_map = day_has_map
        map_html = (
            f'<div class="map-wrap" id="map-wrap-{d["id"]}">'
            f'<button type="button" class="map-fs-btn" data-target="map-wrap-{d["id"]}" '
            f'title="Toggle fullscreen map (Esc to exit)" aria-label="Toggle fullscreen">'
            f'<span class="fs-icon fs-icon-enter" aria-hidden="true">&#x26F6;</span>'
            f'<span class="fs-icon fs-icon-exit" aria-hidden="true">&times;</span>'
            f'<span class="fs-label">Fullscreen</span></button>'
            f'<div id="{map_id}" class="map" data-day-id="{d["id"]}"><div class="map-offline-notice">'
            'Loading map... (requires internet for tiles; falls back to coordinates list if offline)'
            '</div></div></div>'
            if has_map else
            '<div class="info">No mapped track segment for this day (travel/transit/Moab day).</div>'
        )

        # Quick links for this day (weather + alerts)
        quick_links = []
        if d['type'] in ('overland', 'travel') and d['id'] != 'day0_travel':
            quick_links = [
                {'label': 'Swell weather (Wedge)',    'url': 'https://forecast.weather.gov/MapClick.php?lat=39.0985&lon=-110.7850'},
                {'label': 'SLC flash-flood info',     'url': 'https://www.weather.gov/slc/flashflood'},
                {'label': 'SLC active warnings',      'url': 'https://www.weather.gov/slc/WWA'},
                {'label': 'UDOT Region 4',            'url': 'https://x.com/UDOTRegion4'},
                {'label': 'Utah Fire Info',           'url': 'https://utahfireinfo.gov/'},
            ]
        elif d['type'] in ('moab', 'transit'):
            quick_links = [
                {'label': 'Moab weather',             'url': 'https://forecast.weather.gov/MapClick.php?lat=38.5733&lon=-109.5498'},
                {'label': 'Dead Horse Point weather', 'url': 'https://forecast.weather.gov/MapClick.php?lat=38.4710&lon=-109.7450'},
                {'label': 'GJT hazards (Moab)',       'url': 'https://www.weather.gov/gjt/hazards'},
                {'label': 'UDOT I-70/191',            'url': 'https://www.udottraffic.utah.gov/'},
                {'label': 'Arches NP alerts',         'url': 'https://www.nps.gov/arch/planyourvisit/conditions.htm'},
            ]
        elif d['id'] == 'day0_travel':
            quick_links = [
                {'label': 'Green River weather',      'url': 'https://forecast.weather.gov/MapClick.php?lat=38.9953&lon=-110.1599'},
                {'label': 'UDOT I-70',                'url': 'https://www.udottraffic.utah.gov/'},
                {'label': 'SLC active warnings',      'url': 'https://www.weather.gov/slc/WWA'},
            ]

        ql_html = ''
        if quick_links:
            ql_html = (
                '<h3>Real-time quick links</h3>'
                '<div class="link-grid">'
                + ''.join(f'<a href="{esc(l["url"])}" target="_blank">{esc(l["label"])}</a>' for l in quick_links)
                + '</div>'
            )

        pane = (
            f'<div class="tab-pane{active}" id="pane-{d["id"]}">'
            f'<div class="card">'
            f'<h2>{esc(d["title"])}</h2>'
            f'<div class="muted">{esc(d.get("descr", ""))}</div>'
            f'<div class="summary-grid">{stat_html}</div>'
            f'{hike_warn}'
            f'{sched_html}'
            f'{map_html}'
            f'{"".join(poi_tables)}'
            f'{camps_html}'
            f'{ql_html}'
            '</div>'
            '</div>'
        )
        panes.append(pane)

    # Build per-day map data payload (tracks + POI markers + origin/destination camps).
    # We walk days in order so each day's map can include the PRIOR day's primary camp
    # as an "origin" marker (cyan diamond) for orientation.
    map_payload = {}
    prev_primary_camp = None
    for d in data['days']:
        pts = d.get('_map_points') or []
        pois = d.get('pois') or []
        camps = d.get('camps') or {}
        markers = []

        # Origin: previous day's primary camp, if any and this day has a map
        if pts and prev_primary_camp:
            markers.append({
                'lat': prev_primary_camp['lat'],
                'lon': prev_primary_camp['lon'],
                'name': f'Origin (prev night): {prev_primary_camp["name"]}',
                'kind': 'camp_origin',
            })

        # POI marker selection depends on whether there's a driven track.
        #  - Track days: only primary + hike_candidate go on the map (backups
        #    clutter an already busy scheduled-day view).
        #  - Track-less days (e.g. Day 0 travel + stage): ALL coord-bearing
        #    POIs are shown, because there are fewer of them and the "backup"
        #    bonus stops are the entire point of the map.
        if pts:
            show_statuses = {'primary', 'hike_candidate'}
        else:
            show_statuses = {'primary', 'hike_candidate', 'backup', 'conditional'}
        for p in pois:
            if p['status'] in show_statuses and p.get('lat') and p.get('lon'):
                markers.append({'lat': p['lat'], 'lon': p['lon'], 'name': p['name'], 'kind': 'poi'})

        # End-of-day camps (primary / backup / last-resort).
        # Tiers can hold either a single dict OR a list of equal-rank sites
        # (e.g. the Wedge has 3 secondary designated sites). Walk via helper.
        for key, idx, total, c in _iter_camp_entries(camps):
            if not _camp_has_coords(c):
                continue
            label_prefix = _tier_label(key, idx, total)
            markers.append({
                'lat': c['lat'], 'lon': c['lon'],
                'name': f'Camp ({label_prefix.lower()}): {c["name"]}',
                'kind': f'camp_{key}',
            })
            # Primary tiers may define `cluster_members`: additional designated
            # sites in the same cluster that we want pinned on the map as
            # primary-tier options (without generating extra cards).
            if key == 'primary' and isinstance(c.get('cluster_members'), list):
                for m in c['cluster_members']:
                    if _camp_has_coords(m):
                        markers.append({
                            'lat': m['lat'], 'lon': m['lon'],
                            'name': f'Camp (primary cluster): {m["name"]}',
                            'kind': 'camp_primary',
                        })

        map_payload[d['id']] = {'track': pts, 'markers': markers}

        # Update rolling "previous primary camp" for the next day's origin marker.
        # When primary is a list (multiple equal-rank sites), anchor on the first
        # entry -- it's treated as the "nominal" landing spot.
        if isinstance(camps, dict):
            prim_val = camps.get('primary')
            prim = prim_val[0] if isinstance(prim_val, list) and prim_val else prim_val
            if _camp_has_coords(prim):
                prev_primary_camp = {
                    'lat': prim['lat'], 'lon': prim['lon'], 'name': prim['name'],
                }

    map_json = json.dumps(map_payload)

    # POI description dialog: map every POI name with a <desc> to its description + meta
    poi_desc_map = collect_poi_descriptions(data)
    poi_desc_json = json.dumps(poi_desc_map, ensure_ascii=False)
    poi_desc_dialog_js = POI_DESC_DIALOG_JS.format(desc_json=poi_desc_json)

    # Offline tiles: base64 data URIs keyed by "z/x/y" (empty dict if never
    # downloaded). See scripts/download_offline_tiles.py.
    offline_tiles_json = json.dumps(OFFLINE_TILES)

    html_out = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<title>2026 San Rafael Swell + Moab - Itinerary</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
{PWA_HEAD}
<style>{LEAFLET_CSS}</style>
<style>{CSS}</style>
<!-- Inline Leaflet 1.9.4 so the map engine is available before any inline
     script that references `L` (e.g. `L.TileLayer.extend(...)`). -->
<script>{LEAFLET_JS}</script>
</head><body>
<header>
<h1>2026 San Rafael Swell Adventure + Moab</h1>
<div class="meta">May 2 - May 10, 2026 &middot; 11 overlanders + 7 Moab &middot; Route: ~225 mi &middot;
<a href="trip-reference.html">Open reference doc</a> &middot;
<a href="trip-plan.gpx" download>Download GPX</a></div>
</header>
<main>
<div class="tabs" role="tablist">{''.join(tabs)}</div>
{''.join(panes)}
<section class="card" style="margin-top:24px">
<h2>Live NWS Utah alerts</h2>
<div class="muted" style="margin-bottom:8px">Fetched live when online; ignore if viewing offline. Use the per-day weather links above when connectivity is available.</div>
<div id="live-alerts" class="alerts-banner alerts-loading">Checking live NWS Utah alerts...</div>
</section>
{POI_DESC_DIALOG_HTML}
</main>
<script>
const TAB_BTNS = document.querySelectorAll('.tab-btn');
const PANES = document.querySelectorAll('.tab-pane');
function activateTab(dayId) {{
  const btn = document.querySelector('.tab-btn[data-tgt="pane-' + dayId + '"]');
  const pane = document.getElementById('pane-' + dayId);
  if (!btn || !pane) return false;
  TAB_BTNS.forEach(x => x.classList.remove('active'));
  PANES.forEach(x => x.classList.remove('active'));
  btn.classList.add('active');
  pane.classList.add('active');
  return true;
}}
TAB_BTNS.forEach(b => b.addEventListener('click', () => {{
  activateTab(b.dataset.tgt.replace('pane-',''));
  setTimeout(() => ensureMap(b.dataset.tgt.replace('pane-','')), 30);
}}));

const MAP_DATA = {map_json};
const MAPS = {{}};

function esriLayer(name) {{
  // Online Esri tile sources; we mark failed tiles transparent so the
  // underlying offline layer can show through when there's no connectivity.
  return L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/' + name + '/MapServer/tile/{{z}}/{{y}}/{{x}}',
    {{
      attribution: 'Tiles &copy; Esri',
      maxZoom: 19,
      errorTileUrl: TRANSPARENT_PNG,
      crossOrigin: true,
    }}
  );
}}

// ----- Offline low-res tile layer -----
// OFFLINE_TILES is a dict of {{ "z/x/y" : "data:image/png;base64,..." }} built at
// HTML-generation time from planning/offline_tiles/. It covers the full trip
// bbox at zoom 7-9 so the map still has a recognizable background when viewed
// offline. Higher zooms auto-stretch the z=9 tiles via maxNativeZoom.
const OFFLINE_TILES = {offline_tiles_json};
const TRANSPARENT_PNG = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=';
const OfflineTileLayer = L.TileLayer.extend({{
  getTileUrl: function(coords) {{
    const key = coords.z + '/' + coords.x + '/' + coords.y;
    return OFFLINE_TILES[key] || TRANSPARENT_PNG;
  }}
}});

function ensureMap(dayId) {{
  if (typeof L === 'undefined') return;
  const spec = MAP_DATA[dayId]; if (!spec) return;
  const hasTrack = spec.track && spec.track.length > 0;
  const hasMarkers = spec.markers && spec.markers.length > 0;
  // Allow track-less days (e.g. Day 0) to show a map framed around their
  // POI / camp markers. Only bail if BOTH are empty.
  if (!hasTrack && !hasMarkers) return;
  const elId = 'map-' + dayId; const el = document.getElementById(elId);
  if (!el || MAPS[dayId]) return;
  el.innerHTML = '';
  const m = L.map(elId);
  // Offline low-res tiles live in their own pane below the online tile pane
  // so Esri always renders on top when online, and shows through when Esri
  // tiles fail (errorTileUrl keeps failed tiles transparent). The offline
  // layer stays on at all times -- it's the background fallback.
  m.createPane('offlinePane');
  m.getPane('offlinePane').style.zIndex = 150;
  const offline = new OfflineTileLayer('', {{
    pane: 'offlinePane', minZoom: 0, maxZoom: 19, maxNativeZoom: 9,
    attribution: 'Offline baseline: &copy; OpenStreetMap contributors (cached)',
  }}).addTo(m);
  const topo = esriLayer('World_Topo_Map');
  const imagery = esriLayer('World_Imagery');
  const streets = esriLayer('World_Street_Map');
  topo.addTo(m);
  L.control.layers(
    {{'Topo (online)': topo, 'Satellite (online)': imagery, 'Street (online)': streets}},
    {{'Offline baseline (always on)': offline}},
    {{collapsed: true, position: 'topright'}}
  ).addTo(m);
  // Build an extensible bounds object so we can frame track + markers together.
  const bounds = L.latLngBounds([]);
  if (hasTrack) {{
    const line = L.polyline(spec.track, {{color:'#ff9d45', weight:3}}).addTo(m);
    bounds.extend(line.getBounds());
  }}
  spec.markers.forEach(mk => {{
    const mkr = buildMarker(mk);
    if (mkr) {{
      mkr.bindPopup(mk.name).addTo(m);
      bounds.extend([mk.lat, mk.lon]);
    }}
  }});
  if (bounds.isValid()) {{
    m.fitBounds(bounds, {{padding:[30,30], maxZoom: 14}});
  }} else {{
    m.setView([38.93, -110.42], 12);  // Black Dragon fallback
  }}
  addLegend(m);
  MAPS[dayId] = m;
}}

// ----- Custom marker shapes -----
// POIs = green filled circles. Camps = color-coded triangles (tent-shaped).
// Origin (previous night's camp) = cyan diamond so it stands out from end-of-day camps.
function _svgTriangle(color, size) {{
  const s = size;
  return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" width="' + s +
    '" height="' + s + '" style="display:block;filter:drop-shadow(0 1px 2px rgba(0,0,0,0.6))">' +
    '<polygon points="10,2 18,17 2,17" fill="' + color +
    '" stroke="#0d1117" stroke-width="2" stroke-linejoin="round"/></svg>';
}}
function _svgDiamond(color, size) {{
  const s = size;
  return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" width="' + s +
    '" height="' + s + '" style="display:block;filter:drop-shadow(0 1px 2px rgba(0,0,0,0.6))">' +
    '<polygon points="10,1 19,10 10,19 1,10" fill="' + color +
    '" stroke="#0d1117" stroke-width="2" stroke-linejoin="round"/></svg>';
}}
const MARKER_STYLE = {{
  poi:             {{kind: 'circle',  color: '#238636', radius: 6, label: 'Stop'}},
  camp_primary:    {{kind: 'tri',     color: '#a371f7', size: 20,  label: 'Camp (primary)'}},
  camp_secondary:  {{kind: 'tri',     color: '#e3a008', size: 18,  label: 'Camp (backup)'}},
  camp_tertiary:   {{kind: 'tri',     color: '#8b949e', size: 16,  label: 'Camp (last-resort)'}},
  camp_origin:     {{kind: 'diamond', color: '#56d4f5', size: 22,  label: 'Origin (prior night\\'s camp)'}},
}};
function buildMarker(mk) {{
  const st = MARKER_STYLE[mk.kind] || MARKER_STYLE.poi;
  if (st.kind === 'circle') {{
    return L.circleMarker([mk.lat, mk.lon], {{
      radius: st.radius, color: st.color, weight: 2,
      fillColor: st.color, fillOpacity: 0.8
    }});
  }}
  const svg = (st.kind === 'diamond' ? _svgDiamond : _svgTriangle)(st.color, st.size);
  const icon = L.divIcon({{
    html: svg,
    className: 'marker-icon marker-' + mk.kind,
    iconSize: [st.size, st.size],
    iconAnchor: [st.size / 2, st.size / 2],
    popupAnchor: [0, -st.size / 2],
  }});
  return L.marker([mk.lat, mk.lon], {{icon: icon}});
}}

// ----- Map legend -----
function addLegend(m) {{
  const legend = L.control({{position: 'bottomleft'}});
  legend.onAdd = function() {{
    const div = L.DomUtil.create('div', 'map-legend');
    const row = (swatch, text) =>
      '<div class="legend-row"><span class="legend-swatch">' + swatch + '</span>' +
      '<span>' + text + '</span></div>';
    div.innerHTML =
      row('<span class="legend-dot" style="background:#238636"></span>', 'Primary stop / hike') +
      row(_svgTriangle('#a371f7', 14), 'Camp (primary)') +
      row(_svgTriangle('#e3a008', 14), 'Camp (backup)') +
      row(_svgTriangle('#8b949e', 14), 'Camp (last-resort)') +
      row(_svgDiamond('#56d4f5', 14), "Origin (prior night's camp)") +
      '<div class="legend-row"><span class="legend-swatch">' +
        '<span class="legend-line" style="background:#ff9d45"></span>' +
      '</span><span>Route track</span></div>';
    L.DomEvent.disableClickPropagation(div);
    return div;
  }};
  legend.addTo(m);
}}

function focusMap(dayId, lat, lon) {{
  activateTab(dayId);
  ensureMap(dayId);
  const m = MAPS[dayId];
  if (m) {{
    m.flyTo([lat, lon], 15, {{duration: 0.6}});
    const mapEl = document.getElementById('map-' + dayId);
    if (mapEl) mapEl.scrollIntoView({{behavior: 'smooth', block: 'center'}});
  }} else {{
    window.open('https://www.google.com/maps/search/?api=1&query=' + lat + ',' + lon, '_blank');
  }}
}}
document.addEventListener('click', function(e) {{
  const a = e.target.closest('a.focus-map');
  if (!a) return;
  e.preventDefault();
  focusMap(a.dataset.day, parseFloat(a.dataset.lat), parseFloat(a.dataset.lon));
}});

// ----- Map fullscreen toggle (native Fullscreen API; works offline) -----
function _fsRequest(el) {{
  if (el.requestFullscreen) return el.requestFullscreen();
  if (el.webkitRequestFullscreen) return el.webkitRequestFullscreen();
  if (el.msRequestFullscreen) return el.msRequestFullscreen();
}}
function _fsExit() {{
  if (document.exitFullscreen) return document.exitFullscreen();
  if (document.webkitExitFullscreen) return document.webkitExitFullscreen();
  if (document.msExitFullscreen) return document.msExitFullscreen();
}}
function _fsElement() {{
  return document.fullscreenElement || document.webkitFullscreenElement || document.msFullscreenElement || null;
}}
document.addEventListener('click', function(e) {{
  const btn = e.target.closest('.map-fs-btn');
  if (!btn) return;
  e.preventDefault();
  const wrap = document.getElementById(btn.dataset.target);
  if (!wrap) return;
  const dayId = wrap.querySelector('.map').dataset.dayId;
  ensureMap(dayId);
  if (_fsElement() === wrap) {{
    _fsExit();
  }} else {{
    const p = _fsRequest(wrap);
    if (p && p.catch) p.catch(() => {{
      // Fallback: if native fullscreen is denied (rare), use a CSS-only "max" mode.
      wrap.classList.toggle('is-fullscreen-fallback');
      const mm = MAPS[dayId];
      if (mm) setTimeout(() => mm.invalidateSize(), 50);
    }});
  }}
}});
function _fsChange() {{
  const fsEl = _fsElement();
  document.querySelectorAll('.map-wrap').forEach(w => w.classList.remove('is-fullscreen'));
  if (fsEl && fsEl.classList && fsEl.classList.contains('map-wrap')) {{
    fsEl.classList.add('is-fullscreen');
  }}
  // Tell Leaflet the container changed size so it repaints + recenters.
  Object.keys(MAPS).forEach(k => {{
    const m = MAPS[k];
    if (m) setTimeout(() => m.invalidateSize(), 80);
  }});
}}
document.addEventListener('fullscreenchange', _fsChange);
document.addEventListener('webkitfullscreenchange', _fsChange);
document.addEventListener('msfullscreenchange', _fsChange);

// ----- Live NWS Utah alerts (CORS-enabled public API) -----
function escHTML(s){{return String(s==null?'':s).replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));}}
async function loadAlerts() {{
  const el = document.getElementById('live-alerts');
  if (!el) return;
  try {{
    const r = await fetch('https://api.weather.gov/alerts/active?area=UT', {{
      headers: {{'Accept': 'application/geo+json'}}
    }});
    if (!r.ok) throw new Error('NWS HTTP ' + r.status);
    const j = await r.json();
    const feats = j.features || [];
    const now = new Date().toLocaleString();
    if (!feats.length) {{
      el.classList.remove('alerts-loading');
      el.classList.add('alerts-ok');
      el.innerHTML = '<strong>No active NWS alerts for Utah.</strong> <span class="muted">Checked ' + escHTML(now) + '. <a href="https://www.weather.gov/slc/WWA" target="_blank" rel="noopener">Full alert feed</a></span>';
      return;
    }}
    const rank = e => /Flash Flood Warning/i.test(e)?0:/Flood Warning/i.test(e)?1:/Severe Thunderstorm Warning/i.test(e)?2:/Warning/i.test(e)?3:/Red Flag/i.test(e)?4:/Watch/i.test(e)?5:/Advisory/i.test(e)?6:7;
    feats.sort((a,b)=>rank(a.properties.event||'')-rank(b.properties.event||''));
    const rows = feats.map(f => {{
      const p = f.properties || {{}};
      const sev = p.severity || '';
      const exp = p.expires ? new Date(p.expires).toLocaleString() : '';
      return '<li><strong>' + escHTML(p.event) + '</strong> &middot; <span class="muted">' + escHTML(sev) + '</span> &middot; ' + escHTML(p.areaDesc || '') + (exp ? ' &middot; <em>expires ' + escHTML(exp) + '</em>' : '') + (p.headline ? '<div class="alert-desc">' + escHTML(p.headline) + '</div>' : '') + '</li>';
    }}).join('');
    el.classList.remove('alerts-loading');
    el.classList.add('alerts-active');
    el.innerHTML = '<strong>' + feats.length + ' active NWS Utah alert' + (feats.length===1?'':'s') + '.</strong> <span class="muted">Fetched ' + escHTML(now) + '. <a href="#" id="alerts-toggle">show/hide</a> &middot; <a href="https://www.weather.gov/slc/WWA" target="_blank" rel="noopener">full feed</a></span><ul class="alert-list" id="alerts-list">' + rows + '</ul>';
    const tog = document.getElementById('alerts-toggle');
    if (tog) tog.addEventListener('click', function(e){{e.preventDefault();const ul=document.getElementById('alerts-list');if(ul)ul.style.display=ul.style.display==='none'?'':'none';}});
  }} catch (err) {{
    el.classList.remove('alerts-loading');
    el.classList.add('alerts-offline');
    el.innerHTML = '<strong>Live alert check unavailable</strong> <span class="muted">(' + escHTML(err.message) + '). Use the real-time links below when online.</span>';
  }}
}}
loadAlerts();

// ----- Per-day scheduler (checkbox + ETA + duration; localStorage-persisted) -----
function _hav_mi(lat1, lon1, lat2, lon2) {{
  const R = 3958.7613;
  const tr = x => x * Math.PI / 180;
  const dLa = tr(lat2 - lat1), dLo = tr(lon2 - lon1);
  const a = Math.sin(dLa/2)**2 + Math.cos(tr(lat1))*Math.cos(tr(lat2))*Math.sin(dLo/2)**2;
  return 2 * R * Math.asin(Math.sqrt(a));
}}
function _fmtTime(min) {{
  if (!isFinite(min)) return '--';
  const total = Math.round(min);
  const h = Math.floor(total / 60) % 24;
  const m = ((total % 60) + 60) % 60;
  const am = h < 12 ? 'AM' : 'PM';
  const h12 = ((h + 11) % 12) + 1;
  return h12 + ':' + String(m).padStart(2, '0') + ' ' + am;
}}
function _fmtDur(min) {{
  if (!isFinite(min) || min < 0) return '--';
  const total = Math.round(min);
  const h = Math.floor(total / 60);
  const m = total % 60;
  if (h > 0) return h + 'h ' + m + 'm';
  return m + 'm';
}}
function _parseHHMM(s) {{
  const m = (s || '').match(/^(\\d{{1,2}}):(\\d{{2}})$/);
  if (!m) return 9 * 60;
  return (parseInt(m[1], 10) || 0) * 60 + (parseInt(m[2], 10) || 0);
}}
function _schedKey(dayId) {{ return 'sched-v1-' + dayId; }}
function _loadSched(dayId) {{
  try {{ return JSON.parse(localStorage.getItem(_schedKey(dayId)) || 'null'); }}
  catch (e) {{ return null; }}
}}
function _saveSched(dayId, state) {{
  try {{ localStorage.setItem(_schedKey(dayId), JSON.stringify(state)); }} catch (e) {{}}
}}

function recomputeSchedule(dayId) {{
  const ctrl = document.querySelector('.schedule-controls[data-day="' + dayId + '"]');
  if (!ctrl) return;
  const pane = document.getElementById('pane-' + dayId);
  if (!pane) return;
  const startInput = ctrl.querySelector('.sched-start');
  const mphInput = ctrl.querySelector('.sched-mph');
  const startMin = _parseHHMM(startInput.value);
  const mph = Math.max(3, parseFloat(mphInput.value) || 1);
  const startLat = parseFloat(ctrl.dataset.startLat);
  const startLon = parseFloat(ctrl.dataset.startLon);
  const miLo = parseFloat(ctrl.dataset.miLo) || 0;

  const rows = pane.querySelectorAll('tr[data-poi-id]');
  let prevMile = miLo;
  let prevLat = startLat, prevLon = startLon;
  let cur = startMin;
  let driveTotal = 0, stopTotal = 0, includedCount = 0;
  // Miles we avoid driving because an upstream spur POI was un-checked.
  // Accumulated on skipped-spur rows, consumed by the next included leg (and
  // by the final camp leg if no later stops were included).
  let pendingSpurSaveMi = 0;
  rows.forEach(tr => {{
    const include = tr.querySelector('.poi-include').checked;
    const etaCell = tr.querySelector('.poi-eta');
    const durInput = tr.querySelector('.poi-duration');
    const mile = parseFloat(tr.dataset.mile);
    const lat = parseFloat(tr.dataset.lat);
    const lon = parseFloat(tr.dataset.lon);
    const offMi = (parseFloat(tr.dataset.offtrack) || 0) * 2 / 1609.344;
    const spurMi = parseFloat(tr.dataset.spurMi) || 0;
    if (!include) {{
      // If this was an on-spur stop, credit its round-trip miles toward the
      // next included leg. Dwell time is already excluded by skipping the row.
      pendingSpurSaveMi += spurMi;
      etaCell.innerHTML = '<span class="muted">skipped</span>';
      tr.classList.add('skipped-row');
      return;
    }}
    tr.classList.remove('skipped-row');
    const rawLegMi = Math.max(0, mile - prevMile) + offMi;
    const legMi = Math.max(0, rawLegMi - pendingSpurSaveMi);
    pendingSpurSaveMi = 0;   // consumed
    const legMin = legMi / mph * 60;
    cur += legMin;
    driveTotal += legMin;
    etaCell.innerHTML = '<strong>' + _fmtTime(cur) + '</strong>';
    const dur = Math.max(0, parseFloat(durInput.value) || 0);
    cur += dur;
    stopTotal += dur;
    includedCount += 1;
    prevMile = mile;
    prevLat = lat;
    prevLon = lon;
  }});

  // Camp ETAs. The straight-line estimate from the last included stop to camp
  // already ignores any skipped-spur detour (we're not on the spur anymore),
  // so we do not apply pendingSpurSaveMi here. It's only meaningful between
  // two track-mile anchored stops. For the same reason we don't carry it into
  // the next day's computation.
  let primaryCampEta = null;
  pane.querySelectorAll('.camp[data-camp-tier]').forEach(camp => {{
    if (camp.dataset.day !== dayId) return;
    const cLat = parseFloat(camp.dataset.lat);
    const cLon = parseFloat(camp.dataset.lon);
    if (!isFinite(cLat) || !isFinite(cLon)) return;
    const distMi = _hav_mi(prevLat, prevLon, cLat, cLon) * 1.3;
    const legMin = distMi / mph * 60;
    const eta = cur + legMin;
    const span = camp.querySelector('.camp-eta-val');
    if (span) span.textContent = _fmtTime(eta);
    if (camp.dataset.campTier === 'primary') primaryCampEta = eta;
  }});

  ctrl.querySelector('.sched-count').textContent = String(includedCount);
  ctrl.querySelector('.sched-stop-time').textContent = _fmtDur(stopTotal);
  ctrl.querySelector('.sched-drive-time').textContent = _fmtDur(driveTotal);
  ctrl.querySelector('.sched-day-total').textContent = _fmtDur(stopTotal + driveTotal);
  ctrl.querySelector('.sched-camp-eta').textContent =
    primaryCampEta != null ? _fmtTime(primaryCampEta) : '--';

  const state = {{ start: startInput.value, mph: mphInput.value, stops: {{}} }};
  rows.forEach(tr => {{
    state.stops[tr.dataset.poiId] = {{
      checked: tr.querySelector('.poi-include').checked,
      duration: parseFloat(tr.querySelector('.poi-duration').value) || 0,
    }};
  }});
  _saveSched(dayId, state);
}}

function attachSchedule(ctrl) {{
  const dayId = ctrl.dataset.day;
  const pane = document.getElementById('pane-' + dayId);
  if (!pane) return;
  const state = _loadSched(dayId);
  if (state) {{
    if (state.start) ctrl.querySelector('.sched-start').value = state.start;
    if (state.mph) ctrl.querySelector('.sched-mph').value = state.mph;
    pane.querySelectorAll('tr[data-poi-id]').forEach(tr => {{
      const s = state.stops && state.stops[tr.dataset.poiId];
      if (!s) return;
      tr.querySelector('.poi-include').checked = !!s.checked;
      if (s.duration != null) tr.querySelector('.poi-duration').value = s.duration;
    }});
  }}
  const rerun = () => recomputeSchedule(dayId);
  ctrl.querySelector('.sched-start').addEventListener('input', rerun);
  ctrl.querySelector('.sched-mph').addEventListener('input', rerun);
  pane.querySelectorAll('tr[data-poi-id] .poi-include, tr[data-poi-id] .poi-duration')
    .forEach(el => {{ el.addEventListener('input', rerun); el.addEventListener('change', rerun); }});
  ctrl.querySelector('.sched-reset').addEventListener('click', () => {{
    try {{ localStorage.removeItem(_schedKey(dayId)); }} catch (e) {{}}
    ctrl.querySelector('.sched-start').value = ctrl.dataset.defaultBreak;
    ctrl.querySelector('.sched-mph').value = ctrl.dataset.defaultMph;
    pane.querySelectorAll('tr[data-poi-id]').forEach(tr => {{
      tr.querySelector('.poi-include').checked = tr.dataset.defaultChecked === 'true';
      tr.querySelector('.poi-duration').value = tr.dataset.defaultDuration;
    }});
    rerun();
  }});
  rerun();
}}
document.querySelectorAll('.schedule-controls').forEach(attachSchedule);

{poi_desc_dialog_js}

// Leaflet is inlined in <head>, so `L` is already defined by the time this
// script runs. Kick off the first-tab map immediately.
if (typeof L !== 'undefined') {{
  ensureMap('{days[0]["id"]}');
}} else {{
  document.querySelectorAll('.map-offline-notice').forEach(el => {{
    el.textContent = 'Map engine failed to load. Refer to GPX or printed maps. Textual content is fully usable.';
  }});
}}
</script>
{PWA_REGISTER_JS}
</body></html>
"""
    return html_out


# -----------------------------------------------------------------------------
# Full REFERENCE HTML (everything in one linear document)
# -----------------------------------------------------------------------------
def build_reference_html():
    # Real-time links grouped by category
    rt_by_cat = {}
    for l in data['realtime_links']:
        rt_by_cat.setdefault(l['cat'], []).append(l)
    rt_html = ''
    for cat, links in rt_by_cat.items():
        rt_html += f'<div class="cat-head">{esc(cat)}</div><div class="link-grid">'
        for l in links:
            rt_html += f'<a href="{esc(l["url"])}" target="_blank">{esc(l["label"])}</a>'
        rt_html += '</div>'

    # Fuel section
    fp = data['fuel']
    sb = fp['surface_breakdown']
    stations_html = '<table><thead><tr><th>Station</th><th>Role</th><th>Brands</th></tr></thead><tbody>'
    for s in fp['stations']:
        stations_html += f'<tr><td>{esc(s["name"])}</td><td>{esc(s["role"])}</td><td>{esc(s["brands"])}</td></tr>'
    stations_html += '</tbody></table>'

    surface_html = f"""
<table>
<thead><tr><th>Surface</th><th>Miles</th><th>MPG factor</th></tr></thead>
<tbody>
<tr><td>Paved highway</td><td class="num">{sb["paved_hwy_mi"]}</td><td class="num">{fp["mpg_factors"]["paved_hwy_65mph"]:.2f}</td></tr>
<tr><td>Graded dirt</td><td class="num">{sb["graded_dirt_mi"]}</td><td class="num">{fp["mpg_factors"]["graded_dirt"]:.2f}</td></tr>
<tr><td>Rocky 2-track</td><td class="num">{sb["rocky_2track_mi"]}</td><td class="num">{fp["mpg_factors"]["rocky_2track"]:.2f}</td></tr>
<tr><td>Technical low-range</td><td class="num">{sb["technical_mi"]}</td><td class="num">{fp["mpg_factors"]["technical_low_range"]:.2f}</td></tr>
<tr><td><strong>Total route</strong></td><td class="num"><strong>{sb["total_mi"]}</strong></td><td></td></tr>
</tbody>
</table>
<p>Estimated Swell fuel burn (baseline 16 MPG): <strong>~{fp["estimated_swell_gallons_16mpg_baseline"]} gallons</strong>. Plan aux fuel or detours accordingly; see the detailed <a href="planning/fuel_plan.md">fuel_plan.md</a> for per-vehicle worksheet.</p>
"""

    # Day-by-day full dump (no tabs here)
    day_sections = []
    for d in data['days']:
        pois = d.get('pois') or []
        # Full POI table incl. skips for reference
        poi_html = ''
        if pois:
            poi_html = (
                f'<table class="stops-table">{POI_HEADER}<tbody>'
                + ''.join(poi_row(p) for p in pois)
                + '</tbody></table>'
            )

        camps_html = camp_block(d.get('camps'), 'Camping options (primary / secondary / tertiary)') if d.get('camps') else ''

        day_sections.append(
            f'<div class="card" id="{d["id"]}">'
            f'<h2>{esc(d["label"])}</h2>'
            f'<p>{esc(d.get("title", ""))} &mdash; {esc(d.get("descr", ""))}</p>'
            f'<p class="muted">Miles: {d.get("miles") or "--"} &middot; Driving (est): {d.get("driving_hours_est") or "--"} hrs</p>'
            f'{poi_html}'
            f'{camps_html}'
            '</div>'
        )

    # Day 3 hike detail (critical reference)
    hike_detail = """
<div class="card" id="day3-hikes">
<h2>Day 3 Hike Decision (Tactical)</h2>
<p class="muted">Both hikes are kept in the plan as primary candidates. Pick on the day based on schedule, weather, group energy, and interest.</p>

<div class="two-col">
<div>
<h3>Wild Horse Window (a.k.a. "Eye of Sinbad")</h3>
<table>
<tr><th>Type</th><td>Natural bridge with 35x22 ft skylight (cave-style)</td></tr>
<tr><th>Trailhead</th><td>38.6475, -110.6628</td></tr>
<tr><th>Arch</th><td>38.6533, -110.6764 (hike west from TH)</td></tr>
<tr><th>Distance</th><td>~2 mi round trip</td></tr>
<tr><th>Elevation</th><td>200-335 ft</td></tr>
<tr><th>Time</th><td>1-2 hrs</td></tr>
<tr><th>Difficulty</th><td>Easy</td></tr>
<tr><th>Trail</th><td>None - cross-country slickrock with cairns</td></tr>
<tr><th>Shade</th><td>Zero; carry >=1 L water/person</td></tr>
<tr><th>Dogs</th><td>Allowed (leash recommended)</td></tr>
<tr><th>Why go</th><td>Route author's explicit "#1 geological site"; unique cave-bridge hybrid; petroglyphs on R wall (some fake)</td></tr>
<tr><th>Hazards</th><td>Heat/no shade; loose slickrock; faint trail -> carry GPS</td></tr>
</table>
</div>

<div>
<h3>Little Wild Horse Canyon (narrows out-and-back)</h3>
<table>
<tr><th>Type</th><td>Iconic Utah slot canyon with 400 ft walls</td></tr>
<tr><th>Trailhead</th><td>Standard LWH/Bell lot (signed)</td></tr>
<tr><th>Distance</th><td>2.5-4.5 mi RT (turn around when satisfied)</td></tr>
<tr><th>Time</th><td>1.5-2.5 hrs</td></tr>
<tr><th>Difficulty</th><td>Easy-moderate; one dryfall 0.4 mi in (scramble or bypass L slickrock)</td></tr>
<tr><th>Trail</th><td>Wash bottom; scrambles through narrows</td></tr>
<tr><th>Shade</th><td>Canyon walls = partial shade; cooler than open desert</td></tr>
<tr><th>Dogs</th><td>Allowed; must lift over a couple of obstacles</td></tr>
<tr><th>Why go</th><td>Most famous slot canyon in the Swell; dramatic scale</td></tr>
<tr><th>Hazards</th><td><span class="badge badge-hike">EXTREME FLASH FLOOD RISK</span> - do NOT enter if any rain forecast on the Reef. Fatal May 2020 event killed 21.</td></tr>
</table>
</div>
</div>

<h3>Field decision matrix</h3>
<table>
<thead><tr><th>Condition</th><th>Recommendation</th></tr></thead>
<tbody>
<tr><td>On schedule, good weather, energetic</td><td>Do LWH narrows; skip WHW</td></tr>
<tr><td>Any rain forecast (on Reef or upstream)</td><td>Do WHW (no flood exposure); skip LWH</td></tr>
<tr><td>Ahead of schedule + perfect weather</td><td>Do both - WHW morning, LWH after Behind-the-Reef</td></tr>
<tr><td>Behind schedule</td><td>Skip both, go straight to Temple Mtn camp</td></tr>
<tr><td>Want the signature "slot canyon" photo</td><td>LWH narrows</td></tr>
<tr><td>Want the route author's #1 pick</td><td>WHW</td></tr>
</tbody>
</table>
</div>
"""

    # Final emergency card
    emerg_html = """
<div class="card" id="emergency">
<h2>Emergency Contacts & Cell Coverage</h2>
<ul class="clean">
<li><strong>911</strong> - works where cell exists; via satellite messengers where it does not</li>
<li><strong>Emery County Sheriff / SAR (Swell)</strong>: <a href="tel:+14353812404">(435) 381-2404</a></li>
<li><strong>Grand County Sheriff (Moab)</strong>: <a href="tel:+14352598115">(435) 259-8115</a></li>
<li><strong>Utah Highway Patrol (I-70)</strong>: <a href="tel:+18018873800">(801) 887-3800</a></li>
<li><strong>BLM Price Field Office</strong>: <a href="tel:+14356363600">(435) 636-3600</a></li>
<li><strong>BLM Moab Field Office</strong>: <a href="tel:+14352592100">(435) 259-2100</a></li>
</ul>
<h3>Cell coverage realities</h3>
<ul class="clean">
<li>No coverage: Black Dragon Canyon interior, Buckhorn Draw, Reds Canyon, Behind-the-Reef, most canyon bottoms</li>
<li>Partial (Verizon/AT&T): top of Buckhorn Draw, Wedge Overlook (sometimes), Temple Mountain</li>
<li>Full: Green River, Moab, major I-70 / Hwy 191</li>
<li><strong>At least one satellite messenger (InReach/Zoleo/SPOT) required</strong> shared to a non-traveling contact</li>
</ul>
</div>
"""

    # POI description dialog: shared with itinerary (see build_itinerary_html)
    ref_poi_desc_map = collect_poi_descriptions(data)
    ref_poi_desc_json = json.dumps(ref_poi_desc_map, ensure_ascii=False)
    ref_poi_desc_dialog_js = POI_DESC_DIALOG_JS.format(desc_json=ref_poi_desc_json)

    html_out = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<title>2026 San Rafael Swell + Moab - Reference</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
{PWA_HEAD}
<style>{CSS}</style>
</head><body>
<header>
<h1>2026 San Rafael Swell Adventure + Moab - Reference</h1>
<div class="meta">May 2 - May 10, 2026 &middot; Full knowledge dump &middot;
<a href="trip-itinerary.html">Open daily itinerary</a> &middot;
<a href="trip-plan.gpx" download>Download GPX</a></div>
</header>
<main>

<div class="card">
<h2>Trip Overview</h2>
<div class="summary-grid">
<div class="summary-stat"><div class="val">{data["trip"]["route_total_miles"]:.0f}</div><div class="lab">Swell route miles</div></div>
<div class="summary-stat"><div class="val">9</div><div class="lab">Days on trip</div></div>
<div class="summary-stat"><div class="val">11</div><div class="lab">Overlanders</div></div>
<div class="summary-stat"><div class="val">7</div><div class="lab">Moab group</div></div>
<div class="summary-stat"><div class="val">4</div><div class="lab">Swell nights</div></div>
<div class="summary-stat"><div class="val">4</div><div class="lab">Moab nights</div></div>
</div>
<p><strong>Adventure rating:</strong> Epic. Peak technical rating: 4. Expect graded dirt with stretches of moderate jeep trails (Eva Conover, Behind the Reef, Eagle Canyon).</p>
</div>

<div class="card">
<h2>Real-Time Info Sources</h2>
<p class="muted">Bookmark all of these. Check weather / flash-flood alerts daily morning when connectivity is available. Full detail: <a href="planning/realtime_info_sources.md">realtime_info_sources.md</a>.</p>
{rt_html}
</div>

<div class="card">
<h2>Fuel Plan</h2>
<p>Route author: <em>"Be prepared to travel 250+ miles if you do the entire route without refueling."</em></p>
<h3>Fuel stations</h3>
{stations_html}
<h3>Route surface breakdown & MPG factors</h3>
{surface_html}
<p>Per-vehicle worksheet: see <a href="planning/fuel_plan.md">fuel_plan.md</a>. Each driver should fill in their baseline MPG, tank capacity, and aux fuel before the trip.</p>
</div>

{''.join(day_sections)}

{hike_detail}

{emerg_html}

<div class="card">
<h2>Source Files</h2>
<ul class="clean">
<li><a href="san-rafael-swell-adv-route-2025.gpx">Original route GPX (OTG Crew)</a></li>
<li><a href="Utah_Destinations_In_San_Rafael_Area.md">Utah_Destinations_In_San_Rafael_Area.md</a> (raw POI list)</li>
<li><a href="planning/poi_decisions.md">planning/poi_decisions.md</a> (locked POI triage)</li>
<li><a href="planning/campsite_plan.md">planning/campsite_plan.md</a> (camps + live availability check)</li>
<li><a href="planning/fuel_plan.md">planning/fuel_plan.md</a> (full fuel worksheet)</li>
<li><a href="planning/realtime_info_sources.md">planning/realtime_info_sources.md</a></li>
<li><a href="trip-plan.gpx" download>trip-plan.gpx</a> (derived route with day splits + camps labeled)</li>
</ul>
</div>

<div class="card">
<h2>Live NWS Utah alerts</h2>
<p class="muted">Fetched live when online; ignore if viewing offline. Use the per-day weather links above when connectivity is available.</p>
<div id="live-alerts" class="alerts-banner alerts-loading">Checking live NWS Utah alerts...</div>
</div>
{POI_DESC_DIALOG_HTML}
</main>
<script>
function escHTML(s){{return String(s==null?'':s).replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));}}
async function loadAlerts(){{
  const el=document.getElementById('live-alerts'); if(!el) return;
  try{{
    const r=await fetch('https://api.weather.gov/alerts/active?area=UT',{{headers:{{'Accept':'application/geo+json'}}}});
    if(!r.ok) throw new Error('NWS HTTP '+r.status);
    const j=await r.json(); const feats=j.features||[]; const now=new Date().toLocaleString();
    if(!feats.length){{ el.classList.remove('alerts-loading'); el.classList.add('alerts-ok');
      el.innerHTML='<strong>No active NWS alerts for Utah.</strong> <span class="muted">Checked '+escHTML(now)+'. <a href="https://www.weather.gov/slc/WWA" target="_blank" rel="noopener">Full feed</a></span>'; return; }}
    const rank=e=>/Flash Flood Warning/i.test(e)?0:/Flood Warning/i.test(e)?1:/Severe Thunderstorm Warning/i.test(e)?2:/Warning/i.test(e)?3:/Red Flag/i.test(e)?4:/Watch/i.test(e)?5:/Advisory/i.test(e)?6:7;
    feats.sort((a,b)=>rank(a.properties.event||'')-rank(b.properties.event||''));
    const rows=feats.map(f=>{{const p=f.properties||{{}};const exp=p.expires?new Date(p.expires).toLocaleString():'';
      return '<li><strong>'+escHTML(p.event)+'</strong> &middot; <span class="muted">'+escHTML(p.severity||'')+'</span> &middot; '+escHTML(p.areaDesc||'')+(exp?' &middot; <em>expires '+escHTML(exp)+'</em>':'')+(p.headline?'<div class="alert-desc">'+escHTML(p.headline)+'</div>':'')+'</li>';}}).join('');
    el.classList.remove('alerts-loading'); el.classList.add('alerts-active');
    el.innerHTML='<strong>'+feats.length+' active NWS Utah alert'+(feats.length===1?'':'s')+'.</strong> <span class="muted">Fetched '+escHTML(now)+'. <a href="https://www.weather.gov/slc/WWA" target="_blank" rel="noopener">Full feed</a></span><ul class="alert-list">'+rows+'</ul>';
  }}catch(err){{ el.classList.remove('alerts-loading'); el.classList.add('alerts-offline');
    el.innerHTML='<strong>Live alert check unavailable</strong> <span class="muted">('+escHTML(err.message)+'). See links above when online.</span>'; }}
}}
loadAlerts();
{ref_poi_desc_dialog_js}
</script>
{PWA_REGISTER_JS}
</body></html>
"""
    return html_out


# -----------------------------------------------------------------------------
# GPX export
# -----------------------------------------------------------------------------
def _gpx_esc(s):
    return (s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def build_gpx():
    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append('<gpx version="1.1" creator="build_deliverables.py" xmlns="http://www.topografix.com/GPX/1/1">')
    out.append(f'<metadata><name>2026 San Rafael Swell Trip Plan</name>'
               f'<desc>Day-split tracks, primary POIs, and primary/backup campsites for the May 2-10, 2026 trip.</desc>'
               f'<time>2026-04-16T00:00:00Z</time></metadata>')

    # Waypoints: POIs (primary / hike) + campsites (primary/secondary tagged).
    # Dedupe camps by (lat, lon) so Moab days that share camps don't repeat.
    seen_camps = set()
    for d in data['days']:
        for p in (d.get('pois') or []):
            if p['status'] in ('primary', 'hike_candidate', 'conditional', 'backup'):
                label_prefix = ''
                if p['status'] == 'backup':
                    label_prefix = '[BACKUP] '
                elif p['status'] == 'hike_candidate':
                    label_prefix = '[HIKE] '
                elif p['status'] == 'conditional':
                    label_prefix = '[IF NEEDED] '
                name = label_prefix + (p.get('name') or '')
                desc = p.get('note') or ''
                ele = p.get('ele')
                sym = p.get('sym') or ''
                lines = [
                    f'<wpt lat="{p["lat"]}" lon="{p["lon"]}">',
                    (f'<ele>{ele}</ele>' if ele is not None else ''),
                    f'<name>{_gpx_esc(name)}</name>',
                    (f'<desc>{_gpx_esc(desc)}</desc>' if desc else ''),
                    (f'<sym>{_gpx_esc(sym)}</sym>' if sym else ''),
                    '</wpt>',
                ]
                out.append(''.join(x for x in lines if x))

        camps = d.get('camps') or {}
        tag_base = {'primary': '[CAMP PRIMARY]', 'secondary': '[CAMP BACKUP]', 'tertiary': '[CAMP LAST-RESORT]'}
        for key, idx, total, c in _iter_camp_entries(camps):
            if not _camp_has_coords(c):
                continue
            camp_key = (round(c['lat'], 5), round(c['lon'], 5), key)
            if camp_key in seen_camps:
                continue
            seen_camps.add(camp_key)
            tag = tag_base[key]
            if total > 1:
                tag = tag[:-1] + f'-{chr(ord("A") + idx - 1)}]'
            name = f'{tag} {d["label"]} - {c.get("name", "")}'
            desc = (f'{c.get("cost", "")} | {c.get("facilities", "")} | {c.get("notes", "")} | Access: {c.get("access", "")}').strip(' |')
            lines = [
                f'<wpt lat="{c["lat"]}" lon="{c["lon"]}">',
                f'<name>{_gpx_esc(name)}</name>',
                f'<desc>{_gpx_esc(desc)}</desc>',
                '<sym>Campground</sym>',
                '</wpt>',
            ]
            out.append(''.join(lines))
            # Primary cluster members: emit each as its own waypoint so offline
            # mapping apps see the full cluster layout, not just the anchor.
            if key == 'primary' and isinstance(c.get('cluster_members'), list):
                for m in c['cluster_members']:
                    if not _camp_has_coords(m):
                        continue
                    m_key = (round(m['lat'], 5), round(m['lon'], 5), 'primary_cluster')
                    if m_key in seen_camps:
                        continue
                    seen_camps.add(m_key)
                    m_name = f'[CAMP PRIMARY-CLUSTER] {d["label"]} - {m.get("name", "")}'
                    m_desc = f'Designated site in the primary cluster anchored at {c.get("name", "")}'
                    out.append(''.join([
                        f'<wpt lat="{m["lat"]}" lon="{m["lon"]}">',
                        f'<name>{_gpx_esc(m_name)}</name>',
                        f'<desc>{_gpx_esc(m_desc)}</desc>',
                        '<sym>Campground</sym>',
                        '</wpt>',
                    ]))

    # Tracks: one <trk> per Swell day
    for d in data['days']:
        pts = d.get('track_points') or []
        if not pts:
            continue
        out.append(f'<trk><name>{_gpx_esc(d["label"])}</name><trkseg>')
        for lat, lon in pts:
            out.append(f'<trkpt lat="{lat}" lon="{lon}"></trkpt>')
        out.append('</trkseg></trk>')

    # Freeway Access alternate track
    alt = data.get('alternate_tracks', {}).get('freeway_access')
    if alt and alt.get('points'):
        out.append('<trk><name>[ALT] Freeway Access (bypass tunnel for tall rigs)</name><trkseg>')
        for lat, lon in alt['points']:
            out.append(f'<trkpt lat="{lat}" lon="{lon}"></trkpt>')
        out.append('</trkseg></trk>')

    out.append('</gpx>')
    return '\n'.join(out)


# -----------------------------------------------------------------------------
# Emit all
# -----------------------------------------------------------------------------
itin = build_itinerary_html()
(OUT_DIR / 'trip-itinerary.html').write_text(itin, encoding='utf-8')
print(f'Wrote trip-itinerary.html ({len(itin) / 1024:.1f} KB)')

ref = build_reference_html()
(OUT_DIR / 'trip-reference.html').write_text(ref, encoding='utf-8')
print(f'Wrote trip-reference.html ({len(ref) / 1024:.1f} KB)')

gpx = build_gpx()
(OUT_DIR / 'trip-plan.gpx').write_text(gpx, encoding='utf-8')
print(f'Wrote trip-plan.gpx ({len(gpx) / 1024:.1f} KB)')
