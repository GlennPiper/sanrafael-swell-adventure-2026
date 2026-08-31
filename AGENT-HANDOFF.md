# Agent handoff — Washington Cascades trip app

Context for an agent picking this repo up cold. Written 2026-08-31, immediately
after the code was migrated here from its predecessor repo.

Delete or rewrite this file once the trip is planned; it is a snapshot, not
documentation.

---

## What this repo is

A **trip-planning workspace plus an offline-first Progressive Web App** for a
6-vehicle overlanding trip on the Washington Cascades Adventure Route,
September 8–13 2026.

The app is *generated*, not hand-written. A Python pipeline reads a source route
GPX plus planning tables and emits self-contained HTML with maps, POIs,
campgrounds and schedule data baked in, so it works with no cell signal — which
matters, because there is none between Carson and Packwood.

It is deployed to GitHub Pages by GitHub Actions on push to `main`.

## Read these two files before doing anything

| File | What it gives you |
|---|---|
| **`README.md`** | Architecture, the pipeline, which file owns what, build commands, and a retargeting guide |
| **`REVIEW-NOTES.md`** | Every decision made, the assumptions behind them, what still needs the trip organiser's input |

This handoff deliberately does not duplicate them. It covers the things that
only exist in conversation.

---

## The trip

| | |
|---|---|
| Route | 324.8-mile loop, Gifford Pinchot National Forest |
| Dates | Tue Sep 8 – Sun Sep 13, 2026 |
| Start / end | Carson, WA (Columbia River Gorge) → Triangle Pass |
| Meet | Sinclair Stinker Station, 1902 N Franklin Blvd, Nampa ID. Gather 8:00 AM MDT, depart 8:15 |
| Group | ~6 vehicles, no split. Head count still unconfirmed |
| Highway legs | 376 mi out, 368 mi back |
| Fuel on route | Carson (mi 2), Packwood (mi 156), Randle (mi 217) |

**Day split** — dictated by where campgrounds actually exist, not by preference.
Developed campgrounds cluster from mile 34 to 141, then there is an 85-mile gap
with nothing established until North Fork at 226, which forces days 3 and 4 to be
the long ones.

| Day | Route miles | Distance | Camp |
|---|---|---|---|
| Tue Sep 8 | travel | 376 mi highway | Panther Creek CG |
| Wed Sep 9 | 0 → 84.5 | 85 mi | **Takhlakh Lake CG** |
| Thu Sep 10 | 84.5 → 133.5 | 49 mi | Walupt Lake CG |
| Fri Sep 11 | 133.5 → 226.5 | 93 mi | **North Fork Elk Group Camp** |
| Sat Sep 12 | 226.5 → 308.5 | 82 mi | Panther Creek CG |
| Sun Sep 13 | 308.5 → 324.8 | 16 mi + 368 mi home | — |

---

## Immediate outstanding items

**1. GitHub Pages is not enabled yet.** The first workflow run here built
successfully — every step of the `build` job passed, including the PII scan and
artifact upload — but the `deploy` job failed at "Deploy to GitHub Pages" because
Pages was not configured. Fix: Settings → Pages → **Source: GitHub Actions**, then
re-run the workflow. This is a repo-settings action, not a code change.

**2. Nothing is booked.** This is the only genuinely time-sensitive thing. See
`planning/camping_plan.md` for a live Recreation.gov availability snapshot and the
booking priority order. Friday Sep 11 and Saturday Sep 12 are a weekend and the
good sites are going. `python scripts/check_availability.py` re-checks live.

**3. Head count unconfirmed.** `trip_config.GROUP_COUNTS` carries
`people_estimated: 12` with `people_confirmed: False`. The app displays vehicles,
not people, so a wrong guess is not visible anywhere.

**4. The PII guard's participant roster is stale.** `.github/scripts/secret-scan.sh`
still lists the previous trip's names. Harmless — those stay blocked — but it
protects nobody on this trip.

---

## Decisions already made — do not re-litigate without asking

These were settled with the trip organiser. Reasoning is in `REVIEW-NOTES.md`.

- **Four route days, split as above.** Driven by campground availability. Takhlakh
  Lake had 22 sites open Wednesday and **zero** on either weekend night, so Day 1
  exists to reach it midweek.
- **No alternate route variants.** The predecessor app had three (A/B/D); the
  machinery was deliberately removed.
- **No river-crossing or slot-canyon style hazard pages** — no local equivalent.
  **Fire and closures** replaces them as the trip's go/no-go page, because for
  September in Gifford Pinchot, forest orders and smoke are the real risk rather
  than terrain.
- **Pages kept:** itinerary, reference, camping plan, fuel plan, weather, fire and
  closures. Gear notes are a card on the reference page, not a separate page — the
  organiser asked to keep the page count down.
- **Hikes default to unchecked** in the arrival-time scheduler, so each day starts
  as driving-only and the group opts in and watches the ETA move. The organiser
  asked for hikes to be treated as ordinary POIs to triage, not a fixed plan.
- **The Pimlico Road / FS 7807 track in the source GPX is ignored**, by name in
  `trip_config.IGNORED_TRACK_NAMES`, not deleted. Re-enabling is one line.
- **Offline tiles go to zoom 10** (52 tiles, ~985 KB), taking
  `trip-itinerary.html` to ~1.8 MB. Justified by nil cell coverage and dense
  timber. Zoom 11 would push the page past 5 MB.

---

## Architecture traps

These are hard-won. Several caused real bugs that shipped before being caught.

1. **`trip_config.MAIN_TRACK_NAME` must exactly match a `<trk><name>` in the
   source GPX.** Both `parse_route_gpx.py` and `analyze_route.py` fail loudly if
   not, which is deliberate.

