# 2026 San Rafael Swell Adventure + Moab

Trip planning workspace for the **May 2 - 10, 2026** overlanding trip to Utah.

- **11 overlanders** do the San Rafael Swell route (May 2-6)
- **7 of those continue** to Moab (May 6-10); rest head back to Boise May 6
- Route: OTG Crew 225-mi San Rafael Swell Adventure loop

This README is the "where is everything" index. Read it first any time you come back to make changes.

---

## For trip participants

The trip companion is a small offline web app -- install it on your phone once
on cell signal and it works in the Swell with no internet.

**Site:** https://glennpiper.github.io/sanrafael-swell-adventure-2026/
*(replace with your final Pages URL once the repo is created and deployed)*

**Scan to install:** see `assets/qr.png` after the first deploy generates it
(the landing page also displays the QR).

### iPhone / iPad

1. Open the site in **Safari** (must be Safari, not Chrome).
2. Tap **Share** (the square-with-up-arrow at the bottom).
3. Tap **Add to Home Screen** -> **Add**.
4. Open **SRS Trip** from the home screen, then open it once more on cell
   signal so it can finish caching the maps.

### Android

1. Open the site in **Chrome**.
2. Tap the menu (three dots) -> **Install app** (or **Add to Home screen**).
3. Open **SRS Trip** from the home screen, then open it once more on cell
   signal so it can finish caching the maps.

### Updates

When you make a new release (push to `main`), every installed phone shows a
small "New trip data available -- tap to reload" toast on its next online
launch. No app-store review, no manual file shuffling.

### What's in the app

- `trip-itinerary.html` -- daily-tabbed view with maps, POIs, camps, schedule
- `trip-reference.html` -- single-page knowledge dump (fuel, emergency,
  decision matrix, every camp + POI including backups, all real-time links)
- `trip-plan.gpx` -- import into Gaia / CalTopo / Garmin / OnX

---

## Primary deliverables (what the group actually uses)

These live at the **project root** and are regenerated from scripts. Do NOT hand-edit them.

| File | What it is | How to use |
|---|---|---|
| `trip-itinerary.html` | Daily-tabbed browser view. One tab per day with map, POIs, camps, quick real-time links. Offline-first (maps degrade gracefully if no internet). | Double-click to open in a browser. Share with group. |
| `trip-reference.html` | Full knowledge dump on one page: overview, fuel, camps (incl. backups), POIs (incl. skips), Day-3 hike decision matrix, emergency info, all real-time sources. | Utilitarian reference; print-friendly. |
| `trip-plan.gpx` | Route + labeled waypoints for Gaia / CalTopo / Garmin / OnX. 5 tracks (4 day splits + Freeway Access bypass). 59 waypoints tagged `[BACKUP]`, `[HIKE]`, `[CAMP PRIMARY]`, `[CAMP BACKUP]`, `[CAMP LAST-RESORT]`. | Import into your nav app before the trip. |

## Source planning files (the "why" behind each decision)

All inside `planning/`:

| File | Purpose |
|---|---|
| `poi_decisions.md` | Locked POI triage per day (primary / backup / skip / hike). Includes Day-3 Wild Horse Window vs. Little Wild Horse Canyon comparison and tactical decision matrix. |
| `campsite_plan.md` | Primary / secondary / tertiary camps per night. Built from live availability checks (see `check_availability.py`, `check_moab_availability.py`). |
| `fuel_plan.md` | Per-vehicle fuel worksheet, route surface breakdown, MPG factors, fuel stop locations (Green River, Castle Dale, Emery, Hanksville, Moab), group summary table. |
| `realtime_info_sources.md` | NWS point forecasts for each waypoint, UDOT, BLM, fire, water, emergency, and park alert links. |
| `poi_menu.md` | Original POI candidate list (now superseded by `poi_decisions.md`; retained for context). |
| `campsite_menu.md` | Original campsite candidate list (now superseded by `campsite_plan.md`). |
| `trip_data.json` | The single source-of-truth dataset that drives all three deliverables. Generated; do not hand-edit. |
| `route_analysis.json` / `route_waypoints.json` / `route_tracks.json` | Intermediate parsed GPX data. Generated. |
| `moab_availability_raw.txt` / `recgov_*.json` | Raw API responses from live availability checks. |

## Source inputs (what we started from)

