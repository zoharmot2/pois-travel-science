import { focusMapOnLayer } from './map.js';

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function formatMultiline(value) {
    return escapeHtml(value).replace(/\r?\n/g, '<br>');
}

function getProperty(entity, ...names) {
    const properties = entity && entity.properties ? entity.properties : {};
    for (const name of names) {
        if (Object.prototype.hasOwnProperty.call(properties, name) && properties[name] != null && properties[name] !== '') {
            return properties[name];
        }
    }
    return '';
}

function renderField(label, value, className = '') {
    if (value == null || value === '') return '';
    return `
        <div class="entity-detail-field ${className}">
            <div class="entity-detail-label">${escapeHtml(label)}</div>
            <div class="entity-detail-value">${escapeHtml(value)}</div>
        </div>
    `;
}

function isLikelyImageAttachment(path) {
    const value = String(path || '').toLowerCase().split('?')[0];
    if (/\.(jpe?g|png|gif|webp|bmp|tiff?)$/.test(value)) return true;

    // Current ArcGIS attachment URLs do not include a file extension in the URL.
    return /^https?:\/\/.*\/attachments\/\d+$/i.test(String(path || ''));
}

function renderAttachments(entity) {
    const attachments = Array.isArray(entity.attachments) ? entity.attachments : [];
    if (!attachments.length) return '';

    const items = attachments.map((path, index) => {
        const safePath = escapeHtml(path);
        const label = `Attachment ${index + 1}`;

        if (isLikelyImageAttachment(path)) {
            return `
                <a class="entity-detail-media-item" href="${safePath}" target="_blank" rel="noopener noreferrer">
                    <img src="${safePath}" alt="${escapeHtml(entity.name || 'POI')} - image ${index + 1}" loading="lazy">
                    <span>${escapeHtml(label)}</span>
                </a>
            `;
        }

        return `
            <a class="entity-detail-attachment-link" href="${safePath}" target="_blank" rel="noopener noreferrer">
                ${escapeHtml(label)}
            </a>
        `;
    }).join('');

    return `
        <section class="entity-detail-section">
            <h3>Attachments <span class="entity-detail-section-count">${attachments.length}</span></h3>
            <div class="entity-detail-media-grid">${items}</div>
        </section>
    `;
}

function formatBounds(bounds) {
    if (!bounds) return '';
    const values = [bounds.west, bounds.south, bounds.east, bounds.north];
    if (!values.every(Number.isFinite)) return '';

    return `W ${bounds.west.toFixed(5)}, S ${bounds.south.toFixed(5)}, E ${bounds.east.toFixed(5)}, N ${bounds.north.toFixed(5)}`;
}

