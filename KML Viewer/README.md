# KML Viewer

A web application to load KML and GPX files and preview points and tracks on a map.

## Run

```bash
npm install
npm run dev
```

Then open http://localhost:5173/

## Build

```bash
npm run build
```

Output is in `dist/`. Serve with any static file server, or open `dist/index.html` directly (map tiles may require a server).

## Usage

1. Click **Load KML/GPX** or drag and drop a `.kml`, `.kmz`, or `.gpx` file onto the page
2. Use **Base map** dropdown to switch between OpenStreetMap, USGS Topo, and Satellite
3. Use **Layers** checkboxes to show/hide Points, Tracks, and Polygons
4. Zoom and pan the map as usual (scroll to zoom, drag to pan)

## Test Files

Use the KML files in `Test Files/` to verify the viewer. GPX files (e.g., from Gaia GPS or other track apps) are also supported.
