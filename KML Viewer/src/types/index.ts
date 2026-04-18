import type { FeatureCollection, Feature } from 'geojson'

export interface KmlLoadResult {
  fileName: string
  geojson: FeatureCollection
  pointCount: number
  trackCount: number
  polygonCount: number
}

export type { FeatureCollection, Feature }
