'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

interface StateFeature {
  name: string
  aqi: number
  category: string
}

const AQI_RANGES = [
  { max: 50, label: 'Good', color: '#00E400', opacity: 0.7 },
  { max: 100, label: 'Satisfactory', color: '#FFFF00', opacity: 0.75 },
  { max: 200, label: 'Moderate', color: '#FF7E00', opacity: 0.8 },
  { max: 300, label: 'Poor', color: '#FF0000', opacity: 0.8 },
  { max: 400, label: 'Very Poor', color: '#99004C', opacity: 0.85 },
  { max: 500, label: 'Severe', color: '#7E0023', opacity: 0.9 },
]

const AQI_COLORS_RECORD: Record<string, string> = {
  Good: '#00E400',
  Satisfactory: '#FFFF00',
  Moderate: '#FF7E00',
  Poor: '#FF0000',
  'Very Poor': '#99004C',
  Severe: '#7E0023',
}

function getColorForAqi(aqi: number): string {
  for (const r of AQI_RANGES) {
    if (aqi <= r.max) return r.color
  }
  return '#7E0023'
}

const TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'

export function CityMap() {
  const mapContainer = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const popupRef = useRef<maplibregl.Popup | null>(null)
  const [mapLoaded, setMapLoaded] = useState(false)
  const [mapError, setMapError] = useState<string | null>(null)
  const [selectedState, setSelectedState] = useState<StateFeature | null>(null)
  const [viewState, setViewState] = useState<'india' | 'state'>('india')
  const [aqiFilter, setAqiFilter] = useState<string>('all')
  const [statesData, setStatesData] = useState<StateFeature[]>([])

  const filterOptions = ['all', 'Good', 'Satisfactory', 'Moderate', 'Poor', 'Very Poor', 'Severe']

  const flyToState = useCallback((name: string) => {
    const map = mapRef.current
    if (!map) return
    const features = map.querySourceFeatures('india-states')
    const target = features.find((f) => f.properties?.name === name)
    if (target?.geometry && target.geometry.type === 'Polygon') {
      const coords = (target.geometry as any).coordinates[0] as [number, number][]
      const bounds = coords.reduce(
        (b: [[number, number], [number, number]], c: [number, number]) => {
          b[0][0] = Math.min(b[0][0], c[0])
          b[0][1] = Math.min(b[0][1], c[1])
          b[1][0] = Math.max(b[1][0], c[0])
          b[1][1] = Math.max(b[1][1], c[1])
          return b
        },
        [[180, 90], [-180, -90]] as [[number, number], [number, number]]
      )
      map.fitBounds(bounds, { padding: 100, duration: 1000 })
      setViewState('state')
    }
  }, [])

  const resetView = useCallback(() => {
    const map = mapRef.current
    if (!map) return
    map.flyTo({ center: [78.96, 22.59], zoom: 4.5, duration: 1000 })
    setViewState('india')
    setSelectedState(null)
  }, [])

  useEffect(() => {
    const container = mapContainer.current
    if (!container || mapRef.current) return

    if (container.clientWidth === 0 || container.clientHeight === 0) {
      const ro = new ResizeObserver(() => {
        if (container.clientWidth > 0 && container.clientHeight > 0) {
          ro.disconnect()
          initMap(container)
        }
      })
      ro.observe(container)
      return () => ro.disconnect()
    }

    initMap(container)

    function initMap(el: HTMLDivElement) {
      try {
        const map = new maplibregl.Map({
          container: el,
          style: {
            version: 8,
            sources: {
              'osm-tiles': {
                type: 'raster',
                tiles: [TILE_URL],
                tileSize: 256,
                attribution: '&copy; OpenStreetMap contributors',
              },
            },
            layers: [
              { id: 'osm-tiles', type: 'raster', source: 'osm-tiles', minzoom: 0, maxzoom: 19 },
            ],
          },
          center: [78.96, 22.59],
          zoom: 4.5,
          minZoom: 3,
          maxZoom: 10,
          attributionControl: false,
        })

        map.addControl(new maplibregl.NavigationControl(), 'top-right')

        map.on('load', async () => {
          try {
            const resp = await fetch('/data/india-states.json')
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
            const geoData = await resp.json()

            const states: StateFeature[] = geoData.features.map(
              (f: any) => f.properties as StateFeature
            )
            setStatesData(states)

            map.addSource('india-states', { type: 'geojson', data: geoData })

            map.addLayer({
              id: 'states-fill', type: 'fill', source: 'india-states',
              paint: {
                'fill-color': [
                  'match', ['get', 'category'],
                  'Good', '#00E400', 'Satisfactory', '#FFFF00', 'Moderate', '#FF7E00',
                  'Poor', '#FF0000', 'Very Poor', '#99004C', 'Severe', '#7E0023',
                  '#888888',
                ],
                'fill-opacity': ['case', ['boolean', ['feature-state', 'hover'], false], 0.85, 0.65],
              },
            })

            map.addLayer({
              id: 'states-outline', type: 'line', source: 'india-states',
              paint: { 'line-color': 'rgba(255,255,255,0.4)', 'line-width': 1.5 },
            })

            map.addLayer({
              id: 'states-highlight', type: 'line', source: 'india-states',
              paint: { 'line-color': 'rgba(56, 189, 248, 0.9)', 'line-width': 3, 'line-opacity': 0 },
            })

            map.addLayer({
              id: 'state-labels', type: 'symbol', source: 'india-states',
              layout: {
                'text-field': ['get', 'name'],
                'text-size': ['interpolate', ['linear'], ['zoom'], 4, 7, 7, 9, 10, 11],
                'text-offset': [0, 0.5],
                'text-anchor': 'center',
              },
              paint: {
                'text-color': '#ffffff', 'text-halo-color': 'rgba(0,0,0,0.7)',
                'text-halo-width': 1.5, 'text-opacity': 0.9,
              },
            })

            map.addLayer({
              id: 'aqi-labels', type: 'symbol', source: 'india-states',
              layout: {
                'text-field': ['concat', 'AQI ', ['to-string', ['get', 'aqi']]],
                'text-size': ['interpolate', ['linear'], ['zoom'], 4, 6, 7, 7, 10, 9],
                'text-offset': [0, -0.5],
                'text-anchor': 'center',
              },
              paint: {
                'text-color': 'rgba(255,255,255,0.85)', 'text-halo-color': 'rgba(0,0,0,0.6)',
                'text-halo-width': 1, 'text-opacity': 0.8,
              },
            })

            setMapLoaded(true)
          } catch (e: any) {
            console.error('Map data error:', e)
            setMapError('Failed to load India states data')
            setMapLoaded(true)
          }
        })

        map.on('error', (e) => {
          console.error('Map error:', e)
          setMapError('Map render error')
        })

        map.on('tileerror', () => {
          setMapError('Tile server unreachable — check internet')
        })

        // Hover
        let hoveredId: string | null = null
        map.on('mousemove', 'states-fill', (e) => {
          if (e.features?.[0]) {
            const id = e.features[0].id as string
            if (hoveredId !== null) map.setFeatureState({ source: 'india-states', id: hoveredId }, { hover: false })
            hoveredId = id
            map.setFeatureState({ source: 'india-states', id }, { hover: true })
            map.getCanvas().style.cursor = 'pointer'
          }
        })
        map.on('mouseleave', 'states-fill', () => {
          if (hoveredId !== null) {
            map.setFeatureState({ source: 'india-states', id: hoveredId }, { hover: false })
            hoveredId = null
          }
          map.getCanvas().style.cursor = ''
        })

        // Click
        map.on('click', 'states-fill', (e) => {
          if (!e.features?.[0]) return
          const props = e.features[0].properties as any
          const state: StateFeature = { name: props.name, aqi: props.aqi, category: props.category }
          setSelectedState(state)
          flyToState(state.name)

          if (popupRef.current) popupRef.current.remove()
          const color = getColorForAqi(state.aqi)
          const popup = new maplibregl.Popup({ offset: 25, closeButton: true, closeOnClick: false })
            .setLngLat(e.lngLat as any)
            .setHTML(`
              <div style="font-family:Inter,sans-serif;background:#0f172a;color:#e2e8f0;padding:12px 16px;border-radius:12px;border:1px solid rgba(56,189,248,0.2);min-width:180px;">
                <div style="font-size:13px;font-weight:700;margin-bottom:6px;color:white;">${state.name}</div>
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                  <span style="width:10px;height:10px;border-radius:50%;background:${color};display:inline-block;"></span>
                  <span style="font-size:22px;font-weight:800;">${state.aqi}</span>
                  <span style="font-size:11px;color:#94a3b8;">AQI</span>
                </div>
                <div style="font-size:11px;color:${color};font-weight:600;">${state.category}</div>
                <div style="margin-top:8px;padding-top:8px;border-top:1px solid rgba(255,255,255,0.08);font-size:10px;color:#64748b;">Click to explore state details</div>
              </div>
            `)
            .addTo(map)
          popupRef.current = popup

          // Send custom event for panel
          window.dispatchEvent(new CustomEvent('state-selected', { detail: state }))
        })

        mapRef.current = map
      } catch (e: any) {
        console.error('Map init error:', e)
        setMapError(e.message || 'Failed to initialize map')
        setMapLoaded(true)
      }
    }

    return () => {
      mapRef.current?.remove()
      mapRef.current = null
    }
  }, [flyToState])

  // Filter
  useEffect(() => {
    const map = mapRef.current
    if (!map || !mapLoaded) return
    const filter: any = aqiFilter === 'all' ? undefined : ['==', ['get', 'category'], aqiFilter]
    const layers = ['states-fill', 'states-outline', 'state-labels', 'aqi-labels', 'states-highlight']
    layers.forEach((l) => map.setFilter(l, filter))
  }, [aqiFilter, mapLoaded])

  // Stats
  const stateAQISummary = (() => {
    if (statesData.length === 0) return null
    const worst = statesData.reduce((a, b) => (a.aqi > b.aqi ? a : b))
    const best = statesData.reduce((a, b) => (a.aqi < b.aqi ? a : b))
    const avg = Math.round(statesData.reduce((s, st) => s + st.aqi, 0) / statesData.length)
    const poorCount = statesData.filter((s) => s.aqi > 200).length
    return { worst, best, avg, poorCount, total: statesData.length }
  })()

  return (
    <div className="relative rounded-xl overflow-hidden border border-gray-800/60 bg-gray-950 shadow-2xl shadow-black/40 w-full" style={{ height: '100%', minHeight: '480px' }}>
      {/* Map container */}
      <div ref={mapContainer} className="absolute inset-0" />

      {/* Error overlay */}
      {mapError && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-950/90 z-30">
          <div className="text-center max-w-sm px-6">
            <div className="w-12 h-12 rounded-xl bg-red-500/10 flex items-center justify-center mx-auto mb-3">
              <span className="text-red-400 text-xl">!</span>
            </div>
            <p className="text-sm font-medium text-gray-300 mb-1">Map unavailable</p>
            <p className="text-xs text-gray-500 mb-4">{mapError}</p>
            <button
              onClick={() => { setMapError(null); setMapLoaded(false); window.location.reload() }}
              className="px-4 py-2 bg-vayu-600 hover:bg-vayu-500 text-white text-xs font-medium rounded-lg transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* View toggle */}
      <div className="absolute top-3 left-3 z-10 flex gap-1.5 rounded-lg bg-gray-900/85 backdrop-blur-sm border border-gray-800/60 shadow-lg p-1">
        <button
          onClick={resetView}
          className={`px-2.5 py-1.5 text-[10px] font-medium rounded-md transition-all ${
            viewState === 'india' ? 'bg-vayu-600/30 text-vayu-300' : 'text-gray-400 hover:text-gray-200'
          }`}
        >
          India
        </button>
        <button
          className={`px-2.5 py-1.5 text-[10px] font-medium rounded-md transition-all ${
            viewState === 'state' ? 'bg-vayu-600/30 text-vayu-300' : 'text-gray-400 hover:text-gray-200'
          }`}
        >
          State
        </button>
      </div>

      {/* AQI Legend */}
      <div className="absolute top-3 right-3 z-10 bg-gray-900/85 backdrop-blur-sm rounded-xl border border-gray-800/60 shadow-lg p-2.5 min-w-[120px]">
        <div className="text-[9px] font-semibold text-gray-400 uppercase tracking-wider mb-1.5 text-center">AQI</div>
        {AQI_RANGES.map((r) => (
          <div key={r.label} className="flex items-center gap-2 py-0.5">
            <span className="w-3 h-3 rounded" style={{ backgroundColor: r.color, opacity: r.opacity }} />
            <span className="text-[8px] text-gray-300">{r.label}</span>
          </div>
        ))}
      </div>

      {/* Filter */}
      <div className="absolute bottom-3 left-3 z-10">
        <div className="flex gap-1 rounded-lg bg-gray-900/85 backdrop-blur-sm border border-gray-800/60 shadow-lg p-1.5 flex-wrap">
          {filterOptions.map((f) => (
            <button
              key={f}
              onClick={() => setAqiFilter(f)}
              className={`px-2 py-1 text-[8px] font-medium rounded-md transition-all ${
                aqiFilter === f ? 'bg-vayu-600/30 text-vayu-300' : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              {f === 'all' ? 'All' : f}
            </button>
          ))}
        </div>
      </div>

      {/* Summary card */}
      {stateAQISummary && (
        <div className="absolute bottom-3 right-3 z-10">
          <div className="bg-gray-900/85 backdrop-blur-sm rounded-xl border border-gray-800/60 shadow-lg p-3 min-w-[160px]">
            <div className="flex items-center justify-between gap-3">
              <div className="text-center">
                <div className="text-[8px] text-gray-500 uppercase tracking-wider">Avg AQI</div>
                <div className="text-sm font-bold text-white">{stateAQISummary.avg}</div>
              </div>
              <div className="w-px h-7 bg-gray-800" />
              <div className="text-center">
                <div className="text-[8px] text-gray-500 uppercase tracking-wider">Worst</div>
                <div className="text-[10px] font-bold text-red-400">{stateAQISummary.worst.name.split(' ')[0]}</div>
                <div className="text-[9px] text-red-400">{stateAQISummary.worst.aqi}</div>
              </div>
              <div className="w-px h-7 bg-gray-800" />
              <div className="text-center">
                <div className="text-[8px] text-gray-500 uppercase tracking-wider">Best</div>
                <div className="text-[10px] font-bold text-green-400">{stateAQISummary.best.name.split(' ')[0]}</div>
                <div className="text-[9px] text-green-400">{stateAQISummary.best.aqi}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* State detail bar */}
      {selectedState && (
        <div className="absolute left-3 right-3 bottom-16 z-10 animate-slide-up">
          <div className="bg-gray-900/90 backdrop-blur-xl rounded-xl border border-vayu-500/20 shadow-2xl p-3">
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <div className="flex items-center gap-3">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: getColorForAqi(selectedState.aqi) }} />
                <span className="text-sm font-bold text-white">{selectedState.name}</span>
                <span className="text-lg font-bold" style={{ color: getColorForAqi(selectedState.aqi) }}>{selectedState.aqi}</span>
                <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${
                  selectedState.aqi > 200 ? 'bg-red-500/15 text-red-400' : 'bg-emerald-500/15 text-emerald-400'
                }`}>{selectedState.category}</span>
              </div>
              <button onClick={resetView} className="text-[10px] text-gray-400 hover:text-gray-200 px-2.5 py-1 rounded-lg bg-gray-800/60 transition-colors">
                ← Back to India
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Loading */}
      {!mapLoaded && !mapError && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-950 z-20">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-vayu-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
            <p className="text-xs text-gray-500">Loading India map...</p>
          </div>
        </div>
      )}
    </div>
  )
}