2. **POI catalog keys in `trip_core.POI_STATUS` must match the GPX `<name>`
   byte-for-byte, typos included.** This GPX has one: `Olalli Lake Campground`,
   for what is actually Olallie Lake. Never "fix" a spelling in a lookup key —
   put the corrected label in `POI_RENAME`, keyed by
   `(gpx_name, int(route_mile))`, which also handles the three separate waypoints
   all named `Gas Station`.

   Coverage is currently complete: 57 non-campsite waypoints, 0 uncategorised, 0
   dead catalog keys. Re-check after any GPX change:

   ```python
   import json, sys; sys.path.insert(0, 'scripts')
   from trip_core import POI_STATUS
   wps = json.load(open('planning/route_analysis.json'))['waypoints_ordered']
   names = {w['name'] or '' for w in wps}
   print('uncategorised:', [w['name'] for w in wps
                            if w['sym'] != 'campsite-24' and w['name'] not in POI_STATUS])
   print('dead keys:', [k for k in POI_STATUS if k not in names])
   ```

   Anything uncategorised falls through to `status='unclassified'` and quietly
   renders without a badge rather than erroring, so this check matters.

3. **Any waypoint far off the track needs `status='landmark'`.** The source GPX
   marks Rainier, Adams, St Helens and Gilbert Peak as waypoints 5–13 miles off
   route. Without `landmark` — which zeroes the off-track offset and the stop time
   — the ETA scheduler tries to add a 25-mile round trip to go visit the summit of
   Mount Rainier.

4. **Every phone number in `trip_config` must also be in `ALLOW_NUMBERS` in
   `.github/scripts/secret-scan.sh`, or the deploy fails.** The scan runs against
   the published output, not the source.

5. **Any line interpolating `cfg.JS_PREFIX` must be an f-string.** A plain string
   ships the literal `{cfg.JS_PREFIX}` into the page, which is a JS syntax error
   that silently kills the whole `<script>` block. This actually happened and left
   the per-day weather stuck on "Loading forecasts…". The interpolated global is
   now built once into a variable — keep it that way.

6. **`maxNativeZoom` on the offline Leaflet layer must equal
   `max(cfg.TILE_ZOOMS)`.** It now derives automatically. Hardcoding it lower
   silently wastes every tile cached deeper than the cap.

7. **`leaflet.css` references three images by relative URL.** Because the CSS is
   inlined into the page they resolve against the page path and 404. They are
   vendored into `planning/vendor/leaflet/images/` and rewritten to data URIs at
   build time. Do not drop that step.

8. **`generated_at` in `build_trip_data.py` feeds the service-worker cache
   version.** Bump it when shipping changes, or installed PWAs keep serving stale
   pages.

9. **Camps de-duplicate by `(lat, lon, tier, idx)`** and a camp reused on more
   than one night emits a single GPX pin labeled with every night it serves. An
   earlier key of `(lat, lon, tier)` silently dropped the final night's camp
   waypoint entirely.

---

## Build and verify

```bash
pip install markdown pillow "qrcode[pil]"

python scripts/download_offline_tiles.py   # once; also vendors Leaflet + its images
python scripts/fetch_highway_tracks.py     # once; needs network (OSRM)
python scripts/parse_route_gpx.py
python scripts/analyze_route.py
python scripts/build_trip_data.py
python scripts/build_pwa_icons.py
python scripts/build_deliverables.py
python scripts/build_pwa_assets.py

python -m http.server 8899   # then open http://localhost:8899/index.html
```

### Verification that actually catches things

Eyeballing the page is not enough — it looked fine while the weather boot script
was dead. What worked:

- **Syntax-check each inline `<script>` block separately.** Extract them with a
  regex and run `node --check` on each. That is how the dead boot script was found.
- **Drive the pages in headless Chrome** (`puppeteer-core` against
  `/usr/local/bin/google-chrome`), capturing `pageerror`, `console.error`,
  `requestfailed` and any response `>= 400`. Filter out `api.weather.gov`,
  `open-meteo.com`, `arcgisonline.com` and `tile.openstreetmap.org`, which fail
  legitimately offline.
- **Test the scheduler by toggling checkboxes** and asserting the arrival time
  moves in the right direction. Note the fullscreen button needs a *trusted* click
  (`page.click()`, not a synthetic `element.click()`), or the native Fullscreen API
  silently refuses.
- **Parse the generated GPX** and assert every day's primary camp appears.
- **Run the PII scan** against a staged publish directory before assuming CI will pass.
- **Simulate CI from a clean clone** — it must build with no network, since tiles
  and highway tracks are committed.

---

## Provenance

Migrated from `GlennPiper/sanrafael-swell-adventure-2026`, which held the same app
targeted at a San Rafael Swell / Moab trip in May 2026. That repo is the archive
and its Pages site is unaffected.

The retarget replaced all trip content and refactored the pipeline so trip
identity lives in one file (`scripts/trip_config.py`) instead of being scattered
through a 3,000-line HTML generator. `README.md` has the retargeting guide, which
is worth reading even for non-retargeting work because it explains the ownership
boundaries between files.

Full history came across — 71 commits, of which the last ~20 are the retarget.

---

## How the trip organiser prefers to work

- **Ask questions rather than guessing** when something is genuinely ambiguous and
  a wrong answer would be costly. They explicitly asked for this at the start.
- **When they are unavailable, make the best assumption, then document it** for
  later discussion rather than stalling. That is what `REVIEW-NOTES.md` is for —
  keep adding to it.
- They care about **why**, not just what. Explaining the constraint behind a
  recommendation lands better than presenting a conclusion.
- They are comfortable with technical detail and read the actual numbers.