| File | Purpose |
|---|---|
| `san-rafael-swell-adv-route-2025.gpx` | Source route GPX from the OTG Crew (133 waypoints, 3 tracks). |
| `Utah_Destinations_In_San_Rafael_Area.md` | Raw POI research notes. |
| `Planning prompt.md` | Original planning ask that seeded this project. |
| `Participants.md` (gitignored, local only) | Personal roster with phone numbers; never pushed to GitHub. |
| `Collected Location Info/` (gitignored) | Raw narrative + research source material; not needed by the build pipeline. |

---

## How to regenerate after changes

**Everything flows from `scripts/build_trip_data.py`** - that's where POI status, camps, fuel, and real-time links are defined in code.

### One-liner (full rebuild + verify)

```powershell
py scripts\build_trip_data.py
py scripts\build_deliverables.py
py scripts\verify_outputs.py
```

First-time setup also requires populating the offline map assets (runs once; idempotent thereafter):

```powershell
py scripts\download_offline_tiles.py
```

### Full publish-style rebuild (matches the CI flow)

```powershell
py scripts\build_trip_data.py
py scripts\build_pwa_icons.py        # needs: pip install pillow
py scripts\build_pwa_assets.py       # set $env:SITE_URL for the QR code; needs: pip install "qrcode[pil]"
py scripts\build_deliverables.py
```

Pushing to `main` triggers `.github/workflows/deploy.yml`, which runs all four build scripts in the same order, runs the secret-scan PII guard over the staged `_publish/` directory, and publishes the result to GitHub Pages.

### Script-by-script

| Script | Reads | Writes | When to run |
|---|---|---|---|
| `scripts/parse_route_gpx.py` | `san-rafael-swell-adv-route-2025.gpx` | `planning/route_waypoints.json`, `planning/route_tracks.json` | Only if the source GPX changes |
| `scripts/analyze_route.py` | `planning/route_*.json` | `planning/route_analysis.json` (waypoints ordered along track with mile + off-track distance) | Only if parsed GPX changes |
| `scripts/check_availability.py` | (live Recreation.gov API) | `planning/recgov_*.json`, console output | Anytime we want to re-check Swell campground status |
| `scripts/check_moab_availability.py` | (live Recreation.gov API) | `planning/moab_availability_raw.txt` | Anytime we want to re-check Moab camp status |
| **`scripts/build_trip_data.py`** | `planning/route_analysis.json`, `planning/route_tracks.json` + hardcoded `POI_STATUS` + `CAMPSITES` + `FUEL_PLAN_SUMMARY` + `REALTIME_LINKS` + `GROUP_COUNTS` | `planning/trip_data.json` | Anytime a POI, camp, link, or count changes |
| **`scripts/build_deliverables.py`** | `planning/trip_data.json` | `trip-itinerary.html`, `trip-reference.html`, `trip-plan.gpx` | After `build_trip_data.py` |
| `scripts/build_pwa_assets.py` | (env: `SITE_URL`) | `manifest.webmanifest`, `service-worker.js`, `robots.txt`, `assets/qr.png` | Each CI build (PWA shell + cache-bust) |
| `scripts/build_pwa_icons.py` | `assets/icon-source.svg` | `icons/icon-192.png`, `icon-512.png`, `icon-512-maskable.png`, `apple-touch-icon.png` | Whenever the icon source changes |
| `scripts/verify_outputs.py` | deliverables | console output | Sanity check (HTML balance, GPX parse, waypoint / track counts) |

The bold scripts are the two you'll touch 95% of the time.

---

## Common change recipes

### Change a POI's status (primary -> skip, etc.)

Edit `POI_STATUS` dict in `scripts/build_trip_data.py`. Keys are the exact waypoint names from the GPX (prefixed with `DP - ` for most). Values are `(status, note)` tuples where status is one of:

- `'primary'` - scheduled stop
- `'backup'` - fallback / bonus if time allows
- `'skip'` - intentionally not stopping (kept documented so we know we considered it)
- `'hike_candidate'` - on the tactical-decision menu (currently Day 3 only)
- `'conditional'` - stop only if a condition is met (rare)

