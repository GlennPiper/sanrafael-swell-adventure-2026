import { useRef } from 'react'

interface FileLoaderProps {
  onLoad: (xml: string, fileName: string) => void
  onError?: (err: string) => void
}

export function FileLoader({ onLoad, onError }: FileLoaderProps) {
  const inputRef = useRef<HTMLInputElement>(null)

  const ACCEPTED = ['.kml', '.kmz', '.gpx']
  const handleFile = (file: File) => {
    const ext = '.' + file.name.toLowerCase().split('.').pop()
    if (!ACCEPTED.includes(ext)) {
      onError?.(`Please select a .kml, .kmz, or .gpx file (got ${file.name})`)
      return
    }
    const reader = new FileReader()
    reader.onload = () => {
      const text = reader.result as string
      if (text) onLoad(text, file.name)
      else onError?.('Could not read file')
    }
    reader.onerror = () => onError?.('Failed to read file')
    reader.readAsText(file)
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
    e.target.value = ''
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    const file = e.dataTransfer.files?.[0]
    if (file) handleFile(file)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }

  return (
    <div className="file-loader">
      <input
        ref={inputRef}
        type="file"
        accept=".kml,.kmz,.gpx"
        onChange={handleInputChange}
        style={{ display: 'none' }}
      />
      <button type="button" onClick={() => inputRef.current?.click()}>
        Load KML/GPX
      </button>
      <div
        className="drop-zone"
        onDrop={handleDrop}
        onDragOver={handleDragOver}
      >
        or drag & drop .kml, .kmz, .gpx
      </div>
    </div>
  )
}
