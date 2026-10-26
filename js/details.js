import { focusMapOnLayer } from './map.js';

const IMAGE_EXTENSIONS = /\.(jpe?g|png|gif|webp|bmp|tiff?)$/i;
const AUDIO_EXTENSIONS = /\.(mp3|wav|m4a|aac|ogg|oga|flac|opus|wma|aiff?|amr|m4b)$/i;
const VIDEO_EXTENSIONS = /\.(mp4|mov|m4v|webm|avi|mkv)$/i;

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

function attachmentPathWithoutQuery(path) {
    return String(path || '').split('?')[0];
}

function attachmentFileName(path, index) {
    const cleanPath = attachmentPathWithoutQuery(path).replace(/\\/g, '/');
    const lastPart = cleanPath.split('/').filter(Boolean).pop();
    if (!lastPart || /^\d+$/.test(lastPart)) return `Attachment ${index + 1}`;
    try {
        return decodeURIComponent(lastPart);
    } catch {
        return lastPart;
    }
}

function getAttachmentKind(path) {
    const cleanPath = attachmentPathWithoutQuery(path);
    if (IMAGE_EXTENSIONS.test(cleanPath)) return 'image';
    if (AUDIO_EXTENSIONS.test(cleanPath)) return 'audio';
    if (VIDEO_EXTENSIONS.test(cleanPath)) return 'video';
    return 'other';
}

function renderMediaLink(item, label) {
    const safeUrl = escapeHtml(item.url);
    const safeName = escapeHtml(item.name || 'Attachment');
    return `
        <a class="entity-detail-attachment-link" href="${safeUrl}" target="_blank" rel="noopener noreferrer">
            ${escapeHtml(label)} — ${safeName}
        </a>
    `;
}

function renderAttachments(entity) {
    const media = Array.isArray(entity.attachmentMedia) ? entity.attachmentMedia : [];
    if (!media.length) return '';

    const images = media.filter(item => item.kind === 'image');
    const audio = media.filter(item => item.kind === 'audio');
    const other = media.filter(item => item.kind !== 'image' && item.kind !== 'audio');

    const sections = [];

    if (images.length) {
        const items = images.map((item, index) => {
            const safeUrl = escapeHtml(item.url);
            const safeName = escapeHtml(item.name || `Image ${index + 1}`);
            return `
                <a class="entity-detail-media-item" href="${safeUrl}" target="_blank" rel="noopener noreferrer">
                    <img src="${safeUrl}" alt="${escapeHtml(getEntityDisplayName(entity))} - image ${index + 1}" loading="lazy">
                    <span>${safeName}</span>
                </a>
            `;
        }).join('');
        sections.push(`
            <section class="entity-detail-section entity-detail-media-section">
                <h3>Photos <span class="entity-detail-section-count">${images.length}</span></h3>
                <div class="entity-detail-media-grid">${items}</div>
            </section>
        `);
    }

    if (audio.length) {
        const items = audio.map(item => {
            const safeUrl = escapeHtml(item.url);
            const safeName = escapeHtml(item.name || 'Audio');
            const safeType = escapeHtml(item.contentType || '');
            return `
                <div class="entity-detail-audio-item">
                    <div class="entity-detail-attachment-name">${safeName}</div>
                    <audio controls preload="none">
                        <source src="${safeUrl}"${safeType ? ` type="${safeType}"` : ''}>
                        Your browser does not support audio playback.
                    </audio>
                    ${renderMediaLink(item, 'Open audio file')}
                </div>
            `;
        }).join('');
        sections.push(`
            <section class="entity-detail-section entity-detail-media-section">
                <h3>Audio <span class="entity-detail-section-count">${audio.length}</span></h3>
                <div class="entity-detail-audio-list">${items}</div>
            </section>
        `);
    }

    if (other.length) {
        const items = other.map(item => {
            const label = item.kind === 'video' ? 'Open video' : 'Open attachment';
            const kindLabel = item.kind === 'video' ? 'Video' : 'Attachment';
            return `
                <div class="entity-detail-other-item">
                    <span class="entity-detail-media-kind">${escapeHtml(kindLabel)}</span>
                    ${renderMediaLink(item, label)}
                </div>
            `;
        }).join('');
        sections.push(`
            <section class="entity-detail-section entity-detail-media-section">
                <h3>Other Attachments <span class="entity-detail-section-count">${other.length}</span></h3>
                <div class="entity-detail-other-list">${items}</div>
            </section>
        `);
    }

    return sections.join('');
}

