# Alternate overland routes (4-day options)

This document captures **alternate San Rafael Swell overland plans** that lighten the tight **Day 2 / Day 3** schedule in the **main** itinerary (`trip-itinerary.html`, driven by `planning/trip_data.json`). The **reference doc** (`trip-reference.html`) and **GPX** remain aligned with that **primary** route until the group picks an alternate and merges it into the data model.

**Daily narrative pages (offline PWA, same app shell as slot/fuel guides):**

| Page | Description |
|------|-------------|
| [trip-itinerary-alt-a.html](../trip-itinerary-alt-a.html) | Option **A** — forward direction, Family Butte May 4, slot hikes deferred |
| [trip-itinerary-alt-b.html](../trip-itinerary-alt-b.html) | Option **B** — reverse (Sinbad-first); **Variant V1** default (Moab same night May 6) |
| [trip-itinerary-alt-d.html](../trip-itinerary-alt-d.html) | Option **D** — reverse with BTR split; **Variant V1** default (Moab same night May 6) |

**Source files for editors:** `planning/trip-itinerary-alt-a.md`, `trip-itinerary-alt-b.md`, `trip-itinerary-alt-d.md` (rebuild with `python scripts/build_deliverables.py`).

---

## Hard constraints

- **Early departures:** rigs that must return to **Boise** leave **Wednesday May 6** morning; target **on pavement by 09:30** latest (allows ~1.5 hr trail time that morning depending on camp).
- **May 5 night (forward Option A):** camp must stay **highway-adjacent** for the south exit (Temple Mountain → Hwy 24 → I-70).
- **Option C** (split camp May 5 only) was dropped from consideration.

---

## Option A — forward, Family Butte, defer slot hikes

- **Idea:** Keep current **Wedge-first** story; **May 4** camp **Family Butte** (pushes Reds Canyon + Lucky Strike to May 5); **May 5** drive **Behind-the-Reef** but **skip tactical slot hikes en route**; **May 6** stay-overs backtrack for **Chute/Crack** (and optional **WHW** send-off) then **Sinbad / Dutchman**, **not** pushing to Moab that night.
- **Variant:** **A-V2** is the working plan — **May 6 night** short-hop camp (Goblin Valley SP, Temple Mtn again, or Hwy 24 dispersed); **May 7** Moab / **Sand Flats cluster camp** + light afternoon (e.g. **Fins N Things**). **A-V1** (Sand Flats same night May 6) is intentionally avoided as too late for a good camp night.
- **Detail:** [trip-itinerary-alt-a.html](../trip-itinerary-alt-a.html)

---

## Option B — reverse (Sinbad-first), V1 default

- **Idea:** **May 1** meet + Bonneville night **same as main**; stage **May 2** at **Temple Mountain**; run **west → east** so **Black Dragon / Buckhorn** land last; **May 5** camp **Black Dragon** (I-70) *or* **Wedge** (nicer camp, Castle Dale exit for early-leavers).
- **Variant:** **V1** — stay-overs **Moab same night May 6** after any make-up stops. **V2** (extra Swell night) is optional; this doc defaults to **V1** for B.
- **Detail:** [trip-itinerary-alt-b.html](../trip-itinerary-alt-b.html)

---

## Option D — reverse, BTR split, Crack/Chute camp night 1, V1 default

- **Idea:** Same reverse staging as B; **split Behind-the-Reef** across **May 3–4**; **May 3** camp near **Crack Canyon** dispersed (**38.64423, -110.73771** primary; secondary at Chute/Crack TH pockets; tertiary **38.66000, -110.73253**); **Hidden Splendor Overlook** driven on **May 4**; **Family Butte** May 4; **Wedge** May 5; **May 6** split at **Wedge** (early-leavers north via **E Green River Cutoff** → Castle Dale).
- **Variant:** **V1** — stay-overs **Moab / Sand Flats cluster ~18:00–19:00** May 6. **V2** optional. Defaults here: **V1**.
- **Detail:** [trip-itinerary-alt-d.html](../trip-itinerary-alt-d.html)

---

## Quick comparison

| | A (forward) | B (reverse) | D (reverse, split) |
|---|-------------|-------------|---------------------|
| **Meet + staging** | May 1 Bonneville (same as main); May 2 Black Dragon | May 1 Bonneville; May 2 Temple Mtn | May 1 Bonneville; May 2 Temple Mtn |
| **May 5 camp** | Temple Mtn | Black Dragon or Wedge | Wedge |
| **Early-leaver “miss”** | No slots / Sinbad / WHW | Different mix vs D | No Buckhorn / Black Dragon string |
| **Moab timing (defaults)** | A-V2: Moab **May 7** + easy PM trail | V1: Moab **May 6** PM | V1: Moab **May 6** PM |

---

## Merge checklist (when the group picks one)

1. Update `scripts/build_trip_data.py` (`DAYS`, `POI_STATUS`, `CAMP_DATA`, schedules as needed).
2. Refresh `planning/poi_decisions.md`, `planning/slot-canyon-guide.md`; if **B**, adjust `planning/fuel_plan.md` narrative direction.
3. Run `python scripts/build_deliverables.py` and `python scripts/build_pwa_assets.py`.
4. Retire or archive unused alt markdown if the repo should only show the chosen plan.
