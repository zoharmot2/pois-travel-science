import { loadAppData } from './data.js';
import { applyEmbedMode } from './embed.js';
import { attachPopupDetailButton, createEntityDetailPanel } from './details.js';
import {
    buildPopupContent,
    createCustomIcon,
    createEntityFeatureIndex,
    createVectorStyle,
    entitiesToFeatureCollection
} from './entities.js';
import {
    addMapControlPanel,
    computeFilterFacets,
    createFilterState,
    createGeometryFilterItems,
    createTypeFilterItems,
    filterEntitiesByTypeAndGeometry
} from './filters.js';
import {
    attachCoordinateDisplay,
    attachOverlayHandlers,
    attachSearchHandler,
    createMap,
    setInitialExtent
} from './map.js';

applyEmbedMode();

const map = createMap();

const detailPanel = createEntityDetailPanel({
    onVisibilityChange: () => {
        window.setTimeout(() => map.invalidateSize({ pan: false }), 0);
    }
});

let geojsonLayer = null;
let allEntities = [];
let entityFeatureIndex = new WeakMap();
let activeTypesState = {};
let activeGeometryState = {};
let typeSettingsGlobal = {};
let defaultStyleGlobal = {};
let mapControlPanel = null;
let searchController = null;

function getEntityForFeature(feature) {
    return entityFeatureIndex.get(feature) || null;
}

function refreshMapEntities() {
    if (!geojsonLayer) return;

    geojsonLayer.clearLayers();
    const filteredEntities = filterEntitiesByTypeAndGeometry(
        allEntities,
        activeTypesState,
        activeGeometryState
    );
    geojsonLayer.addData(entitiesToFeatureCollection(filteredEntities));

    const activeDetailEntity = detailPanel.getActiveEntity();
    if (activeDetailEntity && !filteredEntities.includes(activeDetailEntity)) {
        detailPanel.close();
    }

    const totalCount = allEntities.length;
    document.getElementById('poiCount').textContent = filteredEntities.length === totalCount
        ? `${totalCount} entities`
        : `${filteredEntities.length} / ${totalCount} entities`;

    if (mapControlPanel && typeof mapControlPanel.updateFilterSummary === 'function') {
        mapControlPanel.updateFilterSummary(
            computeFilterFacets(allEntities, activeTypesState, activeGeometryState)
        );
    }

    if (searchController && typeof searchController.refresh === 'function') {
        searchController.refresh();
    }
}

loadAppData()
    .then(({ config, entities, geometrySummary }) => {
        allEntities = entities;
        console.info(
            `Loaded spatial entities: ${geometrySummary.point} points, ${geometrySummary.line} lines, ` +
            `${geometrySummary.polygon} polygons${geometrySummary.unknown ? `, ${geometrySummary.unknown} unknown` : ''}.`
        );
        entityFeatureIndex = createEntityFeatureIndex(allEntities);

        const symbologyConfig = config.symbology || {};
        typeSettingsGlobal = symbologyConfig.types || {};
        defaultStyleGlobal = symbologyConfig.default || {
            color: '#64748B',
            visible: true,
            label: 'Other Type',
            point: { shape: 'circle', radius: 7 },
            line: { weight: 4, opacity: 0.85 },
            polygon: { weight: 2, opacity: 0.9, fillOpacity: 0.18 }
        };

        const typeFilterItems = createTypeFilterItems(
            allEntities,
            typeSettingsGlobal,
            defaultStyleGlobal
        );
        const geometryFilterItems = createGeometryFilterItems(allEntities);

        activeTypesState = createFilterState(typeFilterItems);
        activeGeometryState = createFilterState(geometryFilterItems);

        const unconfiguredTypes = typeFilterItems.filter(
            item => !item.configured && !item.synthetic && item.count > 0
        );
        if (unconfiguredTypes.length) {
            console.warn(
                'POI_Type values are present in data but missing from config symbology. ' +
                'They remain visible and filterable using the default style:',
                unconfiguredTypes.map(item => item.value)
            );
        }

        geojsonLayer = L.geoJSON(null, {
            pointToLayer: function (feature, latlng) {
                const entity = getEntityForFeature(feature);
                const typeValue = entity ? entity.type : '';
                const setting = typeSettingsGlobal[typeValue] || defaultStyleGlobal;
                const pointSetting = setting.point || defaultStyleGlobal.point || {};
                const icon = createCustomIcon(
                    pointSetting.shape || 'circle',
                    setting.color || defaultStyleGlobal.color || '#64748B',
                    pointSetting.radius ?? 7
                );
                return L.marker(latlng, { icon });
            },
            style: function (feature) {
                const entity = getEntityForFeature(feature);
                const typeValue = entity ? entity.type : '';
                const setting = typeSettingsGlobal[typeValue] || defaultStyleGlobal;
                const geometryFamily = entity ? entity.geometryFamily : 'line';
                return createVectorStyle(setting, geometryFamily, defaultStyleGlobal);
            },
            onEachFeature: function (feature, layer) {
                const entity = getEntityForFeature(feature);
                if (entity) {
                    layer.bindPopup(buildPopupContent(entity));
                    attachPopupDetailButton(layer, entity, detailPanel, map);
                }
            }
        }).addTo(map);

        mapControlPanel = addMapControlPanel(map, {
            typeItems: typeFilterItems,
            geometryItems: geometryFilterItems,
            activeTypesState,
            activeGeometryState,
            onChange: refreshMapEntities
        });

        refreshMapEntities();
        setInitialExtent(map, config, geojsonLayer);

        searchController = attachSearchHandler(map, geojsonLayer, getEntityForFeature, {
            onSelectEntity: (entity) => {
                if (map && typeof map.closePopup === 'function') map.closePopup();
                detailPanel.open(entity);
            }
        });
        attachOverlayHandlers(map);
        attachCoordinateDisplay(map);
    })
    .catch(error => {
        console.error('Error loading application data:', error);
        document.getElementById('poiCount').textContent = 'Load error';
    });
