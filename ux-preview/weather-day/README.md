# Weather day-block — UX preview pack

Static HTML mocks for **per-day weather** on the itinerary. Compare **Options A–F** in the browser before changing [`scripts/build_deliverables.py`](../../scripts/build_deliverables.py) or [`weather-client.js`](../../weather-client.js).

**E / F** refine **A**: same “Forecast for this day” title, location+date on one row when wide, loud Hi/Lo/Rain/Wind, concerns callout, `<details>` for depth, and **text links only** (no large NWS button). **E** uses four **tiles**; **F** uses one **segmented strip** (4-up → 2×2 → stack).

## How to view

1. Open [`index.html`](index.html) in a browser (double-click, or serve the repo root with any static server).
2. Use DevTools **device toolbar** (e.g. iPhone width vs iPad vs desktop) on each option page.

No `fetch`, no `localStorage` — works on **`file://`**.

## What is mocked

Each option page includes two fake “days”:

- **Moab** — shows contextual links (NWS point + optional WU Moab).
- **Boise return** — WU Moab is omitted; only NWS (Boise corridor) is relevant.

Copy and forecasts are **placeholder text**, not live data.

## Optional git hygiene

To stop these files from being committed, add a line to the repo [`.gitignore`](../../.gitignore):

```gitignore
ux-preview/
```

Remove that line if you want the team to share the same mocks via git.
