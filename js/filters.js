import { createShapeSVG } from './entities.js';

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

/**
 * Build the Research Topic filter model from both configuration and data.
 *
 * Configured topics keep their configured order and symbology. Any topic that
 * appears in ArcGIS data but is not yet present in config.json is appended
 * automatically and rendered with the configured default marker style. This
 * keeps future POI_Topic additions visible and filterable instead of silently
 * dropping them.
 */
export function createTopicFilterItems(entities, topicSettings = {}, defaultStyle = {}) {
    const observedCounts = getDimensionValues(entities, 'topic');
    const configuredKeys = Object.keys(topicSettings);
    const configuredSet = new Set(configuredKeys);
    const extraValues = [...observedCounts.keys()]
        .filter(value => !configuredSet.has(value))
        .sort((a, b) => a.localeCompare(b));

    return [...configuredKeys, ...extraValues].map(value => {
        const configured = Object.prototype.hasOwnProperty.call(topicSettings, value);
        const setting = configured ? topicSettings[value] : defaultStyle;

        return {
            value,
            label: configured && topicSettings[value].label
                ? topicSettings[value].label
                : value,
            count: observedCounts.get(value) || 0,
            configured,
            visibleByDefault: configured ? topicSettings[value].visible !== false : true,
            shape: setting.shape || defaultStyle.shape || 'circle',
            color: setting.color || defaultStyle.color || '#64748B'
        };
    });
}

/**
 * Build POI Type filters entirely from values present in the current dataset.
 * No closed list is hard-coded in the website, so a future POI_Type added in
 * ArcGIS appears automatically after the next data refresh.
 */
export function createTypeFilterItems(entities) {
    const observedCounts = getDimensionValues(entities, 'type');

    return [...observedCounts.keys()]
        .sort((a, b) => {
            if (a === 'General Site') return -1;
            if (b === 'General Site') return 1;
            return a.localeCompare(b);
        })
        .map(value => ({
            value,
            label: value,
            count: observedCounts.get(value) || 0,
            visibleByDefault: true
        }));
}

export function createFilterState(items) {
    const state = {};
    items.forEach(item => {
        state[item.value] = item.visibleByDefault !== false;
    });
    return state;
}

// Backward-compatible helper retained for tests and any older callers.
export function createTopicState(topicSettings) {
    if (Array.isArray(topicSettings)) return createFilterState(topicSettings);

    return createFilterState(
        Object.keys(topicSettings || {}).map(value => ({
            value,
            visibleByDefault: topicSettings[value].visible !== false
        }))
    );
}

export function filterEntitiesByDimensions(entities, activeTopicsState, activeTypesState) {
    return entities.filter(entity => {
        const topicVisible = activeTopicsState[entity.topic] !== false;
        const typeVisible = activeTypesState[entity.type] !== false;
        return topicVisible && typeVisible;
    });
}

// Backward-compatible Topic-only helper.
export function filterEntitiesByTopic(entities, activeTopicsState) {
    return entities.filter(entity => activeTopicsState[entity.topic] !== false);
}

// Compatibility helper for callers/tests that still operate on raw GeoJSON features.
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

function updateFilterItemState(element, isVisible) {
    element.classList.toggle('disabled', !isVisible);
    element.setAttribute('aria-checked', isVisible ? 'true' : 'false');
}

function createSectionActions(container, items, state, itemElements, onChange) {
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
            updateFilterItemState(element, state[value] !== false);
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

function addFilterSection(parent, options) {
    const {
        title,
        items,
        state,
        onChange,
        renderIcon,
        open = true
    } = options;

    const section = L.DomUtil.create('details', 'filter-section', parent);
    section.open = open;

    const summary = L.DomUtil.create('summary', 'filter-section-summary', section);
    summary.textContent = title;

    const sectionBody = L.DomUtil.create('div', 'filter-section-body', section);
    const itemElements = new Map();
    createSectionActions(sectionBody, items, state, itemElements, onChange);

    const itemsContainer = L.DomUtil.create('div', 'filter-items', sectionBody);

    items.forEach(item => {
        const isVisible = state[item.value] !== false;
        const itemElement = L.DomUtil.create(
            'div',
            `filter-item ${isVisible ? '' : 'disabled'}`,
            itemsContainer
        );

        itemElement.dataset.value = item.value;
        itemElement.setAttribute('role', 'checkbox');
        itemElement.setAttribute('tabindex', '0');
        updateFilterItemState(itemElement, isVisible);

        const iconContainer = L.DomUtil.create('span', 'filter-icon-container', itemElement);
        iconContainer.innerHTML = renderIcon(item);

        const labelElement = L.DomUtil.create('span', 'filter-label', itemElement);
        labelElement.textContent = item.label;

        const countElement = L.DomUtil.create('span', 'filter-count', itemElement);
        countElement.textContent = String(item.count);

        const toggleItem = () => {
            const value = itemElement.dataset.value;
            state[value] = !state[value];
            updateFilterItemState(itemElement, state[value] !== false);
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

    return section;
}

/**
 * Add the combined, independent Research Topic + POI Type filter control.
 * Within each dimension, selected values are OR'ed. The two dimensions combine
 * with AND logic in filterEntitiesByDimensions().
 */
export function addEntityFiltersControl(map, options) {
    const {
        topicItems,
        typeItems,
        activeTopicsState,
        activeTypesState,
        onChange
    } = options;

    const control = L.control({ position: 'topleft' });

    control.onAdd = function () {
        const div = L.DomUtil.create('div', 'map-filter-panel');
        const title = L.DomUtil.create('h4', 'filter-panel-title', div);
        title.textContent = 'Filters';

        addFilterSection(div, {
            title: 'Research Topics',
            items: topicItems,
            state: activeTopicsState,
            onChange,
            open: true,
            renderIcon: item => createShapeSVG(item.shape, item.color, 18)
        });

        addFilterSection(div, {
            title: 'POI Types',
            items: typeItems,
            state: activeTypesState,
            onChange,
            open: true,
            renderIcon: () => '<span class="type-filter-symbol">✓</span>'
        });

        L.DomEvent.disableClickPropagation(div);
        if (L.DomEvent.disableScrollPropagation) {
            L.DomEvent.disableScrollPropagation(div);
        }
        return div;
    };

    control.addTo(map);
    return control;
}