function formatBounds(bounds) {
    if (!bounds) return '';
    const values = [bounds.west, bounds.south, bounds.east, bounds.north];
    if (!values.every(Number.isFinite)) return '';

    return `W ${bounds.west.toFixed(5)}, S ${bounds.south.toFixed(5)}, E ${bounds.east.toFixed(5)}, N ${bounds.north.toFixed(5)}`;
}

function geometryDisplayLabel(entity) {
    if (!entity) return 'Entity';
    if (entity.geometryFamily === 'point') return 'Point';
    if (entity.geometryFamily === 'line') return 'Line';
    if (entity.geometryFamily === 'polygon') return 'Polygon';
    return entity.geometryType || 'Entity';
}

export function getEntityDisplayName(entity) {
    if (entity && entity.name) return entity.name;
    return `Unnamed ${geometryDisplayLabel(entity)}`;
}

function renderEnrichment(entity) {
    const e = entity.enrichment;
    if (!e) return '';
    const a = e.administrative || {};
    const p = e.provenance || {};
    const region = a.state || a.county || '';
    const fields = [
        renderField('Country', a.country),
        renderField('Region', region),
        renderField('Locality', a.locality),
        renderField('Address', a.display_address),
        renderField('Enrichment Status', p.enrichment_status),
        renderField('Last Enriched', p.enriched_at)
    ].join('');
    return `<section class="entity-detail-section entity-detail-enrichment">
        <h3>External Geographic Information</h3>
        <div class="entity-detail-fields">${fields}</div>
        <h3>Enrichment Notes</h3>
        <div class="entity-detail-description">${formatMultiline(p.enrichment_notes || 'No external enrichment completed.')}</div>
        ${(p.enrichment_sources || []).length ? '<div class="entity-detail-source">© OpenStreetMap contributors · ODbL 1.0 · Nominatim</div>' : ''}
    </section>`;
}

export function buildEntityDetailContent(entity) {
    if (!entity) return '<div class="entity-detail-empty">No entity selected.</div>';

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
        renderField('POI Type', entity.type || 'Unspecified'),
        renderField('Research Topic', entity.topic || 'Unspecified')
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
        renderField('Geometry', geometryDisplayLabel(entity))
    ].join('');

    const technicalFields = [
        renderField('Stable Entity ID', entity.entityId || 'Not available', 'entity-detail-field-monospace'),
        renderField('ArcGIS OBJECTID', objectId, 'entity-detail-field-monospace'),
        renderField('Source Dataset', entity.sourceDataset || 'unknown', 'entity-detail-field-monospace'),
        renderField('GeoJSON Geometry', entity.geometryType || 'Unknown', 'entity-detail-field-monospace')
    ].join('');

    return `
        <div class="entity-detail-badges">
            <span class="entity-detail-badge entity-detail-badge-geometry">${escapeHtml(geometryDisplayLabel(entity))}</span>
            <span class="entity-detail-badge entity-detail-badge-secondary">${escapeHtml(entity.type || 'Unspecified')}</span>
            ${entity.topic ? `<span class="entity-detail-badge">${escapeHtml(entity.topic)}</span>` : ''}
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

        ${renderEnrichment(entity)}

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
        title.textContent = getEntityDisplayName(entity);
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
