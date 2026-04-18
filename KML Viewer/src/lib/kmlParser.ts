import { kml, gpx } from '@tmcw/togeojson'
import type { FeatureCollection, Feature } from 'geojson'
import type { KmlLoadResult } from '../types'

export function mergeKmlResults(results: KmlLoadResult[]): KmlLoadResult {
  if (results.length === 0) {
    return {
      fileName: '',
      geojson: { type: 'FeatureCollection', features: [] },
      pointCount: 0,
      trackCount: 0,
      polygonCount: 0,
    }
  }
  if (results.length === 1) return results[0]
  const allFeatures = results.flatMap((r) => r.geojson.features ?? [])
  const pointCount = results.reduce((s, r) => s + r.pointCount, 0)
  const trackCount = results.reduce((s, r) => s + r.trackCount, 0)
  const polygonCount = results.reduce((s, r) => s + r.polygonCount, 0)
  return {
    fileName: results.map((r) => r.fileName).join(', '),
    geojson: { type: 'FeatureCollection', features: allFeatures },
    pointCount,
    trackCount,
    polygonCount,
  }
}

export function parseKmlToGeoJSON(xml: string): FeatureCollection {
  const parser = new DOMParser()
  const dom = parser.parseFromString(xml, 'text/xml')
  return kml(dom) as FeatureCollection
}

export function parseGpxToGeoJSON(xml: string): FeatureCollection {
  const parser = new DOMParser()
  const dom = parser.parseFromString(xml, 'text/xml')
  return gpx(dom) as FeatureCollection
}

export function countFeaturesByType(geojson: FeatureCollection) {
  let pointCount = 0
  let trackCount = 0
  let polygonCount = 0

  for (const feature of geojson.features || []) {
    const geom = feature.geometry
    if (!geom) continue
    if (geom.type === 'Point') pointCount++
    else if (geom.type === 'LineString' || geom.type === 'MultiLineString') trackCount++
    else if (geom.type === 'Polygon' || geom.type === 'MultiPolygon') polygonCount++
    else if (geom.type === 'GeometryCollection') {
      for (const g of geom.geometries) {
        if (g.type === 'Point') pointCount++
        else if (g.type === 'LineString' || g.type === 'MultiLineString') trackCount++
        else if (g.type === 'Polygon' || g.type === 'MultiPolygon') polygonCount++
      }
    }
  }

  return { pointCount, trackCount, polygonCount }
}

export function getUniqueSymValues(geojson: FeatureCollection): string[] {
  const syms = new Set<string>()
  for (const f of geojson.features ?? []) {
    const geom = f.geometry
    if (!geom || geom.type !== 'Point') continue
    const s = f.properties?.sym ?? f.properties?.Sym
    if (s) syms.add(String(s))
  }
  return Array.from(syms).sort()
}

export function splitByGeometryType(geojson: FeatureCollection): {
  points: FeatureCollection
  tracks: FeatureCollection
  polygons: FeatureCollection
} {
  const points: Feature[] = []
  const tracks: Feature[] = []
  const polygons: Feature[] = []

  function collect(f: Feature) {
    const geom = f.geometry
    if (!geom) return
    if (geom.type === 'Point') points.push(f)
    else if (geom.type === 'LineString' || geom.type === 'MultiLineString') tracks.push(f)
    else if (geom.type === 'Polygon' || geom.type === 'MultiPolygon') polygons.push(f)
    else if (geom.type === 'GeometryCollection') {
      for (const g of geom.geometries) {
        if (g.type === 'Point') points.push({ ...f, geometry: g })
        else if (g.type === 'LineString' || g.type === 'MultiLineString') tracks.push({ ...f, geometry: g })
        else if (g.type === 'Polygon' || g.type === 'MultiPolygon') polygons.push({ ...f, geometry: g })
      }
    }
  }

  for (const feature of geojson.features || []) {
    collect(feature)
  }

  return {
    points: { type: 'FeatureCollection', features: points },
    tracks: { type: 'FeatureCollection', features: tracks },
    polygons: { type: 'FeatureCollection', features: polygons },
  }
}

export function processGeoFile(xml: string, fileName: string): KmlLoadResult {
  const ext = fileName.toLowerCase().split('.').pop()
  const geojson = ext === 'gpx'
    ? parseGpxToGeoJSON(xml)
    : parseKmlToGeoJSON(xml)
  const { pointCount, trackCount, polygonCount } = countFeaturesByType(geojson)
  return {
    fileName,
    geojson,
    pointCount,
    trackCount,
    polygonCount,
  }
}
