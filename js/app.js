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
    addEntityFiltersControl,
    createFilterState,
    createTopicFilterItems,
    createTypeFilterItems,
    filterEntitiesByDimensions
} from './filters.js';
import {
    addCoordinateControl,
    addUtilityControls,
    attachOverlayHandlers,
    attachSearchHandler,
    createMap,
    setInitialExtent
} from './map.js';

applyEmbedMode();

const map = createMap();
addUtilityControls(map);

const detailPanel = createEntityDetailPanel({
    onVisibilityChange: () => {
        window.setTimeout(() => map.invalidateSize({ pan: false }), 0);
    }
});

let geojsonLayer = null;
let allEntities = [];
let entityFeatureIndex = new WeakMap();
let activeTopicsState = {};
let activeTypesState = {};
let topicSettingsGlobal = {};
let defaultStyleGlobal = {};

function getEntityForFeature(feature) {
    return entityFeatureIndex.get(feature) || null;
}

function refreshMapEntities() {
    if (!geojsonLayer) return;

    geojsonLayer.clearLayers();
    const filteredEntities = filterEntitiesByDimensions(
        allEntities,
        activeTopicsState,
        activeTypesState
    );
    geojsonLayer.addData(entitiesToFeatureCollection(filteredEntities));

    const activeDetailEntity = detailPanel.getActiveEntity();
    if (activeDetailEntity && !filteredEntities.includes(activeDetailEntity)) {
        detailPanel.close();
    }

    document.getElementById('poiCount').textContent = `${filteredEntities.length} POIs`;
}

loadAppData()
    .then(({ config, entities }) => {
        allEntities = entities;
        entityFeatureIndex = createEntityFeatureIndex(allEntities);

        const symbologyConfig = config.symbology || {};
        topicSettingsGlobal = symbologyConfig.topics || {};
        defaultStyleGlobal = symbologyConfig.default || {
            color: '#64748B',
            shape: 'circle',
            label: 'Other'
        };

        const topicFilterItems = createTopicFilterItems(
            allEntities,
            topicSettingsGlobal,
            defaultStyleGlobal
        );
        const typeFilterItems = createTypeFilterItems(allEntities);

        activeTopicsState = createFilterState(topicFilterItems);
        activeTypesState = createFilterState(typeFilterItems);

        const unconfiguredTopics = topicFilterItems.filter(
            item => !item.configured && item.count > 0
        );
        if (unconfiguredTopics.length) {
            console.warn(
                'POI_Topic values are present in data but missing from config symbology. ' +
                'They remain visible and filterable using the default style:',
                unconfiguredTopics.map(item => item.value)
            );
        }

        geojsonLayer = L.geoJSON(null, {
            pointToLayer: function (feature, latlng) {
                const entity = getEntityForFeature(feature);
                const topicValue = entity ? entity.topic : '';
                const setting = topicSettingsGlobal[topicValue] || defaultStyleGlobal;
                const icon = createCustomIcon(setting.shape || 'circle', setting.color || '#64748B');
                return L.marker(latlng, { icon });
            },
            style: function (feature) {
                const entity = getEntityForFeature(feature);
                const topicValue = entity ? entity.topic : '';
                const setting = topicSettingsGlobal[topicValue] || defaultStyleGlobal;
                const geometryFamily = entity ? entity.geometryFamily : 'line';
                return createVectorStyle(setting, geometryFamily);
            },
            onEachFeature: function (feature, layer) {
                const entity = getEntityForFeature(feature);
                if (entity) {
                    layer.bindPopup(buildPopupContent(entity));
                    attachPopupDetailButton(layer, entity, detailPanel, map);
                }
            }
        }).addTo(map);

        refreshMapEntities();
        setInitialExtent(map, config, geojsonLayer);
        addEntityFiltersControl(map, {
            topicItems: topicFilterItems,
            typeItems: typeFilterItems,
            activeTopicsState,
            activeTypesState,
            onChange: refreshMapEntities
        });
        addCoordinateControl(map);
        attachSearchHandler(map, geojsonLayer, getEntityForFeature);
        attachOverlayHandlers(map);
    })
    .catch(error => {
        console.error('Error loading application data:', error);
        document.getElementById('poiCount').textContent = 'Load error';
    });
