import { normalizeGlobalId } from './entities.js';

export const ENRICHMENT_PATH = 'data/derived/enrichment.json';

export function attachEnrichment(entities, document) {
    const entries = document && typeof document.entities === 'object' && document.entities !== null ? document.entities : {};
    let matched = 0;
    for (const entity of entities) {
        const id = normalizeGlobalId(entity.entityId);
        const raw = id ? entries[id] : null;
        entity.enrichment = raw && typeof raw === 'object' ? raw : null;
        if (entity.enrichment) matched++;
    }
    return matched;
}
