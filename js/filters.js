function normalizeDimensionValue(value) {
    return value == null ? '' : String(value).trim();
}

function getDimensionValues(entities, propertyName) {
    const counts = new Map();

    for (const entity of entities) {
        const value = normalizeDimensionValue(entity ? entity[propertyName] : '');
        if (!value) continue;
        counts.set(value, (counts.get(value) || 0) + 1);
    }

    return counts;
}

function generalFirstSort(a, b, generalValue) {
    if (a === generalValue) return -1;
    if (b === generalValue) return 1;
    return a.localeCompare(b);
}

/**
 * Research Topic remains part of the Entity model for detail/research use.
 * It is intentionally not rendered in the v1.4 primary map legend.
 */
export function createTopicFilterItems(entities) {
    const observedCounts = getDimensionValues(entities, 'topic');

    return [...observedCounts.keys()]
        .sort((a, b) => generalFirstSort(a, b, 'General'))
        .map(value => ({
            value,
            label: value,
            count: observedCounts.get(value) || 0,
            visibleByDefault: true
        }));
}

/**
 * Build the primary POI Type legend from configuration plus values observed
 * across every loaded Entity dataset. Configured Types retain explicit order
 * and presentation; new ArcGIS values are appended with the default style.
 */
export function createTypeFilterItems(entities, typeSettings = {}, defaultStyle = {}) {
    const observedCounts = getDimensionValues(entities, 'type');
    const configuredKeys = Object.keys(typeSettings);
    const configuredSet = new Set(configuredKeys);
    const extraValues = [...observedCounts.keys()]
        .filter(value => !configuredSet.has(value))
        .sort((a, b) => generalFirstSort(a, b, 'General Site'));

    return [...configuredKeys, ...extraValues].map(value => {
        const configured = Object.prototype.hasOwnProperty.call(typeSettings, value);
        const setting = configured ? typeSettings[value] : defaultStyle;
        const pointSetting = setting.point || defaultStyle.point || {};

        return {
            value,
            label: configured && typeSettings[value].label
                ? typeSettings[value].label
                : value,
            count: observedCounts.get(value) || 0,
            configured,
            visibleByDefault: configured ? typeSettings[value].visible !== false : true,
            shape: pointSetting.shape || 'circle',
            radius: pointSetting.radius ?? 7,
            color: setting.color || defaultStyle.color || '#64748B'
        };
    });
}

/**
 * Geometry is a separate visibility dimension from POI Type. The control is
 * deliberately fixed to the three supported geometry families so Lines and
 * Polygons appear in the UI before their AGOL export is activated.
 */
export function createGeometryFilterItems(entities) {
    const counts = { point: 0, line: 0, polygon: 0 };
    for (const entity of entities || []) {
        if (Object.prototype.hasOwnProperty.call(counts, entity.geometryFamily)) {
            counts[entity.geometryFamily] += 1;
        }
    }

    return [
        { value: 'point', label: 'Points', count: counts.point, visibleByDefault: true },
        { value: 'line', label: 'Lines', count: counts.line, visibleByDefault: true },
        { value: 'polygon', label: 'Polygons', count: counts.polygon, visibleByDefault: true }
    ];
}

export function createFilterState(items) {
    const state = {};
    items.forEach(item => {
        state[item.value] = item.visibleByDefault !== false;
    });
    return state;
}

// Retained for compatibility with existing tests/utilities.
export function createTopicState(topicSettings) {
    if (Array.isArray(topicSettings)) return createFilterState(topicSettings);

    return createFilterState(
        Object.keys(topicSettings || {}).map(value => ({
            value,
            visibleByDefault: topicSettings[value].visible !== false
        }))
    );
}

/** Primary v1.4 map filter: POI Type AND Geometry family. */
export function filterEntitiesByTypeAndGeometry(entities, activeTypesState, activeGeometryState) {
    return entities.filter(entity => {
        const typeVisible = activeTypesState[entity.type] !== false;
        const geometryVisible = activeGeometryState[entity.geometryFamily] !== false;
        return typeVisible && geometryVisible;
    });
}

