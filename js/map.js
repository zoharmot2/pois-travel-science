export function createMap() {
    const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap'
    });

    const satelliteLayer = L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        { maxZoom: 19, attribution: 'Tiles © Esri' }
    );

    const topoLayer = L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
        { maxZoom: 19, attribution: 'Tiles © Esri' }
    );

    const lightLayer = L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}',
        { maxZoom: 16, attribution: 'Tiles © Esri' }
    );

    const historicalLayer = L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}',
        { maxZoom: 16, attribution: 'National Geographic, Esri' }
    );

    const map = L.map('map', { layers: [osmLayer] });

    const baseMaps = {
        OpenStreetMap: osmLayer,
        'Satellite (Esri World Imagery)': satelliteLayer,
        'Topographic (Esri Topo)': topoLayer,
        'Light (Esri Light Gray)': lightLayer,
        'Historic (NatGeo/Esri)': historicalLayer
    };

    L.control.layers(baseMaps, null, { position: 'topright' }).addTo(map);
    return map;
}

export function addUtilityControls(map) {
    const extraControls = L.control({ position: 'topright' });
    extraControls.onAdd = function () {
        const div = L.DomUtil.create('div', 'custom-control-box');
        div.innerHTML = `
            <div class="search-container" style="margin-bottom: 6px;">
                <input type="text" id="poiSearchInput" class="search-input" placeholder="Search POI by name..." />
            </div>
            <div style="display: flex; gap: 4px;">
                <button id="btnDayNight" class="btn-control">Day/Night</button>
                <button id="btnTimezones" class="btn-control">Time Zones</button>
            </div>
        `;
        L.DomEvent.disableClickPropagation(div);
        return div;
    };
    extraControls.addTo(map);
}

export function addCoordinateControl(map) {
    const coordsControl = L.control({ position: 'topleft' });
    coordsControl.onAdd = function () {
        const div = L.DomUtil.create('div', 'coords-box');
        div.id = 'coordsDisplay';
        div.innerHTML = 'Lat: -- | Lon: --';
        return div;
    };
    coordsControl.addTo(map);

    map.on('mousemove', function (event) {
        const element = document.getElementById('coordsDisplay');
        if (element) {
            element.innerHTML = `Lat: ${event.latlng.lat.toFixed(5)} | Lon: ${event.latlng.lng.toFixed(5)}`;
        }
    });
}

export function setInitialExtent(map, config, geojsonLayer) {
    const initialExtent = config.mapConfig && config.mapConfig.initialExtent;
    if (initialExtent && initialExtent.useCustomExtent) {
        map.fitBounds(initialExtent.bounds);
    } else if (geojsonLayer.getBounds().isValid()) {
        map.fitBounds(geojsonLayer.getBounds(), { padding: [40, 40] });
    }
}

function hasValidLayerBounds(layer) {
    if (!layer || typeof layer.getBounds !== 'function') return false;
    const bounds = layer.getBounds();
    return Boolean(bounds && typeof bounds.isValid === 'function' && bounds.isValid());
}

/**
 * Focus the map on any supported Leaflet geometry layer.
 *
 * Point layers use getLatLng(). Line/polygon layers use getBounds(). A final
 * Entity representative-point fallback keeps the navigation contract independent
 * from the concrete Leaflet layer implementation.
 */
export function focusMapOnLayer(map, layer, entity = null, options = {}) {
    if (!map || !layer) return false;

    const pointZoom = Number.isFinite(options.pointZoom) ? options.pointZoom : null;
    const maxZoom = Number.isFinite(options.maxZoom) ? options.maxZoom : 14;
    const padding = Array.isArray(options.padding) ? options.padding : [40, 40];

    if (typeof layer.getLatLng === 'function') {
        const latlng = layer.getLatLng();
        if (latlng) {
            if (pointZoom !== null && typeof map.setView === 'function') {
                map.setView(latlng, pointZoom, { animate: false });
            } else if (typeof map.panTo === 'function') {
                map.panTo(latlng, { animate: false });
            }
            return true;
        }
    }

    if (hasValidLayerBounds(layer) && typeof map.fitBounds === 'function') {
        map.fitBounds(layer.getBounds(), {
            padding,
            maxZoom,
            animate: false
        });
        return true;
    }

    const point = entity && entity.representativePoint;
    if (point && Number.isFinite(point.latitude) && Number.isFinite(point.longitude)) {
        const latlng = [point.latitude, point.longitude];
        if (pointZoom !== null && typeof map.setView === 'function') {
            map.setView(latlng, pointZoom, { animate: false });
        } else if (typeof map.panTo === 'function') {
            map.panTo(latlng, { animate: false });
        }
        return true;
    }

    return false;
}

