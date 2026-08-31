# Review notes — Washington Cascades trip app

Written for you to read on waking. Everything here is a call I made without you,
grouped by whether it needs your input. The app builds and works; nothing below
blocks using it.

---

## 1. Needs your decision

### 1.1 Book the campgrounds — this is the only genuinely time-critical item

Nothing is reserved. Availability was checked 2026-08-31 and Friday Sep 11 /
Saturday Sep 12 are a weekend, so the good sites are going. Priority order:

| # | Night | Campground | Why |
|---|---|---|---|
| **1** | **Fri Sep 11 + Sat Sep 12** | [North Fork **Elk Group Camp**](https://www.recreation.gov/camping/campgrounds/232898) | Single group site, covers all six rigs in one booking, and was open on **both** weekend nights when nearly nothing else was. If this goes, the plan gets materially worse. |
| 2 | Wed Sep 9 | [Takhlakh Lake](https://www.recreation.gov/camping/campgrounds/232861) | 22 sites open Wednesday, **zero** Friday or Saturday. The whole day split exists to reach it midweek. |
| 3 | Tue Sep 8 + Sat Sep 12 | [Panther Creek](https://www.recreation.gov/camping/campgrounds/233103) | 19 open Tuesday but only 5 Saturday — book both together. |
| 4 | Thu Sep 10 | [Walupt Lake](https://www.recreation.gov/camping/campgrounds/232860) | Only 7 open Thursday. |

`python scripts/check_availability.py` re-checks all of these live. Run it before
booking; the numbers will have moved.

### 1.2 Head count

I assumed **12 people across 6 vehicles**. It is flagged as an estimate in
`scripts/trip_config.py` (`GROUP_COUNTS`, with `people_confirmed: False`) and shows
as "6 Vehicles" in the app rather than a person count, so a wrong guess is not
visible anywhere. Tell me the real number and I will set it.

### 1.3 Saturday's shape — a real trade, not a fallback

Two options, and I picked the first:

- **What I built:** Saturday runs 82 miles to Panther Creek, then Sunday morning
  closes the final 16 miles of loop before driving home. Sunday becomes about 9.5
  hours, so a 7:00 AM departure matters.
- **The alternative:** finish the whole loop Saturday and drop 21 miles to Home
  Valley Campground on the Columbia. Saturday becomes ~117 miles, but you get hot
  showers before the drive and Sunday is purely driving.

Home Valley is booked through Skamania County, not Recreation.gov. Worth deciding
before booking since it changes what you reserve for Saturday.

### 1.4 The repository move

I cannot create a repository — my GitHub access is read-only. Nothing is hardcoded
to the current repo name, so moving is: add remote, push, enable Pages, update the
branch trigger in `.github/workflows/deploy.yml`. I pointed the workflow at this
branch meanwhile so you can preview the live site before deciding.

### 1.5 Participant names in the PII guard

`.github/scripts/secret-scan.sh` still carries the previous trip's roster. Harmless
(those names stay blocked) but it protects nobody new. Send me the roster and I will
swap it.

---

## 2. Assumptions I made — tell me if any are wrong

| Assumption | Basis | Where to change |
|---|---|---|
| Camp at **Panther Creek** the night of Sep 8, not on-route | You had no preference. It is 11 mi up Wind River Rd, had the best Tuesday availability, and is the same camp as your last night so the group learns one site. | `CAMPSITES['sep8_travel']` |
| **Don't** bank miles Tuesday evening | Banking 35 mi doesn't shorten the days that are actually long, and it puts camp setup at dusk after 9 hours of driving. | — |
| Break camp **08:00 / 08:30 / 07:30 / 07:30** | Earlier on the two long days. Sunrise is 06:35, so all are comfortably post-dawn. | `SCHEDULE_DEFAULTS` |
| Moving speeds **22 / 20 / 28 / 22 mph** | Graded Forest Service gravel, with Day 3 faster because much of it is paved US 12. | `SCHEDULE_DEFAULTS` |
| Hikes start **unchecked** | You said triage them. Each day's ETA starts as driving-only; you tick and watch it move. | `DEFAULT_CHECKED_BY_STATUS` in `trip_core.py` |
| Kept the **weather** and **fuel** pages, added **fire & closures** and **camping plan** | Your call on the first two; fire is the September go/no-go risk here. | nav list in `build_deliverables.py` |
| Dropped alternate routes, river crossing, slot canyons | You said no alternates, and neither hazard page has an equivalent here. | — |
| **Skipped** the Pimlico Road / FS 7807 track | You said probably not doing it. It is ignored by name, not deleted, so re-enabling is one line. | `IGNORED_TRACK_NAMES` |
| Kept the **KML Viewer**, deleted `ux-preview/` | You never answered. The viewer is a generic tool for inspecting route files; ux-preview was Swell-era scratch work. | — |

---

## 3. Does the plan actually fit? Yes, with one caveat

I simulated the scheduler against real sunset times for every combination of hikes.
Margin is against sunset; usable light in timber ends earlier.

| Day | Defaults only | + all its hikes | Verdict |
|---|---|---|---|
| Wed Sep 9 | 15:56 (+3h36m) | 18:52 (+40m) | **Pick two of three hikes, not all three** |
| Thu Sep 10 | 12:03 (+7h27m) | 16:12 (+3h18m) | Lots of room |
| Fri Sep 11 | 11:46 (+7h42m) | 14:19 (+5h09m) | High Rock fits easily |
| Sat Sep 12 | 13:30 (+5h56m) | 15:57 (+3h29m) | Room for the lava caves and Red Mountain |

**Day 1 is the only pinch point.** It carries 21 of the route's POIs because the
Indian Heaven / Berry Fields / Mount Adams corridor is where the density is. All
three hikes puts you into camp at 18:52 with 40 minutes of light — doable but no
slack. Langfield Falls plus Steamboat Mountain lands at 17:33, which is comfortable.

Good news: **High Rock Lookout, the one hike I would fight for, fits Friday with
five hours to spare.** Mount Rainier from 13 air miles away is the best thing on
this route.

---

## 4. Bugs I found and fixed

Worth knowing because several would have bitten you in the field:

1. **The Saturday camp had no GPX waypoint.** Camps were de-duplicated by location,
   and Panther Creek serves both your first and last night, so it emitted once
   labeled "Sep 8". Anyone navigating from the GPX would have found no pin for their
   final camp. Now reads `[CAMP PRIMARY] Sep 8 (Tue) + Sep 12 (Sat)`.

2. **The per-day weather never loaded.** A JavaScript syntax error killed the boot
   script on the itinerary page, so every day's forecast panel would have sat on
   "Loading forecasts…" indefinitely. Caused by my own prefix rename landing on a
   plain string instead of an f-string, which shipped `{cfg.JS_PREFIX}` literally
   into the page. Found by syntax-checking each inline script block.

3. **The offline map was capped at zoom 9** by a hardcoded `maxNativeZoom`. I
   deepened the cache to zoom 10, which without that fix would have downloaded 35
   tiles that were never requested.

4. **Leaflet was requesting three images that 404'd.** Its CSS references
   `images/layers.png` and friends by relative URL, and because the CSS is inlined
   into the page those resolved against the page path. The layers control was
   missing its icon and the page wasn't truly self-contained. Now inlined as data
   URIs, so the map makes zero requests offline.

5. Recreation.gov reports North Fork Campground and North Fork Bear Group Camp at
   identical coordinates, which was silently deleting one of them.

### Verified in a real browser

I drove all seven pages in headless Chrome. Result: **no JavaScript errors and no
failed requests on any page**, and all six inline script blocks parse.

- All 7 day tabs render maps with offline tiles, route polylines and markers.
- Sunday's map correctly shows two lines: solid orange for the loop closure and
  dashed blue for the drive home.
- The scheduler moves in both directions and resets: baseline 3:33 PM → uncheck
  three stops → 2:43 PM → add Council Bluff → 4:40 PM → Reset → 3:33 PM.
- POI description dialogs open (17 of them on Day 1 alone).
- Map fullscreen toggles in and out.
- Live weather fetches: Takhlakh Lake showed 71°F/41°F for Sep 9.

One thing that caught my eye in that live data: **Saturday Sep 12 currently
forecasts a high of 55°F and a low of 37°F**, a sharp drop from the mid-to-high
70s earlier in the week. Nine days out that will move, but it is the kind of swing
worth watching — that is your lava-caves-and-Burley-Mountain day.

---

## 5. Judgement calls you might disagree with

**Offline map now goes to zoom 10.** This takes `trip-itinerary.html` from 1.07 MB
to 1.83 MB. I did it because cell coverage between Carson and Packwood is nil and
dense Cascade timber is far harder to orient in than the open desert last time —
zoom 9 shows towns and highways but not the forest-road network, which is exactly
what you need when a junction isn't where you expected. Zoom 11 would push the page
past 5 MB, so I stopped at 10. Revert by setting `TILE_ZOOMS = [7, 8, 9]`.

**Fuel is framed around the gap, not the total.** The loop burns ~20 gallons, which
sounds easy. The real constraint is 154 miles from Carson to Packwood with nothing.
The fuel page leads with that and includes a per-vehicle range worksheet, because
anyone with a small tank needs a jerry can and should know before departure.

**I added a daylight table** rather than the vague "sunset around 7:30" I first
wrote. Computed properly it is 19:34 falling to 19:25 across the week.

**Distant peaks are marked as landmarks.** The source GPX tags Rainier, Adams,
St Helens and Gilbert Peak as waypoints 5–13 miles off the track. Untreated, the
scheduler would have added a 25-mile round trip to go visit the summit of Rainier.
They now show as reference markers contributing zero miles and zero time.

---

## 6. State of things

- Full pipeline runs clean from a fresh clone with no network needed — tiles and
  highway tracks are committed. I simulated the entire CI workflow including staging
  and the PII scan: passes, 2.6 MB published artifact, all 15 precache entries present.
- Generated GPX validates: 61 waypoints, 7 tracks, all five camps represented.
- No remaining reference to San Rafael, Swell, Moab, Utah or the old `SRS` prefix in
  any shipped file.
- `README.md` documents the pipeline, which file owns what, and a retargeting guide
  for next time — including the specific traps, since the whole point of this pass
  was to make trip number three cheap.

## 7. What I would do next, if you want more

- Set the real head count and swap the PII roster.
- Decide Saturday's shape (§1.3), then book (§1.1).
- Optional: a short packing/gear page. You did not ask for one and I did not
  presume, but the lava caves need per-person lights, fires may be restricted so a
  gas stove is mandatory, and the 4,000 ft camps will be near freezing. Those three
  facts are currently scattered across three pages.