Then rebuild. The status flows to:
- The HTML daily tabs (primary table / backup table / skip list)
- GPX waypoint name prefix (`[BACKUP]`, `[HIKE]`, etc.)
- `poi_decisions.md` is **not** auto-updated - if you want that file to stay canonical, update it by hand too (it's human-readable narrative; the script data is the source of truth for deliverables).

### Change a campsite

Edit `CAMPSITES` dict in `scripts/build_trip_data.py`. Each day key maps to `{primary, secondary, tertiary}` each with fields `name, lat, lon, kind, cost, facilities, notes, access, reserve_url (optional)`.

**Coordinate sourcing rule (important):** For any Swell overnight, **snap `lat`/`lon` to an actual `<sym>campsite-24</sym>` waypoint in `san-rafael-swell-adv-route-2025.gpx`** rather than estimating. The GPX has 67 mapped camp waypoints. Quick way to list them:

```powershell
py -c "import xml.etree.ElementTree as ET; ns={'g':'http://www.topografix.com/GPX/1/1'}; [print(f\"{w.find('g:name',ns).text:<40s} {w.get('lat')},{w.get('lon')}\") for w in ET.parse('san-rafael-swell-adv-route-2025.gpx').getroot().findall('g:wpt',ns) if (w.find('g:sym',ns) is not None and (w.find('g:sym',ns).text or '')=='campsite-24')]"
```

After editing, spot-check that each primary camp is within ~4 km of the relevant day's track start (Day 0) or end (Day 1-3) by rebuilding and opening the itinerary map. The camp should appear inside the day's map extent with no long leader line to the route. Moab-area camps aren't on the overland track; real ReserveAmerica / Recreation.gov coords are fine there.

For a Moab day that shares camps with another day, use `{'inherit': 'day5_moab'}`.

Then rebuild.

### Change fuel data (new station, different MPG factor)

Edit `FUEL_PLAN_SUMMARY` dict in `scripts/build_trip_data.py` for the embedded / HTML version. Edit `planning/fuel_plan.md` for the full per-vehicle worksheet (manually, not generated).

### Update the group counts

Edit `GROUP_COUNTS` in `scripts/build_trip_data.py` (overland / moab integers). The deliverables show counts only, never names. Keep `Participants.md` (gitignored, local only) in sync by hand for your own reference.

### Add a new real-time info link

Edit `REALTIME_LINKS` list in `scripts/build_trip_data.py`. Category shows up as a heading in the reference doc.

### Refresh live camp availability

```powershell
py scripts\check_availability.py         # Swell BLM campgrounds
py scripts\check_moab_availability.py    # Moab-area campgrounds
```

These hit the Recreation.gov public API (no auth required) and print availability per target date. Outputs are informational - if availability changes significantly, update `CAMPSITES` in `build_trip_data.py` and rebuild.

### Change day structure / add a rest day / resize a window

Edit the `DAYS` list in `scripts/build_trip_data.py`. `mi_lo` / `mi_hi` defines what section of the main track and which waypoints (by mile) belong to each overland day. Also update `CAMPSITES` keys to match any new day IDs.

### Tune the on-page scheduler (break-camp time, driving speed, stop durations)

The itinerary's per-day scheduler (checkboxes, ETA column, camp ETA) is driven by three knobs in `scripts/build_trip_data.py`:

- `SCHEDULE_DEFAULTS` (per day): `break_camp` time and `moving_mph` (pure driving speed, no stops folded in). Only the days listed here get a scheduler UI - today that's `day1_swell` through `day4_swell`. Add a key to enable scheduling on another day (needs a sliced track and POIs to be useful).
- `DEFAULT_CHECKED_BY_STATUS`: which POI statuses are checked by default. Primary / hike_candidate / conditional are on; backups off.
- `_default_minutes(name, sym, status, note)`: seeds the "Stop (min)" input for each POI. Tune special cases at the top (by name), then fall back to symbol-based defaults. Changes only affect *default* values - users can override inline on the page, and their edits are saved in `localStorage` per day.
- `POI_SPUR_OVERRIDES` (per POI name): round-trip miles saved if the POI is un-checked. Used for out-and-back spurs where the main track drives in and back out to reach the POI; skipping the stop avoids the full detour, not just the dwell time. Currently set for `DP - Red Canyon` (15.3 mi) and `DP - Hidden Splendor Overlook` (19.7 mi). See "Audit spurs" below.

On the page itself, each scheduled day has a `Reset day` button that clears its localStorage entry (`sched-v1-<dayId>`) and restores the defaults from the freshly rebuilt HTML. The scheduler math: each leg = `|mile_delta| + 2 * off_track_m / 1609` at `moving_mph`; if any POI between the previous and current included stop has `spur_mi > 0` and was un-checked, that value is subtracted from the leg (capped at zero). Camp ETA = straight-line haversine from last included stop * 1.3 winding factor (spur savings do not cascade into the camp leg).

### Audit spurs (which primary POIs add meaningful detour miles?)

```powershell
py scripts\spur_audit.py
```

Scans the unified 225-mile track and, for each primary / hike_candidate / conditional POI, detects whether the track goes out and doubles back to reach it (an out-and-back spur). Prints one row per POI with detected spur length in miles; POIs with spur ≥ 2 mi are flagged with `*`. The tail of the output calls out specific POIs of interest (see the `targets` list inside the script).

Use the printed "Spur length" values to populate `POI_SPUR_OVERRIDES` in `scripts/build_trip_data.py`, then rebuild. The auto-detection is a heuristic (pinches at 60 m tolerance, 25 mi search window) — it handles clean out-and-back spurs well, but you should eyeball the GPX before trusting big numbers (loops and braided tracks can mis-detect).

### POI description pop-ups

Every POI that has a `<desc>` element in `san-rafael-swell-adv-route-2025.gpx` (27 of them, ranging from one-liner hints like "Large/tall vehicles may have issues fitting through the tunnel" to multi-paragraph descriptions of Wedge Overlook, Head of Sinbad, etc.) gets a small document-icon button next to its name in both `trip-itinerary.html` and `trip-reference.html`. Click it to open a native `<dialog>` showing the full description plus mile, type, off-track distance, and a Google Maps link. Works fully offline (all descriptions are embedded into the page as a JS object at build time).

To add or edit descriptions, edit the `<desc>` elements directly in the source GPX and rebuild — `parse_route_gpx.py -> build_trip_data.py -> build_deliverables.py` will thread them through automatically.

---

## Pre-trip action items (time-sensitive)

These must be done by **a human** - they require a real reservation or phone call:

1. **Reserve Ken's Lake Group Site B for May 6, 2026**
   - [recreation.gov/camping/campgrounds/251840](https://www.recreation.gov/camping/campgrounds/251840)
   - $50/night, 25-person capacity, was available as of Apr 16, 2026

2. **Reserve Dead Horse Point SP - Wingate Loop (1 standard electric site) for May 7, 8, 9**
   - [utahstateparks.reserveamerica.com](https://utahstateparks.reserveamerica.com)
   - $60/night * 3 nights = ~$180 total, max 8 people / site (we have 7)

3. **Circulate the per-vehicle fuel worksheet** in `planning/fuel_plan.md`. Each driver fills in their baseline MPG, tank capacity, aux fuel, and the resulting "can do 255 mi @ 11 MPG?" verdict. Share the filled-in table so the group knows who has aux capacity.

4. **Confirm at least one satellite messenger** (Garmin InReach / Zoleo / SPOT) is active for the Swell portion, with a non-traveling emergency contact.

5. **Check Arches NP timed-entry reservation requirements** for May 6-9, 2026, at [recreation.gov/timed-entry/10089519](https://www.recreation.gov/timed-entry/10089519) - if active, reserve.

6. **Morning of May 1 or May 2** - run the pre-trip checklist in `planning/realtime_info_sources.md` (NWS forecasts, flash-flood watches, UDOT, fire restrictions, stream gauges).

---

## Environment & tooling

- Python 3.10+ required. The core build pipeline (`build_trip_data.py`, `build_deliverables.py`, `download_offline_tiles.py`, `verify_outputs.py`) uses only the stdlib (`json`, `xml.etree.ElementTree`, `urllib.request`, `pathlib`, `math`, `html`, `base64`, `re`).
- The PWA scripts add two optional deps:
  - `scripts/build_pwa_icons.py` -- needs `pillow`.
  - `scripts/build_pwa_assets.py` -- needs `qrcode[pil]` (only for the QR code; manifest / service worker / robots are written without it).
  - Install both: `pip install pillow "qrcode[pil]"`. CI installs them automatically.
- Windows PowerShell is the expected shell (all commands use `py` launcher).
- No virtual env required.
- **Leaflet + offline tiles are bundled into `trip-itinerary.html`.** See "Offline map assets" below.

---

## Offline map assets (map works with zero internet)

`trip-itinerary.html` is fully self-contained for offline use:

1. **Leaflet 1.9.4 JS + CSS are inlined** into the HTML (from `planning/vendor/leaflet/`). The map engine loads without any CDN request.
2. **A low-res OpenStreetMap tile cache is base64-embedded** into the HTML (from `planning/offline_tiles/`). It covers the full trip bounding box (~38.25 to 39.35 N, -111.30 to -109.10 W) at zoom levels 7-9, about 22 tiles, ~430 KB base64. At higher zooms Leaflet auto-stretches the zoom-9 tile into a pixelated-but-recognizable background.
3. **When online, Esri Topo / Satellite / Street tiles render on top** of the offline baseline. Failed Esri tiles are set to a transparent PNG so the low-res background shows through offline.
4. The layer control (top-right of each map) exposes both the three Esri base layers and the always-on offline baseline.

To (re)populate the caches:

```powershell
py scripts\download_offline_tiles.py
py scripts\build_deliverables.py
```

The download script is idempotent (skips files already on disk), rate-limits at ~1 tile/sec per OSM's usage policy, and uses a descriptive `User-Agent`. If the bbox or zoom range in `scripts/download_offline_tiles.py` changes, delete `planning/offline_tiles/` to force a fresh fetch.

Attribution: offline tiles are OpenStreetMap raster tiles; the Leaflet map renders the required `© OpenStreetMap contributors (cached)` credit in the attribution control. Online Esri tiles render their own attribution when active.

---

## Scripts directory map

Current-use scripts (the ones above). The rest in `scripts/` are legacy one-off data-collection scripts from earlier phases of this project (Google Takeout extraction, Overpass / Nominatim geocoding, etc.) - kept for provenance but no longer part of the active pipeline.

Safe to ignore unless re-doing the raw-data pull:
- `extract_places.py`, `clean_places.py`, `match_takeout.py`, `filter_*_by_area.py`
- `geocode_*.py`, `validate_geocodes.py`, `complete_coords.py`, `patch_outliers.py`
- `overpass_*.py`, `nominatim_*.py`
- `md_to_kml_gpx.py`, `generate_outputs.py`
- `build_poi_menu.py`, `build_campsite_menu.py` (superseded by the decision-locked versions in the pipeline)

---

## At-a-glance summary

```
root/
  README.md                         <-- you are here
  index.html                        <-- LANDING + INSTALL INSTRUCTIONS (PWA entry)
  trip-itinerary.html               <-- DAILY VIEW (primary deliverable)
  trip-reference.html               <-- FULL REFERENCE (primary deliverable)
  trip-plan.gpx                     <-- NAV DATA (primary deliverable)
  Planning prompt.md
  san-rafael-swell-adv-route-2025.gpx  (source GPX from the OTG Crew)
  Utah_Destinations_In_San_Rafael_Area.md

  assets/icon-source.svg            <-- icon source (rasterized by build_pwa_icons.py)
  manifest.webmanifest              <-- GENERATED (gitignored; built by CI)
  service-worker.js                 <-- GENERATED (gitignored; built by CI)
  robots.txt                        <-- GENERATED (gitignored; built by CI)
  icons/*.png                       <-- GENERATED (gitignored; built by CI)
  assets/qr.png                     <-- GENERATED (gitignored; built by CI)

  .github/workflows/deploy.yml      <-- Pages deploy + secret-scan on every push to main
  .github/scripts/secret-scan.sh    <-- PII guard run against the staged publish dir

  Participants.md          (gitignored - local-only personal roster)
  Collected Location Info/ (gitignored - raw narrative + research)
  Takeout/                 (gitignored - Google Maps Takeout dump)

  planning/
    poi_decisions.md                <-- locked POI triage (human-readable)
    campsite_plan.md                <-- locked camps (human-readable)
    fuel_plan.md                    <-- per-vehicle fuel worksheet
    realtime_info_sources.md        <-- every live-data link in one place
    trip_data.json                  <-- GENERATED source-of-truth
    route_*.json                    <-- GENERATED intermediate
    offline_tiles/{z}/{x}/{y}.png   <-- GENERATED OSM tiles for offline map
    vendor/leaflet/{leaflet.js,.css}<-- GENERATED local Leaflet bundle
    poi_menu.md / campsite_menu.md  <-- earlier drafts, kept for context

  scripts/
    build_trip_data.py              <-- *** main edit point for data changes ***
    build_deliverables.py           <-- HTML + GPX generator
    build_pwa_assets.py             <-- manifest + service-worker + robots + QR
    build_pwa_icons.py              <-- rasterize assets/icon-source.svg -> icons/*.png
    download_offline_tiles.py       <-- one-time: cache OSM tiles + Leaflet locally
    spur_audit.py                   <-- detect out-and-back spurs in the GPX
    verify_outputs.py               <-- sanity check
    check_availability.py           <-- Swell live availability
    check_moab_availability.py      <-- Moab live availability
    parse_route_gpx.py              <-- parse source GPX
    analyze_route.py                <-- project waypoints onto track
    ... legacy scripts ...
```

To rebuild everything: `py scripts\build_trip_data.py && py scripts\build_deliverables.py && py scripts\verify_outputs.py`