export function attachSearchHandler(map, geojsonLayer, getEntityForFeature = null) {
    const searchInput = document.getElementById('poiSearchInput');
    if (!searchInput) return;

    const SEARCH_DELAY_MS = 180;
    let searchTimer = null;
    let lastOpenedLayer = null;

    function normalizeSearchText(value) {
        return String(value || '').toLocaleLowerCase().trim();
    }

    function findBestMatchingLayer(query) {
        let exactMatch = null;
        let prefixMatch = null;
        let partialMatch = null;

        geojsonLayer.eachLayer(layer => {
            if (exactMatch) return;

            const entity = getEntityForFeature ? getEntityForFeature(layer.feature) : null;
            const properties = layer.feature && layer.feature.properties ? layer.feature.properties : {};
            const name = normalizeSearchText(
                entity ? entity.name : (properties.POI_Name || properties.Name || '')
            );

            if (!name) return;
            if (name === query) {
                exactMatch = layer;
            } else if (!prefixMatch && name.startsWith(query)) {
                prefixMatch = layer;
            } else if (!partialMatch && name.includes(query)) {
                partialMatch = layer;
            }
        });

        return exactMatch || prefixMatch || partialMatch;
    }

    function runSearch() {
        const query = normalizeSearchText(searchInput.value);
        if (!query) {
            lastOpenedLayer = null;
            return;
        }

        const matchedLayer = findBestMatchingLayer(query);
        if (!matchedLayer || matchedLayer === lastOpenedLayer) return;

        lastOpenedLayer = matchedLayer;
        const entity = getEntityForFeature ? getEntityForFeature(matchedLayer.feature) : null;
        focusMapOnLayer(map, matchedLayer, entity, { pointZoom: 14, maxZoom: 14 });
        if (typeof matchedLayer.openPopup === 'function') {
            matchedLayer.openPopup();
        }
    }

    searchInput.addEventListener('input', function () {
        window.clearTimeout(searchTimer);
        searchTimer = window.setTimeout(runSearch, SEARCH_DELAY_MS);
    });

    searchInput.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
            window.clearTimeout(searchTimer);
            runSearch();
        }
    });
}

export function attachOverlayHandlers(map) {
    let terminatorLayer = null;
    let timezonesLayer = null;

    document.getElementById('btnDayNight').addEventListener('click', function () {
        if (!terminatorLayer) {
            terminatorLayer = L.terminator({ fillOpacity: 0.35 });
            terminatorLayer.addTo(map);
            this.classList.add('active');
        } else {
            map.removeLayer(terminatorLayer);
            terminatorLayer = null;
            this.classList.remove('active');
        }
    });

    document.getElementById('btnTimezones').addEventListener('click', function () {
        const button = this;

        if (!timezonesLayer) {
            button.textContent = 'Loading...';

            fetch('https://cdn.jsdelivr.net/gh/nvkelso/natural-earth-vector@master/geojson/ne_10m_time_zones.geojson')
                .then(response => {
                    if (!response.ok) throw new Error(`HTTP status ${response.status}`);
                    return response.json();
                })
                .then(timezoneData => {
                    timezonesLayer = L.geoJSON(timezoneData, {
                        style: {
                            color: '#0284c7',
                            weight: 1.5,
                            opacity: 0.75,
                            fillColor: '#38bdf8',
                            fillOpacity: 0.12
                        },
                        onEachFeature: function (feature, layer) {
                            if (feature.properties) {
                                const timezoneName =
                                    feature.properties.name ||
                                    feature.properties.NAME ||
                                    feature.properties.utc_format ||
                                    '';
                                if (timezoneName) {
                                    layer.bindTooltip(`UTC: ${timezoneName}`, { sticky: true });
                                }
                            }
                        }
                    }).addTo(map);
                    button.classList.add('active');
                    button.textContent = 'Time Zones';
                })
                .catch(error => {
                    console.warn('GeoJSON fetch failed; falling back to Esri TileLayer:', error);
                    timezonesLayer = L.tileLayer(
                        'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Time_Zones/MapServer/tile/{z}/{y}/{x}',
                        {
                            maxZoom: 18,
                            opacity: 0.8,
                            attribution: 'Tiles © Esri'
                        }
                    ).addTo(map);
                    button.classList.add('active');
                    button.textContent = 'Time Zones';
                });
        } else {
            map.removeLayer(timezonesLayer);
            timezonesLayer = null;
            button.classList.remove('active');
        }
    });
}
