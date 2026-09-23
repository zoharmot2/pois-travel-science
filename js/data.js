import {
    createEntitiesFromSources,
    createEntityIdIndex,
    summarizeGeometryFamilies
} from './entities.js';
import {
    attachSiteMetadata,
    createEmptySiteMetadataSidecar,
    normalizeSiteMetadataSidecar
} from './metadata.js';

const SITE_METADATA_PATH = 'data/site/poi-meta.json';

// Stage 8 keeps only the current point export active. Future line/polygon exports
// can be added here without changing the Entity/filters/search/detail architecture.
const ENTITY_DATA_SOURCES = Object.freeze([
    { sourceDataset: 'points', path: 'data/pois.geojson', required: true }
]);

function withCacheBuster(path) {
    const separator = path.includes('?') ? '&' : '?';
    return `${path}${separator}t=${Date.now()}`;
}

async function fetchJson(path) {
    const response = await fetch(withCacheBuster(path), { cache: 'no-store' });
    if (!response.ok) {
        throw new Error(`Failed to load ${path}: HTTP ${response.status}`);
    }
    return response.json();
}

async function fetchOptionalJson(path, fallbackValue) {
    const response = await fetch(withCacheBuster(path), { cache: 'no-store' });

    if (response.status === 404) {
        console.warn(`Optional data file not found: ${path}. Continuing without website metadata.`);
        return fallbackValue;
    }

    if (!response.ok) {
        throw new Error(`Failed to load ${path}: HTTP ${response.status}`);
    }

    return response.json();
}

async function loadEntityDataSources() {
    return Promise.all(ENTITY_DATA_SOURCES.map(async source => ({
        ...source,
        geojsonData: await fetchJson(source.path)
    })));
}

export async function loadAppData() {
    const [config, entitySources, rawSiteMetadata] = await Promise.all([
        fetchJson('config.json'),
        loadEntityDataSources(),
        fetchOptionalJson(SITE_METADATA_PATH, createEmptySiteMetadataSidecar())
    ]);

    const entities = createEntitiesFromSources(entitySources);
    const geometrySummary = summarizeGeometryFamilies(entities);
    const { index: entityIdIndex, missing: entitiesMissingStableId } = createEntityIdIndex(entities);

    if (entitiesMissingStableId.length > 0) {
        console.warn(
            `${entitiesMissingStableId.length} entities are missing a valid ArcGIS GlobalID and therefore have no stable entity ID.`
        );
    }

    if (geometrySummary.unknown > 0) {
        console.warn(
            `${geometrySummary.unknown} entities have missing or unsupported geometry and may not render on the map.`
        );
    }

    const siteMetadata = normalizeSiteMetadataSidecar(rawSiteMetadata, entityIdIndex);
    const metadataMatchedCount = attachSiteMetadata(entities, siteMetadata);

    if (siteMetadata.invalidIds.length > 0) {
        console.warn(
            `${siteMetadata.invalidIds.length} website metadata records have invalid stable entity IDs and were ignored.`,
            siteMetadata.invalidIds
        );
    }

    if (siteMetadata.invalidRecords.length > 0) {
        console.warn(
            `${siteMetadata.invalidRecords.length} website metadata records are not JSON objects and were ignored.`,
            siteMetadata.invalidRecords
        );
    }

    if (siteMetadata.orphanIds.length > 0) {
        console.warn(
            `${siteMetadata.orphanIds.length} website metadata records reference entity IDs that are not present in the current ArcGIS snapshot.`,
            siteMetadata.orphanIds
        );
    }

    const pointSource = entitySources.find(source => source.sourceDataset === 'points');

    return {
        config,
        // Retained for backward compatibility during the v1.3 transition.
        geojsonData: pointSource ? pointSource.geojsonData : null,
        entitySources,
        entities,
        geometrySummary,
        entityIdIndex,
        entitiesMissingStableId,
        siteMetadata,
        metadataMatchedCount
    };
}