export function buildEntityDetailContent(entity) {
    if (!entity) return '<div class="entity-detail-empty">No POI selected.</div>';

    const collectionDate = entity.collectionDate || getProperty(entity, 'Collection_date');
    const creationDate = entity.creationDate || getProperty(entity, 'CreationDate');
    const editDate = getProperty(entity, 'EditDate');
    const collectedBy = getProperty(entity, 'Collect_Name', 'collector_name');
    const objectId = entity.sourceIds && entity.sourceIds.objectId != null
        ? entity.sourceIds.objectId
        : getProperty(entity, 'OBJECTID', 'FID');

    const coordinateText = entity.latitude != null && entity.longitude != null
        ? `${Number(entity.latitude).toFixed(5)}, ${Number(entity.longitude).toFixed(5)}`
        : '';

    const representativePointText = entity.geometryType !== 'Point' && entity.representativePoint
        ? `${Number(entity.representativePoint.latitude).toFixed(5)}, ${Number(entity.representativePoint.longitude).toFixed(5)}`
        : '';

    const descriptionSection = entity.description
        ? `
            <section class="entity-detail-section">
                <h3>Description</h3>
                <div class="entity-detail-description">${formatMultiline(entity.description)}</div>
            </section>
        `
        : '';

    const classificationFields = [
        renderField('Research Topic', entity.topic || '—'),
        renderField('POI Type', entity.type || '—')
    ].join('');

    const fieldworkFields = [
        renderField('Collection Date', collectionDate),
        renderField('Collected By', collectedBy),
        renderField('Creation Date', creationDate),
        renderField('Last Edited', editDate)
    ].join('');

    const locationFields = [
        renderField('Coordinates', coordinateText),
        renderField('Map Center (derived)', representativePointText),
        renderField('Extent', entity.geometryType !== 'Point' ? formatBounds(entity.bounds) : ''),
        renderField('Geometry', entity.geometryType || entity.geometryFamily || '')
    ].join('');

    const technicalFields = [
        renderField('Stable Entity ID', entity.entityId || 'Not available', 'entity-detail-field-monospace'),
        renderField('ArcGIS OBJECTID', objectId, 'entity-detail-field-monospace'),
        renderField('Source Dataset', entity.sourceDataset || 'unknown', 'entity-detail-field-monospace')
    ].join('');

    return `
        <div class="entity-detail-badges">
            ${entity.topic ? `<span class="entity-detail-badge">${escapeHtml(entity.topic)}</span>` : ''}
            ${entity.type ? `<span class="entity-detail-badge entity-detail-badge-secondary">${escapeHtml(entity.type)}</span>` : ''}
        </div>

        ${descriptionSection}

        <section class="entity-detail-section">
            <h3>Classification</h3>
            <div class="entity-detail-fields">${classificationFields}</div>
        </section>

        ${locationFields ? `
            <section class="entity-detail-section">
                <h3>Location</h3>
                <div class="entity-detail-fields">${locationFields}</div>
            </section>
        ` : ''}

        ${fieldworkFields ? `
            <section class="entity-detail-section">
                <h3>Field Record</h3>
                <div class="entity-detail-fields">${fieldworkFields}</div>
            </section>
        ` : ''}

        ${renderAttachments(entity)}

        <details class="entity-detail-technical">
            <summary>Technical details</summary>
            <div class="entity-detail-fields">${technicalFields}</div>
        </details>
    `;
}

export function createEntityDetailPanel(options = {}) {
    const panel = document.getElementById('entityDetailPanel');
    const title = document.getElementById('entityDetailTitle');
    const content = document.getElementById('entityDetailContent');
    const closeButton = document.getElementById('entityDetailClose');

    if (!panel || !title || !content || !closeButton) {
        throw new Error('Entity detail panel markup is missing from index.html.');
    }

    let activeEntity = null;

    function notifyVisibilityChange(isOpen) {
        if (typeof options.onVisibilityChange === 'function') {
            options.onVisibilityChange(isOpen, activeEntity);
        }
    }

    function open(entity) {
        if (!entity) return;
        activeEntity = entity;
        title.textContent = entity.name || 'Unnamed POI';
        content.innerHTML = buildEntityDetailContent(entity);
        panel.classList.add('open');
        panel.setAttribute('aria-hidden', 'false');
        notifyVisibilityChange(true);
    }

    function close() {
        if (!panel.classList.contains('open')) return;
        panel.classList.remove('open');
        panel.setAttribute('aria-hidden', 'true');
        activeEntity = null;
        notifyVisibilityChange(false);
    }

    closeButton.addEventListener('click', close);
    document.addEventListener('keydown', event => {
        if (event.key === 'Escape' && panel.classList.contains('open')) {
            close();
        }
    });

    return {
        open,
        close,
        getActiveEntity: () => activeEntity,
        isOpen: () => panel.classList.contains('open')
    };
}

export function attachPopupDetailButton(layer, entity, detailPanel, map) {
    layer.on('popupopen', () => {
        const popupElement = layer.getPopup() && layer.getPopup().getElement();
        if (!popupElement) return;

        const button = popupElement.querySelector('.popup-detail-button');
        if (!button || button.dataset.bound === 'true') return;

        button.dataset.bound = 'true';
        button.addEventListener('click', event => {
            event.preventDefault();
            event.stopPropagation();
            detailPanel.open(entity);
            if (map && typeof map.closePopup === 'function') {
                map.closePopup();
            }
            window.setTimeout(() => {
                focusMapOnLayer(map, layer, entity, { maxZoom: 14, padding: [30, 30] });
            }, 20);
        });
    });
}
