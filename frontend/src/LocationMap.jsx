import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { api } from './api';
export default function LocationMap({
  onChoose,
  radius = 15,
  value = {},
  points = [],
  readOnly = false,
}) {
  const { t, i18n } = useTranslation(),
    host = useRef(null),
    mapRef = useRef(null),
    marker = useRef(null),
    circle = useRef(null),
    layer = useRef(null),
    handler = useRef(onChoose),
    rev = useRef(0);
  const [mapReady, setMapReady] = useState(false);
  const [message, setMessage] = useState('map_hint'),
    [query, setQuery] = useState(value.location || ''),
    [results, setResults] = useState([]),
    [lat, setLat] = useState(value.lat ?? ''),
    [lon, setLon] = useState(value.lon ?? ''),
    [busy, setBusy] = useState(false);
  handler.current = onChoose;
  function place(a, b) {
    if (!mapRef.current) return;
    marker.current?.remove();
    circle.current?.remove();
    marker.current = L.marker([a, b], {
      draggable: !readOnly,
      icon: L.divIcon({
        className: 'user-pin-marker',
        html: `<div style="background:#165f49;color:#ffffff;border-radius:50% 50% 50% 0;transform:rotate(-45deg);width:34px;height:34px;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 12px rgba(0,0,0,0.4);border:2px solid #ffffff;"><span style="transform:rotate(45deg);font-size:18px;">📍</span></div>`,
        iconSize: [34, 34],
        iconAnchor: [17, 34],
      }),
    }).addTo(mapRef.current);
    marker.current.on('dragend', () => {
      let p = marker.current.getLatLng();
      select(p.lat, p.lng);
    });
    circle.current = L.circle([a, b], {
      radius: (radius || 15) * 1000,
      color: '#165f49',
      fillColor: '#165f49',
      fillOpacity: 0.12,
      weight: 2,
    }).addTo(mapRef.current);
    // The container's real size can still be wrong here (mount timing, a
    // Suspense-loaded panel, a still-animating layout) -- jumping the view
    // before Leaflet knows the true size leaves stale tiles from the old
    // view sitting under the new one instead of being replaced. Force a
    // resize check immediately before recentring.
    mapRef.current.invalidateSize();
    mapRef.current.setView([a, b], (radius || 15) <= 5 ? 13 : (radius || 15) <= 10 ? 12 : 11);
  }
  // Dynamically update circle when radius changes
  useEffect(() => {
    if (circle.current && Number.isFinite(radius)) {
      circle.current.setRadius(radius * 1000);
      if (marker.current && mapRef.current) {
        const p = marker.current.getLatLng();
        mapRef.current.setView(p, radius <= 5 ? 13 : radius <= 10 ? 12 : 11);
      }
    }
  }, [radius]);
  async function select(a, b) {
    if (!Number.isFinite(a) || !Number.isFinite(b) || a < 8 || a > 13.7 || b < 76 || b > 80.5) {
      setMessage('outside_state');
      return;
    }
    const request = ++rev.current;
    setLat(a);
    setLon(b);
    place(a, b);
    setMessage('map_loading');
    handler.current?.({
      location: `${a.toFixed(5)}, ${b.toFixed(5)}`,
      lat: a,
      lon: b,
      district: '',
    });
    try {
      let data = await api(`/geocode?lat=${a}&lon=${b}`);
      if (request !== rev.current) return;
      handler.current?.({ ...data, lat: a, lon: b });
      setQuery(data.location);
      setMessage('map_selected');
    } catch {
      if (request === rev.current) setMessage('coordinate_fallback');
    }
  }
  useEffect(() => {
    const map = L.map(host.current, {
      center: [10.95, 78.45],
      zoom: 7,
      scrollWheelZoom: false,
      zoomControl: false,
      attributionControl: false,
    });
    mapRef.current = map;
    layer.current = L.layerGroup().addTo(map);
    // OSM's own operations team asks non-osm.org sites not to hit the a/b/c
    // load-balancing subdomains -- https://github.com/openstreetmap/operations/issues/737 --
    // requests through them get throttled/dropped under load, which is the
    // other likely cause of tiles loading for some map areas and not others.
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 18 })
      .on('tileerror', () => setMessage('tiles_unavailable'))
      .addTo(map);
    if (!readOnly) map.on('click', (e) => select(e.latlng.lat, e.latlng.lng));
    setMapReady(true);
    // A fixed-delay setTimeout guesses when the container's final size is
    // ready; it guesses wrong whenever mount happens inside a Suspense
    // boundary, a still-animating panel, or a slow-loading sidebar (exactly
    // the case here -- LocationMap mounts inside Nearby's lazy Suspense).
    // A ResizeObserver instead reacts to the container's actual size,
    // however many times it changes, and clears the leftover-tile problem
    // at its source rather than timing around it.
    map.invalidateSize();
    const observer = new ResizeObserver(() => map.invalidateSize());
    observer.observe(host.current);
    return () => {
      observer.disconnect();
      rev.current++;
      map.remove();
      mapRef.current = null;
      setMapReady(false);
    };
  }, []);
  // Place pin once map is ready AND we have coordinates — fixes auto-load from saved reports
  useEffect(() => {
    if (!mapReady) return;
    if (value.lat != null && value.lon != null) {
      setLat(value.lat);
      setLon(value.lon);
      place(value.lat, value.lon);
      if (readOnly) setMessage('map_selected');
    } else {
      marker.current?.remove();
      circle.current?.remove();
    }
  }, [value.lat, value.lon, mapReady]);
  useEffect(() => {
    layer.current?.clearLayers();
    points.forEach((p) => {
      const isComp = p.kind === 'competitor';
      const color =
        p.kind === 'bank' ? '#1d4ed8' : p.kind === 'post_office' ? '#a16207' : '#dc2626';
      const el = document.createElement('div');
      el.className = 'map-point-popup';
      const name = p.names?.[i18n.language] || p.name || (isComp ? t('competitor') : t(p.kind));
      const dist = p.distance_m ? ` · ${(p.distance_m / 1000).toFixed(1)} km` : '';
      el.innerHTML = `<strong>${name}</strong><br/><small style="color:${color};font-weight:600;">${isComp ? '🏢 ' + t('competitor') : '🏦 ' + t(p.kind)}</small><small>${dist}</small>`;
      L.circleMarker([p.lat, p.lon], {
        color: '#ffffff',
        weight: 2,
        fillColor: color,
        radius: isComp ? 8 : 7,
        fillOpacity: 0.9,
      })
        .bindPopup(el)
        .addTo(layer.current);
    });
  }, [points, i18n.language]);
  async function search() {
    const request = ++rev.current;
    setBusy(true);
    setMessage('map_loading');
    try {
      const r = await api(`/map/search?q=${encodeURIComponent(query)}`);
      if (request !== rev.current) return;
      setResults(r.items);
      setMessage(r.items.length ? 'choose_place' : 'no_places');
    } catch (e) {
      if (request === rev.current) setMessage(e.message === 'map_wait' ? 'map_wait' : 'map_failed');
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="location-map">
      {!readOnly && (
        <>
          <label htmlFor="map-search">{t('map_search')}</label>
          <div className="map-search-row">
            <input
              id="map-search"
              value={query}
              maxLength={200}
              onChange={(e) => setQuery(e.target.value)}
            />
            <button type="button" onClick={search} disabled={busy || query.trim().length < 2}>
              {t('search_map')}
            </button>
          </div>
          {results.map((r, i) => (
            <button
              className="map-result"
              type="button"
              key={i}
              onClick={() => {
                rev.current++;
                handler.current?.(r);
                setResults([]);
                setMessage('map_selected');
              }}
            >
              {r.location}
            </button>
          ))}
          <div className="form-grid">
            <div>
              <label htmlFor="map-lat">{t('latitude')}</label>
              <input
                id="map-lat"
                type="number"
                step="any"
                value={lat}
                onChange={(e) => setLat(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="map-lon">{t('longitude')}</label>
              <input
                id="map-lon"
                type="number"
                step="any"
                value={lon}
                onChange={(e) => setLon(e.target.value)}
              />
            </div>
          </div>
          <button
            type="button"
            onClick={() => {
              if (lat !== '' && lon !== '') select(Number(lat), Number(lon));
            }}
          >
            {t('use_coordinates')}
          </button>
        </>
      )}
      <p aria-live="polite">{t(message)}</p>
      <div className="actions">
        <button type="button" onClick={() => mapRef.current?.zoomIn()}>
          {t('zoom_in')}
        </button>
        <button type="button" onClick={() => mapRef.current?.zoomOut()}>
          {t('zoom_out')}
        </button>
      </div>
      <div className="map-surface" ref={host} role="region" aria-label={t('map_label')} />
      <small>
        ©{' '}
        <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">
          OpenStreetMap
        </a>{' '}
        · {t('radius_fixed')}
      </small>
    </div>
  );
}
