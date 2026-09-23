# Stable Entity ID Strategy — v1.3 Foundation

## Decision

The canonical stable website identifier for an Entity is the ArcGIS `GlobalID`.

The website exposes it as:

```text
entity.entityId
```

The value is normalized to:

- lowercase
- no surrounding braces
- standard UUID form, for example `e5cd1f45-76fa-4fa5-a75c-4aea0b7ff422`

No new ArcGIS Online field is required.

## Why GlobalID

`GlobalID` is the appropriate identity for the website because it belongs to the source feature itself and is designed to remain associated with that feature across normal editing and synchronization workflows.

By contrast:

- `OBJECTID` / `FID` are operational row identifiers and are not considered stable website identity.
- GeoJSON `feature.id` is retained as a source/export identifier only.
- POI names are editable and are therefore unsuitable as identifiers.
- Coordinates may change as field locations are corrected and are therefore unsuitable as identifiers.

## Entity contract

Each normalized Entity contains:

```text
entityId
entityIdSource
sourceIds.featureId
sourceIds.objectId
sourceIds.globalId
sourceIds.normalizedGlobalId
```

`entityIdSource` is `GlobalID` when a valid canonical ID is available.

## Missing IDs

The application does not synthesize a fake stable ID from `OBJECTID`, feature order, name, or coordinates.

If a future feature lacks a valid GlobalID:

- the feature can still be loaded and displayed;
- `entity.entityId` is `null`;
- the loader emits a warning;
- the later v1.3 QA stage will define whether such a condition should block publication for datasets that require stable identity.

This avoids creating references that appear stable but are not.

## Duplicate IDs

Duplicate canonical IDs are an application error. The data loader rejects duplicate stable IDs because future sidecar metadata, Trips, Collections, Routes, deep links, and public pages must resolve one ID to exactly one Entity.

## Website metadata sidecar

Website-only metadata references ArcGIS entities by `entityId`, never by POI name or `OBJECTID`.

Beginning with v1.3 Stage 5, the canonical sidecar is `data/site/poi-meta.json`. Its `entities` object is keyed directly by normalized `entityId` values:

```json
{
  "schemaVersion": 1,
  "entities": {
    "e5cd1f45-76fa-4fa5-a75c-4aea0b7ff422": {
      "exampleFutureField": "value"
    }
  }
}
```

The metadata payload is intentionally left open at this stage. See `docs/metadata-sidecar.md` for the current contract and integrity rules.

## Multi-geometry compatibility

The same policy applies to point, line, and polygon entities. Each ArcGIS source layer should provide a valid GlobalID for any feature that needs to participate in cross-file website relationships.
