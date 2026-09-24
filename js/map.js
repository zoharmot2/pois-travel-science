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

    // Render polygons below lines. Leaflet point markers already render in the
    // standard marker pane above both vector families.
    const polygonPane = map.createPane('polygonPane');
    polygonPane.style.zIndex = '410';
    const linePane = map.createPane('linePane');
    linePane.style.zIndex = '420';

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

/** Attach coordinate updates to the display hosted inside the v1.4 map panel. */
export function attachCoordinateDisplay(map) {
    map.on('mousemove', function (event) {
        const element = document.getElementById('coordsDisplay');
        if (element) {
            element.textContent = `Lat: ${event.latlng.lat.toFixed(5)} | Lon: ${event.latlng.lng.toFixed(5)}`;
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

export function attachSearchHandler(map, geojsonLayer, getEntityForFeature = null, options = {}) {
    const searchInput = document.getElementById('poiSearchInput');
    if (!searchInput) return { refresh: () => {}, close: () => {} };

    const SEARCH_DELAY_MS = 180;
    const SEARCH_RESULT_LIMIT = 8;
    let searchTimer = null;
    let currentMatches = [];
    let activeResultIndex = -1;

    const resultsElement = document.createElement('div');
    resultsElement.id = 'poiSearchResults';
    resultsElement.className = 'map-search-results';
    resultsElement.setAttribute('role', 'listbox');
    resultsElement.setAttribute('aria-label', 'POI search results');
    resultsElement.hidden = true;
    searchInput.insertAdjacentElement('afterend', resultsElement);
    searchInput.setAttribute('aria-controls', resultsElement.id);
    searchInput.setAttribute('aria-expanded', 'false');

    function normalizeSearchText(value) {
        return String(value || '').toLocaleLowerCase().trim();
    }

    function geometryLabel(entity) {
        if (!entity) return 'Entity';
        if (entity.geometryFamily === 'point') return 'Point';
        if (entity.geometryFamily === 'line') return 'Line';
        if (entity.geometryFamily === 'polygon') return 'Polygon';
        return entity.geometryType || 'Entity';
    }

    function entityDisplayName(entity, properties = {}) {
        const name = entity ? entity.name : (properties.POI_Name || properties.Name || '');
        return String(name || '').trim();
    }

    function collectSearchMatches(query) {
        const matches = [];

        geojsonLayer.eachLayer(layer => {
            const entity = getEntityForFeature ? getEntityForFeature(layer.feature) : null;
            const properties = layer.feature && layer.feature.properties ? layer.feature.properties : {};
            const displayName = entityDisplayName(entity, properties);
            const normalizedName = normalizeSearchText(displayName);
            if (!normalizedName || !normalizedName.includes(query)) return;

            let rank = 2;
            if (normalizedName === query) rank = 0;
            else if (normalizedName.startsWith(query)) rank = 1;

            matches.push({
                layer,
                entity,
                displayName,
                normalizedName,
                rank
            });
        });

        matches.sort((a, b) => (
            a.rank - b.rank ||
            a.displayName.localeCompare(b.displayName, undefined, { sensitivity: 'base' })
        ));

        return matches.slice(0, SEARCH_RESULT_LIMIT);
    }

    // Retained as a named helper because Stage 3.1 established the best-match
    // search contract. Stage 9 now exposes multiple ranked matches in the UI.
    function findBestMatchingLayer(query) {
        const bestMatch = collectSearchMatches(query)[0];
        return bestMatch ? bestMatch.layer : null;
    }

    function closeResults() {
        currentMatches = [];
        activeResultIndex = -1;
        resultsElement.innerHTML = '';
        resultsElement.hidden = true;
        searchInput.setAttribute('aria-expanded', 'false');
        searchInput.removeAttribute('aria-activedescendant');
    }

    function updateActiveResult() {
        const buttons = [...resultsElement.querySelectorAll('.map-search-result')];
        buttons.forEach((button, index) => {
            const active = index === activeResultIndex;
            button.classList.toggle('active', active);
            button.setAttribute('aria-selected', active ? 'true' : 'false');
        });

        const activeButton = buttons[activeResultIndex];
        if (activeButton) {
            searchInput.setAttribute('aria-activedescendant', activeButton.id);
            activeButton.scrollIntoView({ block: 'nearest' });
        } else {
            searchInput.removeAttribute('aria-activedescendant');
        }
    }

    function selectMatch(match) {
        if (!match) return;

        focusMapOnLayer(map, match.layer, match.entity, {
            pointZoom: 14,
            maxZoom: 14,
            padding: [40, 40]
        });

        if (typeof options.onSelectEntity === 'function' && match.entity) {
            options.onSelectEntity(match.entity, match.layer);
        } else if (typeof match.layer.openPopup === 'function') {
            match.layer.openPopup();
        }

        closeResults();
    }

    function renderSearchResults(query) {
        currentMatches = collectSearchMatches(query);
        activeResultIndex = currentMatches.length ? 0 : -1;
        resultsElement.innerHTML = '';
        resultsElement.hidden = false;
        searchInput.setAttribute('aria-expanded', 'true');

        if (!currentMatches.length) {
            const empty = document.createElement('div');
            empty.className = 'map-search-empty';
            empty.textContent = 'No matching visible entities.';
            resultsElement.appendChild(empty);
            searchInput.removeAttribute('aria-activedescendant');
            return;
        }

        currentMatches.forEach((match, index) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'map-search-result';
            button.id = `poiSearchResult-${index}`;
            button.setAttribute('role', 'option');
            button.setAttribute('aria-selected', index === activeResultIndex ? 'true' : 'false');

            const geometry = document.createElement('span');
            geometry.className = `map-search-result-geometry geometry-${match.entity ? match.entity.geometryFamily : 'unknown'}`;
            geometry.textContent = geometryLabel(match.entity);

            const text = document.createElement('span');
            text.className = 'map-search-result-text';

            const name = document.createElement('span');
            name.className = 'map-search-result-name';
            name.textContent = match.displayName;

            const meta = document.createElement('span');
            meta.className = 'map-search-result-meta';
            const type = match.entity && match.entity.type ? match.entity.type : 'Unspecified';
            const topic = match.entity && match.entity.topic ? match.entity.topic : '';
            meta.textContent = topic ? `${type} · ${topic}` : type;

            text.append(name, meta);
            button.append(geometry, text);
            button.addEventListener('click', event => {
                event.preventDefault();
                event.stopPropagation();
                selectMatch(match);
            });
            resultsElement.appendChild(button);
        });

        updateActiveResult();
    }

    function runSearch() {
        const query = normalizeSearchText(searchInput.value);
        if (!query) {
            closeResults();
            return;
        }
        renderSearchResults(query);
    }

    searchInput.addEventListener('input', function () {
        window.clearTimeout(searchTimer);
        searchTimer = window.setTimeout(runSearch, SEARCH_DELAY_MS);
    });

    searchInput.addEventListener('keydown', function (event) {
        if (event.key === 'ArrowDown' && currentMatches.length) {
            event.preventDefault();
            activeResultIndex = (activeResultIndex + 1) % currentMatches.length;
            updateActiveResult();
            return;
        }

        if (event.key === 'ArrowUp' && currentMatches.length) {
            event.preventDefault();
            activeResultIndex = (activeResultIndex - 1 + currentMatches.length) % currentMatches.length;
            updateActiveResult();
            return;
        }

        if (event.key === 'Escape') {
            closeResults();
            return;
        }

        if (event.key === 'Enter') {
            event.preventDefault();
            window.clearTimeout(searchTimer);
            const query = normalizeSearchText(searchInput.value);
            if (!query) {
                closeResults();
                return;
            }

            if (!currentMatches.length) {
                renderSearchResults(query);
            }
            const match = currentMatches[activeResultIndex >= 0 ? activeResultIndex : 0];
            if (match) selectMatch(match);
        }
    });

    document.addEventListener('click', event => {
        if (event.target === searchInput || resultsElement.contains(event.target)) return;
        closeResults();
    });

    return {
        refresh: () => {
            const query = normalizeSearchText(searchInput.value);
            if (query && !resultsElement.hidden) renderSearchResults(query);
        },
        close: closeResults,
        findBestMatchingLayer
    };
}

export function attachOverlayHandlers(map) {
    let terminatorLayer = null;
    let timezonesLayer = null;

    const dayNightButton = document.getElementById('btnDayNight');
    const timezonesButton = document.getElementById('btnTimezones');
    if (!dayNightButton || !timezonesButton) return;

    dayNightButton.addEventListener('click', function () {
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

    timezonesButton.addEventListener('click', function () {
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