// Compatibility helpers retained while v1.4 is under development.
export function filterEntitiesByDimensions(entities, activeTopicsState, activeTypesState) {
    return entities.filter(entity => {
        const topicVisible = activeTopicsState[entity.topic] !== false;
        const typeVisible = activeTypesState[entity.type] !== false;
        return topicVisible && typeVisible;
    });
}

export function filterEntitiesByTopic(entities, activeTopicsState) {
    return entities.filter(entity => activeTopicsState[entity.topic] !== false);
}

export function filterFeaturesByTopic(features, activeTopicsState) {
    return features.filter(feature => {
        const topicValue = feature.properties ? feature.properties.POI_Topic : null;
        return activeTopicsState[topicValue] !== false;
    });
}

function setAllStates(items, state, visible) {
    items.forEach(item => {
        state[item.value] = visible;
    });
}

function updateToggleItemState(element, isVisible) {
    element.classList.toggle('disabled', !isVisible);
    element.setAttribute('aria-checked', isVisible ? 'true' : 'false');
}

function createAllNoneActions(container, items, state, itemElements, onChange) {
    const actions = L.DomUtil.create('div', 'filter-actions', container);

    const showAllButton = L.DomUtil.create('button', 'filter-action-button', actions);
    showAllButton.type = 'button';
    showAllButton.textContent = 'All';

    const hideAllButton = L.DomUtil.create('button', 'filter-action-button', actions);
    hideAllButton.type = 'button';
    hideAllButton.textContent = 'None';

    const applyState = visible => {
        setAllStates(items, state, visible);
        itemElements.forEach((element, value) => {
            updateToggleItemState(element, state[value] !== false);
        });
        onChange();
    };

    L.DomEvent.on(showAllButton, 'click', event => {
        L.DomEvent.stop(event);
        applyState(true);
    });

    L.DomEvent.on(hideAllButton, 'click', event => {
        L.DomEvent.stop(event);
        applyState(false);
    });
}

function createToggleList(container, options) {
    const {
        items,
        state,
        onChange,
        renderIcon,
        includeAllNone = false
    } = options;

    const itemElements = new Map();
    if (includeAllNone) {
        createAllNoneActions(container, items, state, itemElements, onChange);
    }

    const itemsContainer = L.DomUtil.create('div', 'control-toggle-items', container);

    items.forEach(item => {
        const isVisible = state[item.value] !== false;
        const itemElement = L.DomUtil.create(
            'div',
            `control-toggle-item ${isVisible ? '' : 'disabled'}`,
            itemsContainer
        );

        itemElement.dataset.value = item.value;
        itemElement.setAttribute('role', 'checkbox');
        itemElement.setAttribute('tabindex', '0');
        updateToggleItemState(itemElement, isVisible);

        const iconContainer = L.DomUtil.create('span', 'control-toggle-icon', itemElement);
        iconContainer.innerHTML = renderIcon(item);

        const labelElement = L.DomUtil.create('span', 'control-toggle-label', itemElement);
        labelElement.textContent = item.label;

        const countElement = L.DomUtil.create('span', 'control-toggle-count', itemElement);
        countElement.textContent = String(item.count);

        const toggleItem = () => {
            const value = itemElement.dataset.value;
            state[value] = !state[value];
            updateToggleItemState(itemElement, state[value] !== false);
            onChange();
        };

        L.DomEvent.on(itemElement, 'click', event => {
            L.DomEvent.stop(event);
            toggleItem();
        });

        L.DomEvent.on(itemElement, 'keydown', event => {
            if (event.key === 'Enter' || event.key === ' ') {
                L.DomEvent.stop(event);
                toggleItem();
            }
        });

        itemElements.set(item.value, itemElement);
    });

    return itemElements;
}

