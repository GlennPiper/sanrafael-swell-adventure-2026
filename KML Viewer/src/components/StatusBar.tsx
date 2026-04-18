import type { KmlLoadResult } from '../types'

interface StatusBarProps {
  result: KmlLoadResult | null
}

export function StatusBar({ result }: StatusBarProps) {
  if (!result) {
    return (
      <div className="status-bar">
        No file loaded. Use &quot;Load KML/GPX&quot; or drag & drop a KML or GPX file.
      </div>
    )
  }

  const parts: string[] = []
  if (result.pointCount > 0) parts.push(`${result.pointCount} point${result.pointCount !== 1 ? 's' : ''}`)
  if (result.trackCount > 0) parts.push(`${result.trackCount} track${result.trackCount !== 1 ? 's' : ''}`)
  if (result.polygonCount > 0) parts.push(`${result.polygonCount} polygon${result.polygonCount !== 1 ? 's' : ''}`)

  return (
    <div className="status-bar">
      <strong>{result.fileName}</strong>
      {parts.length > 0 && ` — ${parts.join(', ')}`}
    </div>
  )
}
