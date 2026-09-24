const POINT_GEOMETRY_TYPES = new Set(['Point', 'MultiPoint']);
const LINE_GEOMETRY_TYPES = new Set(['LineString', 'MultiLineString']);
const POLYGON_GEOMETRY_TYPES = new Set(['Polygon', 'MultiPolygon']);
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

const IMAGE_ATTACHMENT_PATTERN = /\.(jpe?g|png|gif|webp|bmp|tiff?)$/i;
const AUDIO_ATTACHMENT_PATTERN = /\.(mp3|wav|m4a|aac|ogg|oga|flac|opus|wma|aiff?|amr|m4b)$/i;
const VIDEO_ATTACHMENT_PATTERN = /\.(mp4|mov|m4v|webm|avi|mkv)$/i;
const MEDIA_KINDS = new Set(['image', 'audio', 'video', 'other']);
const MEDIA_STORAGE = new Set(['local', 'remote']);


function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function getProperty(properties, ...names) {
    if (!properties) return null;

    for (const name of names) {
        if (Object.prototype.hasOwnProperty.call(properties, name) && properties[name] != null) {
            return properties[name];
        }
    }

    const lowerCaseKeys = new Map(
        Object.keys(properties).map(key => [key.toLowerCase(), key])
    );

    for (const name of names) {
        const matchingKey = lowerCaseKeys.get(name.toLowerCase());
        if (matchingKey && properties[matchingKey] != null) {
            return properties[matchingKey];
        }
    }

    return null;
}

function toFiniteNumber(value) {
    const number = Number(value);
    return Number.isFinite(number) ? number : null;
}

function collectCoordinatePairs(value, output) {
    if (!Array.isArray(value)) return;

    if (value.length >= 2) {
        const longitude = toFiniteNumber(value[0]);
        const latitude = toFiniteNumber(value[1]);
        if (longitude !== null && latitude !== null) {
            output.push([longitude, latitude]);
            return;
        }
    }

    value.forEach(item => collectCoordinatePairs(item, output));
}

export function getGeometryFamily(geometryType) {
    if (POINT_GEOMETRY_TYPES.has(geometryType)) return 'point';
    if (LINE_GEOMETRY_TYPES.has(geometryType)) return 'line';
    if (POLYGON_GEOMETRY_TYPES.has(geometryType)) return 'polygon';
    return 'unknown';
}

/**
 * Return a geometry-independent geographic extent.
 *
 * The returned object deliberately does not use Leaflet classes so the Entity
 * model remains independent from the rendering library.
 */
export function getGeometryBounds(geometry) {
    if (!geometry || !Array.isArray(geometry.coordinates)) return null;

    const pairs = [];
    collectCoordinatePairs(geometry.coordinates, pairs);
    if (!pairs.length) return null;

    let west = pairs[0][0];
    let east = pairs[0][0];
    let south = pairs[0][1];
    let north = pairs[0][1];

    for (const [longitude, latitude] of pairs.slice(1)) {
        west = Math.min(west, longitude);
        east = Math.max(east, longitude);
        south = Math.min(south, latitude);
        north = Math.max(north, latitude);
    }

    return { west, south, east, north };
}

/**
 * Provide one geometry-independent location for navigation and summaries.
 *
 * For a Point this is the point itself. For multi-part, line, and polygon
 * geometries this is the center of the geometry bounding box. It is a map
 * navigation helper, not a scientific centroid and must not be treated as a
 * derived research measurement.
 */
export function getGeometryRepresentativePoint(geometry, bounds = null) {
    if (!geometry) return null;

    if (geometry.type === 'Point' && Array.isArray(geometry.coordinates)) {
        const longitude = toFiniteNumber(geometry.coordinates[0]);
        const latitude = toFiniteNumber(geometry.coordinates[1]);
        if (longitude !== null && latitude !== null) {
            return { latitude, longitude, method: 'point' };
        }
    }

    const geometryBounds = bounds || getGeometryBounds(geometry);
    if (!geometryBounds) return null;

    return {
        latitude: (geometryBounds.south + geometryBounds.north) / 2,
        longitude: (geometryBounds.west + geometryBounds.east) / 2,
        method: 'bounds-center'
    };
}

export function normalizeAttachments(value) {
    if (!value) return [];
    if (Array.isArray(value)) return value.filter(Boolean);

    return String(value)
        .split(',')
        .map(item => item.trim())
        .filter(Boolean);
}