function geometryIcon(value) {
    if (value === 'line') {
        return '<span class="geometry-icon geometry-icon-line" aria-hidden="true"></span>';
    }
    if (value === 'polygon') {
        return '<span class="geometry-icon geometry-icon-polygon" aria-hidden="true"></span>';
    }
    return '<span class="geometry-icon geometry-icon-point" aria-hidden="true"></span>';
}

function createSection(parent, title) {
    const section = L.DomUtil.create('section', 'map-control-section', parent);
    const heading = L.DomUtil.create('h3', 'map-control-section-title', section);
    heading.textContent = title;
    return section;
}

/**
 * v1.4 integrated map control panel.
 * Order is intentionally: POI Types → Search → Geometry → Map Utilities.
 * Research Topic stays out of the primary legend and remains Entity metadata.
 */
export function addMapControlPanel(map, options) {
    const {
        typeItems,
        geometryItems,
        activeTypesState,
        activeGeometryState,
        onChange
    } = options;

    const control = L.control({ position: 'topleft' });

    control.onAdd = function () {
        const panel = L.DomUtil.create('div', 'map-ui-panel');

        const header = L.DomUtil.create('div', 'map-ui-panel-header', panel);
        const panelTitle = L.DomUtil.create('div', 'map-ui-panel-title', header);
        panelTitle.textContent = 'Map Controls';

        const collapseButton = L.DomUtil.create('button', 'map-ui-panel-collapse', header);
        collapseButton.type = 'button';
        collapseButton.textContent = '−';
        collapseButton.setAttribute('aria-label', 'Toggle map controls');
        collapseButton.setAttribute('aria-expanded', 'true');

        const body = L.DomUtil.create('div', 'map-ui-panel-body', panel);

        const typeSection = createSection(body, 'POI Types');
        createToggleList(typeSection, {
            items: typeItems,
            state: activeTypesState,
            onChange,
            includeAllNone: true,
            renderIcon: item => `<span class="type-color-swatch" style="--type-color:${item.color}" aria-hidden="true"></span>`
        });

        const searchSection = createSection(body, 'Search');
        const searchInput = L.DomUtil.create('input', 'map-search-input', searchSection);
        searchInput.type = 'search';
        searchInput.id = 'poiSearchInput';
        searchInput.placeholder = 'Search POI by name...';
        searchInput.setAttribute('aria-label', 'Search POI by name');
        searchInput.autocomplete = 'off';

        const geometrySection = createSection(body, 'Geometry');
        createToggleList(geometrySection, {
            items: geometryItems,
            state: activeGeometryState,
            onChange,
            renderIcon: item => geometryIcon(item.value)
        });

        const utilitySection = createSection(body, 'Map Utilities');
        const buttons = L.DomUtil.create('div', 'map-utility-buttons', utilitySection);

        const dayNightButton = L.DomUtil.create('button', 'btn-control', buttons);
        dayNightButton.type = 'button';
        dayNightButton.id = 'btnDayNight';
        dayNightButton.textContent = 'Day/Night';

        const timezonesButton = L.DomUtil.create('button', 'btn-control', buttons);
        timezonesButton.type = 'button';
        timezonesButton.id = 'btnTimezones';
        timezonesButton.textContent = 'Time Zones';

        const coords = L.DomUtil.create('div', 'coords-display', utilitySection);
        coords.id = 'coordsDisplay';
        coords.textContent = 'Lat: -- | Lon: --';

        const setCollapsed = collapsed => {
            panel.classList.toggle('collapsed', collapsed);
            collapseButton.textContent = collapsed ? '+' : '−';
            collapseButton.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
        };

        L.DomEvent.on(collapseButton, 'click', event => {
            L.DomEvent.stop(event);
            setCollapsed(!panel.classList.contains('collapsed'));
        });

        if (window.matchMedia && window.matchMedia('(max-width: 700px)').matches) {
            setCollapsed(true);
        }

        L.DomEvent.disableClickPropagation(panel);
        if (L.DomEvent.disableScrollPropagation) {
            L.DomEvent.disableScrollPropagation(panel);
        }

        return panel;
    };

    control.addTo(map);
    return control;
}
