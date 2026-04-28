# Highway polylines (`highway_tracks.json`)

This file holds **decimated driving polylines** (lat/lon pairs) for **paved days** when the main Swell GPX has no useful corridor. They are **not** from Google or Apple; they come from [OSRM](https://project-osrm.org/) over **OpenStreetMap** and are only a **rough** match to what a live nav app will pick.

- **Do not** hand-tweak thousands of points unless you know what you are doing; prefer re-requesting a route and replacing the array for that key.
- After any edit, run the normal rebuild (`scripts/build_trip_data.py`, alternate builders if you use them, `scripts/build_deliverables.py`, `scripts/build_pwa_assets.py`, `scripts/verify_outputs.py`) so `trip_data.json` and the HTML pick up the geometry.

## Keys (arrays of `[lat, lon]`)

| JSON key | Used on (main trip) | Endpoints / intent |
|----------|---------------------|---------------------|
| `may1_boise_bonneville` | May 1 travel | Boise Federal Way meet → Bonneville staging |
| `may2_bonneville_black_dragon` | May 2 travel | Bonneville → Black Dragon (forward itinerary) |
| `may2_bonneville_temple_mtn` | May 2 travel (alts B/D) | Bonneville → Temple Mountain side |
| `green_river_to_sand_flats` | May 6 transit to Moab | **Start** is OSRM-snapped near the **end of the Day 4 AM Swell track** (Head of Sinbad / tunnel area), with a **via** at I-70 Green River (fuel), then to the **Sand Flats** cluster pin — so the PM line continues from the AM line on the map. (The JSON key name is historical.) |
| `sand_flats_to_boise_federal_way` | May 10 return | Sand Flats → midpoint on I-15/I-84 → Federal Way meet (same as trip start) |

The top-level `"source"` string in the JSON is copied into trip metadata as `highway_tracks_note` for the app.

## Wiring in code

- **Load:** `load_highway_tracks()` in `scripts/trip_core.py` reads `planning/highway_tracks.json`.
- **Main trip:** `scripts/build_trip_data.py` maps day ids to keys in `_attach_main_highway_tracks()`.
- **Alternates:** `scripts/alts/alt_a.py`, `alt_b.py`, `alt_d.py` attach the same Moab keys to their Moab-transit and return day ids.

## Regenerating a route

1. Choose coordinates for **start** and **end** (and any **via** points if you split the leg).
2. Request a driving route from a public OSRM instance (e.g. `https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson`), or use your own OSRM / OSM toolchain.
3. Decode the line string to WGS84 points, **decimate** to a few hundred points max for file size, and replace the corresponding array in `highway_tracks.json`.
4. Update the `"source"` field if the methodology changed.
5. Rebuild and verify (see main `README.md`).
