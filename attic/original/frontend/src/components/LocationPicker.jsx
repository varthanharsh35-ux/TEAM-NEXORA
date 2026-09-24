import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Search, MapPin, Loader2, Crosshair } from 'lucide-react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix Leaflet default marker icons in Vite/Webpack
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const userPinIcon = L.divIcon({
  className: 'custom-user-pin',
  html: `<div style="background-color: #3b5bdb; width: 34px; height: 34px; border-radius: 50%; border: 3px solid white; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(59,91,219,0.5);"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg></div>`,
  iconSize: [34, 34],
  iconAnchor: [17, 34],
  popupAnchor: [0, -34]
});

export default function LocationPicker({
  location = 'Wardha, Maharashtra',
  lat = 20.7453,
  lon = 78.6022,
  radiusKm = 5.0,
  onChange
}) {
  const { t } = useTranslation();
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markerRef = useRef(null);
  const circleRef = useRef(null);

  const [searchQuery, setSearchQuery] = useState(location);
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [currentLat, setCurrentLat] = useState(lat || 20.7453);
  const [currentLon, setCurrentLon] = useState(lon || 78.6022);
  const [currentRadius, setCurrentRadius] = useState(radiusKm || 5.0);

  // Initialize Leaflet map
  useEffect(() => {
    if (!mapContainerRef.current) return;
    if (mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [currentLat, currentLon],
      zoom: 12,
      scrollWheelZoom: true
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 18
    }).addTo(map);

    const marker = L.marker([currentLat, currentLon], { icon: userPinIcon, draggable: true }).addTo(map);
    marker.bindPopup(`<b>${searchQuery || 'Selected Location'}</b><br/>Lat: ${currentLat.toFixed(4)}, Lon: ${currentLon.toFixed(4)}`).openPopup();

    const circle = L.circle([currentLat, currentLon], {
      radius: currentRadius * 1000,
      color: '#3b5bdb',
      fillColor: '#3b5bdb',
      fillOpacity: 0.12,
      weight: 2,
      dashArray: '6, 6'
    }).addTo(map);

    mapInstanceRef.current = map;
    markerRef.current = marker;
    circleRef.current = circle;

    // Handle map click
    map.on('click', (e) => {
      const { lat: newLat, lng: newLon } = e.latlng;
      updatePosition(newLat, newLon, true);
    });

    // Handle marker drag
    marker.on('dragend', (e) => {
      const pos = e.target.getLatLng();
      updatePosition(pos.lat, pos.lng, true);
    });

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update map center & markers when lat/lon change
  const updatePosition = async (newLat, newLon, reverseGeocode = false) => {
    setCurrentLat(newLat);
    setCurrentLon(newLon);

    if (markerRef.current) {
      markerRef.current.setLatLng([newLat, newLon]);
    }
    if (circleRef.current) {
      circleRef.current.setLatLng([newLat, newLon]);
      circleRef.current.setRadius(currentRadius * 1000);
    }
    if (mapInstanceRef.current) {
      mapInstanceRef.current.panTo([newLat, newLon]);
    }

    let resolvedLocation = searchQuery;

    if (reverseGeocode) {
      try {
        const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${newLat}&lon=${newLon}`);
        if (res.ok) {
          const data = await res.json();
          resolvedLocation = data.display_name || `${newLat.toFixed(4)}, ${newLon.toFixed(4)}`;
          setSearchQuery(resolvedLocation);
          if (markerRef.current) {
            markerRef.current.setPopupContent(`<b>${resolvedLocation}</b><br/>Lat: ${newLat.toFixed(4)}, Lon: ${newLon.toFixed(4)}`).openPopup();
          }
        }
      } catch (e) {
        console.warn('Reverse geocode warning:', e);
      }
    }

    if (onChange) {
      onChange({
        location: resolvedLocation,
        lat: newLat,
        lon: newLon,
        radiusKm: currentRadius
      });
    }
  };

  const handleRadiusChange = (newRadius) => {
    setCurrentRadius(newRadius);
    if (circleRef.current) {
      circleRef.current.setRadius(newRadius * 1000);
    }
    if (onChange) {
      onChange({
        location: searchQuery,
        lat: currentLat,
        lon: currentLon,
        radiusKm: newRadius
      });
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    try {
      const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}&countrycodes=in&limit=5`);
      if (res.ok) {
        const results = await res.json();
        setSearchResults(results);
      }
    } catch (e) {
      console.warn('Geocoding search failed:', e);
    } finally {
      setIsSearching(false);
    }
  };

  const selectSearchResult = (result) => {
    const newLat = parseFloat(result.lat);
    const newLon = parseFloat(result.lon);
    setSearchQuery(result.display_name);
    setSearchResults([]);
    updatePosition(newLat, newLon, false);
    if (mapInstanceRef.current) {
      mapInstanceRef.current.setView([newLat, newLon], 13);
    }
  };

  const useCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          updatePosition(pos.coords.latitude, pos.coords.longitude, true);
          if (mapInstanceRef.current) {
            mapInstanceRef.current.setView([pos.coords.latitude, pos.coords.longitude], 13);
          }
        },
        (err) => {
          console.warn('Geolocation error:', err);
        }
      );
    }
  };

  return (
    <div className="space-y-4">
      {/* Search Bar & Auto-Detect */}
      <div className="space-y-2">
        <label className="input-label flex items-center justify-between">
          <span>{t('assessment.location_input')}</span>
          <button
            type="button"
            onClick={useCurrentLocation}
            className="text-xs text-primary-400 hover:text-primary-300 flex items-center gap-1 cursor-pointer"
          >
            <Crosshair size={12} />
            Auto-Detect Location
          </button>
        </label>
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1">
            <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="e.g. Wardha, Nagpur, Varanasi, Madurai..."
              className="input-field pl-11"
              id="location-search-input"
            />
          </div>
          <button
            type="submit"
            disabled={isSearching}
            className="btn btn-primary btn-sm px-4 cursor-pointer flex items-center gap-1"
          >
            {isSearching ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
            Search
          </button>
        </form>

        {/* Search Autocomplete Results */}
        {searchResults.length > 0 && (
          <div className="rounded-xl bg-surface-800 border border-white/10 shadow-2xl p-2 space-y-1 max-h-48 overflow-y-auto">
            {searchResults.map((item, i) => (
              <button
                key={i}
                type="button"
                onClick={() => selectSearchResult(item)}
                className="w-full text-left p-2.5 rounded-lg hover:bg-white/5 text-xs text-white/80 transition-colors flex items-start gap-2 cursor-pointer"
              >
                <MapPin size={14} className="text-primary-400 mt-0.5 flex-shrink-0" />
                <span className="truncate">{item.display_name}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Catchment Radius Slider (5 to 10 km) */}
      <div className="p-4 rounded-xl bg-white/3 border border-white/5 space-y-2">
        <div className="flex justify-between items-center text-sm">
          <span className="text-xs font-semibold text-white/60">{t('assessment.radius_label')}</span>
          <span className="font-bold text-accent-400">{currentRadius} km</span>
        </div>
        <input
          type="range"
          min="1"
          max="15"
          step="0.5"
          value={currentRadius}
          onChange={(e) => handleRadiusChange(parseFloat(e.target.value))}
          className="w-full accent-accent-500"
          id="catchment-radius-slider"
        />
        <div className="flex justify-between text-[10px] text-white/30">
          <span>1 km (Micro-Catchment)</span>
          <span>5 km (Standard Rural)</span>
          <span>15 km (Block Level)</span>
        </div>
      </div>

      {/* Interactive Leaflet Map */}
      <div className="space-y-1">
        <div
          ref={mapContainerRef}
          className="h-64 sm:h-72 rounded-xl overflow-hidden border border-white/10 shadow-inner z-0"
          id="leaflet-location-map"
        />
        <div className="flex justify-between text-[11px] text-white/40 px-1">
          <span>💡 Click anywhere or drag the pin to set exact coordinates</span>
          <span>GPS: {currentLat.toFixed(4)}, {currentLon.toFixed(4)}</span>
        </div>
      </div>
    </div>
  );
}
