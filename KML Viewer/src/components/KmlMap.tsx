import { useEffect, useMemo } from 'react'
import L from 'leaflet'
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  useMap,
} from 'react-leaflet'
import type { FeatureCollection } from 'geojson'
import { splitByGeometryType } from '../lib/kmlParser'

/** GPX <sym> values to emoji/icons. Covers common Mapped PI and Gaia GPS symbols. */
const SYM_TO_EMOJI: Record<string, string> = {
  'campsite': '⛺',
  'campsite-24': '⛺',
  'cliff': '⛰️',
  'petroglyph': '🪨',
  'stone': '🪨',
  'building': '🏠',
  'building-24': '🏠',
  'attraction': '⭐',
  'cave': '🕳️',
  'bridge': '🌉',
  'off-road': '🚙',
  'water': '💧',
  'city': '🏙️',
  'city-24': '🏙️',
  'mine': '⛏️',
  'known-route': '🛤️',
}
const DEFAULT_EMOJI = '📍'

function getEmojiForSym(sym: string | undefined): string {
  if (!sym) return DEFAULT_EMOJI
  const s = String(sym)
  if (SYM_TO_EMOJI[s]) return SYM_TO_EMOJI[s]
  const lower = s.toLowerCase()
  if (SYM_TO_EMOJI[lower]) return SYM_TO_EMOJI[lower]
  const base = s.replace(/-?\d+$/, '')
  return SYM_TO_EMOJI[base] ?? SYM_TO_EMOJI[base.toLowerCase()] ?? DEFAULT_EMOJI
}

const TILE_LAYERS: Record<string, { url: string; attribution: string }> = {
  osm: {
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  },
  topo: {
    url: 'https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}',
    attribution: '&copy; <a href="https://www.usgs.gov/">USGS</a>',
  },
  satellite: {
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: '&copy; <a href="https://www.esri.com/">Esri</a>',
  },
}

interface FitBoundsProps {
  geojson: FeatureCollection | null
}

function FitBounds({ geojson }: FitBoundsProps) {
  const map = useMap()

  useEffect(() => {
    if (!geojson?.features?.length) return
    const bounds: [number, number][] = []
    const collectCoords = (coords: unknown): void => {
      if (Array.isArray(coords)) {
        if (typeof coords[0] === 'number' && typeof coords[1] === 'number') {
          bounds.push([coords[1], coords[0]])
        } else {
          coords.forEach(collectCoords)
        }
      }
    }
    for (const f of geojson.features) {
      const g = f.geometry
      if (!g) continue
      if (g.type === 'Point') bounds.push([g.coordinates[1], g.coordinates[0]])
      else if (g.type === 'LineString') g.coordinates.forEach((c) => collectCoords(c))
      else if (g.type === 'Polygon') g.coordinates.forEach((ring) => ring.forEach((c) => collectCoords(c)))
      else if (g.type === 'MultiLineString') g.coordinates.forEach((line) => line.forEach((c) => collectCoords(c)))
      else if (g.type === 'MultiPolygon') g.coordinates.forEach((poly) => poly.forEach((ring) => ring.forEach((c) => collectCoords(c))))
    }
    if (bounds.length > 0) {
      map.fitBounds(bounds, { padding: [30, 30], maxZoom: 14 })
    }
  }, [map, geojson])

  return null
}

interface KmlMapProps {
  geojson: FeatureCollection | null
  geojsonKey: string
  baseMap: string
  showPoints: boolean
  showTracks: boolean
  showPolygons: boolean
  selectedSyms: string[]
}

export function KmlMap({
  geojson,
  geojsonKey,
  baseMap,
  showPoints,
  showTracks,
  showPolygons,
  selectedSyms,
}: KmlMapProps) {
  const { points, tracks, polygons } = useMemo(() => {
    if (!geojson) return { points: { type: 'FeatureCollection' as const, features: [] }, tracks: { type: 'FeatureCollection' as const, features: [] }, polygons: { type: 'FeatureCollection' as const, features: [] } }
    const split = splitByGeometryType(geojson)
    if (selectedSyms.length > 0 && split.points.features.length > 0) {
      const set = new Set(selectedSyms)
      const filtered = split.points.features.filter(
        (f) => set.has((f.properties?.sym ?? f.properties?.Sym) as string)
      )
      split.points = { type: 'FeatureCollection', features: filtered }
    }
    return split
  }, [geojson, selectedSyms])

  const tileConfig = TILE_LAYERS[baseMap] ?? TILE_LAYERS.osm

  const pointToLayer = (feature: import('geojson').Feature, latlng: L.LatLng) => {
    const props = feature.properties ?? {}
    const name = props.name ?? props.Name ?? 'Point'
    const desc = props.description ?? props.Description ?? props.desc ?? ''
    const popup = desc ? `${name}<br/>${String(desc).slice(0, 200)}` : name
    const sym = props.sym ?? props.Sym
    if (sym) {
      const emoji = getEmojiForSym(sym)
      const icon = L.divIcon({
        html: `<span class="marker-emoji">${emoji}</span>`,
        className: 'custom-marker',
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      })
      return L.marker(latlng, { icon }).bindPopup(popup)
    }
    return L.marker(latlng).bindPopup(popup)
  }

  const style = () => ({ color: '#3388ff', weight: 3 })

  return (
    <div className="map-wrapper">
      <MapContainer
        center={[39, -111]}
        zoom={7}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom
      >
        <TileLayer
          url={tileConfig.url}
          attribution={tileConfig.attribution}
        />
        <FitBounds geojson={geojson} />
        {showPoints && points.features.length > 0 && (
          <GeoJSON
            key={`points-${geojsonKey}-${[...selectedSyms].sort().join(',')}`}
            data={points}
            pointToLayer={pointToLayer}
          />
        )}
        {showTracks && tracks.features.length > 0 && (
          <GeoJSON
            key={`tracks-${geojsonKey}`}
            data={tracks}
            style={style}
          />
        )}
        {showPolygons && polygons.features.length > 0 && (
          <GeoJSON
            key={`polygons-${geojsonKey}`}
            data={polygons}
            style={style}
          />
        )}
      </MapContainer>
    </div>
  )
}