export function inferAttachmentKind(url = '', contentType = '') {
    const cleanUrl = String(url || '').split('?')[0];
    const mime = String(contentType || '').toLowerCase();
    if (mime.startsWith('image/') || IMAGE_ATTACHMENT_PATTERN.test(cleanUrl)) return 'image';
    if (mime.startsWith('audio/') || AUDIO_ATTACHMENT_PATTERN.test(cleanUrl)) return 'audio';
    if (mime.startsWith('video/') || VIDEO_ATTACHMENT_PATTERN.test(cleanUrl)) return 'video';
    return 'other';
}

function attachmentDisplayName(url, index) {
    const cleanUrl = String(url || '').split('?')[0].replace(/\\/g, '/');
    const lastPart = cleanUrl.split('/').filter(Boolean).pop();
    if (!lastPart || /^\d+$/.test(lastPart)) return `Attachment ${index + 1}`;
    try {
        return decodeURIComponent(lastPart);
    } catch {
        return lastPart;
    }
}

export function normalizeAttachmentMedia(value, attachments = []) {
    const attachmentUrls = normalizeAttachments(attachments);
    if (!Array.isArray(value)) {
        return attachmentUrls.map((url, index) => ({
            url,
            name: attachmentDisplayName(url, index),
            contentType: '',
            kind: inferAttachmentKind(url),
            storage: /^https?:\/\//i.test(url) ? 'remote' : 'local',
            attachmentId: null,
            parentObjectId: null,
            sourceDataset: null
        }));
    }

    const normalized = [];
    value.forEach((item, index) => {
        if (!item || typeof item !== 'object') return;
        const url = String(item.url || '').trim();
        if (!url) return;
        const kind = MEDIA_KINDS.has(item.kind) ? item.kind : inferAttachmentKind(url, item.contentType);
        const storage = MEDIA_STORAGE.has(item.storage)
            ? item.storage
            : (/^https?:\/\//i.test(url) ? 'remote' : 'local');
        normalized.push({
            url,
            name: String(item.name || attachmentDisplayName(url, index)),
            contentType: String(item.contentType || ''),
            kind,
            storage,
            attachmentId: item.attachmentId ?? null,
            parentObjectId: item.parentObjectId ?? null,
            sourceDataset: item.sourceDataset || null
        });
    });

    // Preserve backward compatibility if metadata is partial or absent.
    const knownUrls = new Set(normalized.map(item => item.url));
    attachmentUrls.forEach((url, index) => {
        if (knownUrls.has(url)) return;
        normalized.push({
            url,
            name: attachmentDisplayName(url, index),
            contentType: '',
            kind: inferAttachmentKind(url),
            storage: /^https?:\/\//i.test(url) ? 'remote' : 'local',
            attachmentId: null,
            parentObjectId: null,
            sourceDataset: null
        });
    });

    return normalized;
}

/**
 * Normalize an ArcGIS GlobalID into the website's canonical stable-ID form.
 *
 * ArcGIS may expose GlobalIDs with or without braces and with mixed casing.
 * The website stores them as lowercase RFC-style UUID strings without braces.
 * Invalid or missing values return null rather than falling back to OBJECTID,
 * because OBJECTID is not a stable cross-refresh identity.
 */
export function normalizeGlobalId(value) {
    if (value == null) return null;

    const normalized = String(value)
        .trim()
        .replace(/^\{/, '')
        .replace(/\}$/, '')
        .toLowerCase();

    return UUID_PATTERN.test(normalized) ? normalized : null;
}

export function getStableEntityId(properties) {
    return normalizeGlobalId(getProperty(properties, 'GlobalID'));
}

function getPointCoordinates(feature, properties, geometryFamily) {
    if (geometryFamily !== 'point') {
        return { latitude: null, longitude: null };
    }

    const geometry = feature && feature.geometry;
    if (geometry && geometry.type === 'Point' && Array.isArray(geometry.coordinates)) {
        const longitude = toFiniteNumber(geometry.coordinates[0]);
        const latitude = toFiniteNumber(geometry.coordinates[1]);
        if (longitude !== null && latitude !== null) {
            return { latitude, longitude };
        }
    }

    return {
        latitude: toFiniteNumber(getProperty(properties, 'Latitude')),
        longitude: toFiniteNumber(getProperty(properties, 'Longitude'))
    };
}

/**
 * Normalize one source GeoJSON Feature into the website's generic Entity model.
 *
 * `entityId` is the canonical website identity. It is derived only from the
 * ArcGIS GlobalID and normalized to lowercase UUID form. OBJECTID and GeoJSON
 * feature.id remain source identifiers and must not be used as stable identity.
 *
 * Stage 8 keeps the currently published point workflow unchanged while making
 * the Entity contract and map-navigation helpers safe for future line and
 * polygon datasets.
 */
export function createEntity(feature, options = {}) {
    const safeFeature = feature && feature.type === 'Feature'
        ? feature
        : { type: 'Feature', properties: {}, geometry: null };
    const properties = safeFeature.properties || {};
    const geometry = safeFeature.geometry || null;
    const geometryType = geometry && geometry.type ? geometry.type : 'Unknown';
    const geometryFamily = getGeometryFamily(geometryType);
    const bounds = getGeometryBounds(geometry);
    const representativePoint = getGeometryRepresentativePoint(geometry, bounds);
    const { latitude, longitude } = getPointCoordinates(safeFeature, properties, geometryFamily);
    const rawGlobalId = getProperty(properties, 'GlobalID');
    const entityId = normalizeGlobalId(rawGlobalId);

    return {
        entityId,
        entityIdSource: entityId ? 'GlobalID' : null,
        sourceDataset: options.sourceDataset || 'unknown',
        feature: safeFeature,
        properties,
        geometry,
        geometryType,
        geometryFamily,
        bounds,
        representativePoint,
        sourceIds: {
            featureId: safeFeature.id ?? null,
            objectId: getProperty(properties, 'OBJECTID', 'FID'),
            globalId: rawGlobalId,
            normalizedGlobalId: entityId
        },
        name: getProperty(properties, 'POI_Name', 'Name') || '',
        topic: getProperty(properties, 'POI_Topic', 'Topic') || '',
        type: getProperty(properties, 'POI_Type', 'Type') || '',
        description: getProperty(properties, 'POI_Description', 'Description') || '',
        creationDate: getProperty(properties, 'CreationDate') || '',
        collectionDate: getProperty(properties, 'Collection_date') || '',
        latitude,
        longitude,
        attachments: normalizeAttachments(getProperty(properties, 'attachments')),
        attachmentMedia: normalizeAttachmentMedia(
            getProperty(properties, 'attachment_media'),
            getProperty(properties, 'attachments')
        )
    };
}

export function createEntitiesFromFeatureCollection(geojsonData, options = {}) {
    const features = geojsonData && Array.isArray(geojsonData.features)
        ? geojsonData.features
        : [];

    return features.map(feature => createEntity(feature, options));
}

/**
 * Combine multiple independently exported GeoJSON datasets into one Entity list.
 * This is intentionally generic so future point/line/polygon exports can be
 * added without changing filters, search, detail panels, or stable-ID logic.
 */
export function createEntitiesFromSources(sources) {
    if (!Array.isArray(sources)) return [];

    return sources.flatMap(source => createEntitiesFromFeatureCollection(
        source && source.geojsonData,
        { sourceDataset: source && source.sourceDataset ? source.sourceDataset : 'unknown' }
    ));
}

export function summarizeGeometryFamilies(entities) {
    const summary = { point: 0, line: 0, polygon: 0, unknown: 0 };

    for (const entity of entities || []) {
        const family = entity && Object.prototype.hasOwnProperty.call(summary, entity.geometryFamily)
            ? entity.geometryFamily
            : 'unknown';
        summary[family] += 1;
    }

    return summary;
}

export function entitiesToFeatureCollection(entities) {
    return {
        type: 'FeatureCollection',
        features: entities.map(entity => entity.feature)
    };
}

export function createEntityFeatureIndex(entities) {
    const index = new WeakMap();
    entities.forEach(entity => {
        if (entity && entity.feature && typeof entity.feature === 'object') {
            index.set(entity.feature, entity);
        }
    });
    return index;
}

/**
 * Build a stable-ID lookup and validate the canonical Entity identity contract.
 * Missing IDs are reported but do not throw here; the formal QA pipeline added
 * later in v1.3 will decide publication policy. Duplicate stable IDs are always
 * an error because they make entity references ambiguous.
 */
export function createEntityIdIndex(entities) {
    const index = new Map();
    const missing = [];

    entities.forEach((entity, position) => {
        if (!entity || !entity.entityId) {
            missing.push({ entity, position });
            return;
        }

        if (index.has(entity.entityId)) {
            throw new Error(`Duplicate stable entity ID: ${entity.entityId}`);
        }

        index.set(entity.entityId, entity);
    });

    return { index, missing };
}

export function createShapeSVG(shape, color, size = 20) {
    const stroke = '#FFFFFF';
    const strokeWidth = 2;
    let svgContent = '';

    switch (shape) {
        case 'square':
            svgContent = `<rect x="3" y="3" width="14" height="14" fill="${color}" stroke="${stroke}" stroke-width="${strokeWidth}" rx="2" />`;
            break;
        case 'triangle':
            svgContent = `<polygon points="10,2 18,17 2,17" fill="${color}" stroke="${stroke}" stroke-width="${strokeWidth}" />`;
            break;
        case 'diamond':
            svgContent = `<polygon points="10,2 18,10 10,18 2,10" fill="${color}" stroke="${stroke}" stroke-width="${strokeWidth}" />`;
            break;
        case 'circle':
        default:
            svgContent = `<circle cx="10" cy="10" r="7" fill="${color}" stroke="${stroke}" stroke-width="${strokeWidth}" />`;
            break;
    }

    return `<svg width="${size}" height="${size}" viewBox="0 0 20 20">${svgContent}</svg>`;
}

export function createCustomIcon(shape, color, radius = 7) {
    const safeRadius = Number.isFinite(Number(radius)) ? Number(radius) : 7;
    const size = Math.max(16, Math.round(safeRadius * 2 + 6));
    const anchor = size / 2;

    return L.divIcon({
        className: 'custom-svg-icon',
        html: createShapeSVG(shape, color, size),
        iconSize: [size, size],
        iconAnchor: [anchor, anchor],
        popupAnchor: [0, -anchor]
    });
}

/**
 * POI_Type-based vector styling for line/polygon entities.
 * Geometry-specific options inherit from the symbology default when omitted.
 */
export function createVectorStyle(setting = {}, geometryFamily = 'line', defaultSetting = {}) {
    const color = setting.color || defaultSetting.color || '#64748B';

    if (geometryFamily === 'polygon') {
        const polygonDefault = defaultSetting.polygon || {};
        const polygon = setting.polygon || {};
        return {
            pane: 'polygonPane',
            color,
            weight: polygon.weight ?? polygonDefault.weight ?? 2,
            opacity: polygon.opacity ?? polygonDefault.opacity ?? 0.9,
            fillColor: polygon.fillColor || color,
            fillOpacity: polygon.fillOpacity ?? polygonDefault.fillOpacity ?? 0.18,
            dashArray: polygon.dashArray ?? polygonDefault.dashArray ?? null
        };
    }

    const lineDefault = defaultSetting.line || {};
    const line = setting.line || {};
    return {
        pane: 'linePane',
        color,
        weight: line.weight ?? lineDefault.weight ?? 4,
        opacity: line.opacity ?? lineDefault.opacity ?? 0.85,
        dashArray: line.dashArray ?? lineDefault.dashArray ?? null
    };
}

export function buildPopupContent(entityOrProperties) {
    const entity = entityOrProperties && entityOrProperties.feature
        ? entityOrProperties
        : createEntity({ type: 'Feature', properties: entityOrProperties || {}, geometry: null });

    const geometryLabel = entity.geometryFamily === 'line'
        ? 'Line'
        : (entity.geometryFamily === 'polygon' ? 'Polygon' : 'Point');
    const name = entity.name || `Unnamed ${geometryLabel}`;
    const topic = entity.topic || 'Unspecified';
    const type = entity.type || 'Unspecified';

    return `
        <div class="popup-summary">
            <div class="popup-title">${escapeHtml(name)}</div>
            <div class="popup-field"><strong>POI Type:</strong> ${escapeHtml(type)}</div>
            <div class="popup-field"><strong>Research Topic:</strong> ${escapeHtml(topic)}</div>
            <div class="popup-field"><strong>Geometry:</strong> ${escapeHtml(geometryLabel)}</div>
            <button type="button" class="popup-detail-button">View details</button>
        </div>
    `;
}
