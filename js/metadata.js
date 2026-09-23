import { normalizeGlobalId } from './entities.js';

export const SITE_METADATA_SCHEMA_VERSION = 1;

function isPlainObject(value) {
    return value !== null && typeof value === 'object' && !Array.isArray(value);
}

export function createEmptySiteMetadataSidecar() {
    return {
        schemaVersion: SITE_METADATA_SCHEMA_VERSION,
        entities: {}
    };
}

/**
 * Normalize and validate the website-managed metadata sidecar.
 *
 * Sidecar records are keyed by the canonical ArcGIS GlobalID-based entity ID.
 * Keys are normalized using the same UUID rules as Entity.entityId so metadata
 * remains linked even if a manually entered UUID uses braces or uppercase.
 *
 * The values are intentionally opaque plain objects in v1.3 Stage 5. Trips,
 * Collections, Routes, publication state, and other future schemas are not
 * defined here yet; this layer only establishes safe one-to-one linkage.
 */
export function normalizeSiteMetadataSidecar(rawSidecar, entityIdIndex = new Map()) {
    const sidecar = rawSidecar ?? createEmptySiteMetadataSidecar();

    if (!isPlainObject(sidecar)) {
        throw new Error('Site metadata sidecar must be a JSON object.');
    }

    const schemaVersion = Number(sidecar.schemaVersion);
    if (schemaVersion !== SITE_METADATA_SCHEMA_VERSION) {
        throw new Error(
            `Unsupported site metadata schemaVersion: ${sidecar.schemaVersion}. ` +
            `Expected ${SITE_METADATA_SCHEMA_VERSION}.`
        );
    }

    if (!isPlainObject(sidecar.entities)) {
        throw new Error('Site metadata sidecar "entities" must be a JSON object keyed by stable entity ID.');
    }

    const byEntityId = new Map();
    const invalidIds = [];
    const invalidRecords = [];
    const orphanIds = [];

    for (const [rawEntityId, metadata] of Object.entries(sidecar.entities)) {
        const entityId = normalizeGlobalId(rawEntityId);
        if (!entityId) {
            invalidIds.push(rawEntityId);
            continue;
        }

        if (!isPlainObject(metadata)) {
            invalidRecords.push(entityId);
            continue;
        }

        if (byEntityId.has(entityId)) {
            throw new Error(`Duplicate normalized entity ID in site metadata: ${entityId}`);
        }

        byEntityId.set(entityId, metadata);

        if (entityIdIndex instanceof Map && !entityIdIndex.has(entityId)) {
            orphanIds.push(entityId);
        }
    }

    return {
        schemaVersion,
        byEntityId,
        invalidIds,
        invalidRecords,
        orphanIds,
        recordCount: byEntityId.size
    };
}

/**
 * Attach website-managed metadata to normalized Entity objects.
 *
 * ArcGIS-authored properties remain untouched. The sidecar lives in the
 * separate `websiteMetadata` property, preserving provenance by construction.
 */
export function attachSiteMetadata(entities, siteMetadata) {
    const byEntityId = siteMetadata && siteMetadata.byEntityId instanceof Map
        ? siteMetadata.byEntityId
        : new Map();

    let matchedCount = 0;

    for (const entity of entities) {
        const metadata = entity && entity.entityId
            ? byEntityId.get(entity.entityId) ?? null
            : null;

        entity.websiteMetadata = metadata;
        if (metadata) matchedCount += 1;
    }

    return matchedCount;
}
