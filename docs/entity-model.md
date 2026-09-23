# Entity Model — v1.3 Foundation

Version 1.3 introduces a generic in-browser `Entity` model between source GeoJSON and the website UI. The current point dataset remains the only dataset published by the website in v1.3, but the application contract is geometry-agnostic and ready for future point, line, and polygon datasets.

## Purpose

The website must not assume that every future record is a point. ArcGIS Online already contains point, line, and polygon collection layers. The Entity model gives the application a common contract for those geometry families without changing the authoritative ArcGIS Online / Field Maps schema.

## Data flow

```text
ArcGIS-derived GeoJSON source(s)
        ↓
createEntity(feature, source options)
        ↓
Generic Entity
        ↓
filters / search / detail panel / map rendering
```

The original GeoJSON Feature is retained on `entity.feature`, so Leaflet can continue to consume standard GeoJSON and the current point workflow remains compatible.

## Current Entity shape

```text
Entity
├── entityId               Canonical stable website ID (normalized ArcGIS GlobalID)
├── entityIdSource         `GlobalID` when a valid stable ID is available
├── sourceDataset          Website data-source key, currently `points`
├── feature                Original GeoJSON Feature
├── properties             Original ArcGIS-derived properties
├── geometry               Original GeoJSON geometry
├── geometryType           Point / MultiPoint / LineString / Polygon / etc.
├── geometryFamily         point / line / polygon / unknown
├── bounds                 Plain geographic extent or null
│   ├── west
│   ├── south
│   ├── east
│   └── north
├── representativePoint    Geometry-independent map-navigation point or null
│   ├── latitude
│   ├── longitude
│   └── method             `point` or `bounds-center`
├── sourceIds
│   ├── featureId          GeoJSON feature.id, if present
│   ├── objectId           ArcGIS OBJECTID/FID, if present
│   ├── globalId           Raw ArcGIS GlobalID, if present
│   └── normalizedGlobalId Canonical normalized GlobalID
├── name                   Normalized display name
├── topic                  POI_Topic
├── type                   POI_Type
├── description            POI description
├── creationDate
├── collectionDate
├── latitude               Single Point coordinate only; otherwise null
├── longitude              Single Point coordinate only; otherwise null
├── attachments[]          Normalized attachment list
└── websiteMetadata        Website-managed sidecar record or null
```

## Geometry families

The model recognizes these GeoJSON geometry types:

- `Point`, `MultiPoint` → `point`
- `LineString`, `MultiLineString` → `line`
- `Polygon`, `MultiPolygon` → `polygon`
- anything else or missing geometry → `unknown`

Actual line and polygon export/publication is **not** part of v1.3. Stage 8 only removes point-only assumptions from the application architecture.

## Geometry-independent spatial helpers

Every supported geometry may expose `bounds` and a `representativePoint`.

For a single `Point`, `representativePoint` is the point itself. For `MultiPoint`, line, and polygon geometries, it is the center of the geometry bounding box. This value exists only for navigation and UI summaries. It is **not** a scientific centroid and must not be used as an analytical measurement.

The existing `latitude` and `longitude` Entity properties remain single-Point coordinates only, preserving their original meaning.

## Multi-source readiness

The loader now treats spatial exports as named data sources. Only the current source is active in v1.3:

```text
points → data/pois.geojson
```

When the existing ArcGIS line and polygon layers are later added to the GitHub Actions export pipeline, they can be introduced as additional sources while preserving the same Entity contract, stable-ID validation, filters, search, detail panel, and map-rendering flow.

## Stable identity

The canonical website identifier is `entity.entityId`.

It is derived from the ArcGIS `GlobalID`, normalized to a lowercase UUID without braces. `OBJECTID`, `FID`, and GeoJSON `feature.id` remain source identifiers only and must not be used as stable website identity because they may change when data is exported, recreated, or refreshed.

The current point snapshot contains a valid and unique `GlobalID` for every record. If a future record lacks a valid GlobalID, the Entity remains renderable but `entityId` is `null` and the data loader reports the condition. Duplicate stable IDs are treated as an error because they make entity references ambiguous.

The stable-ID policy is documented in more detail in `docs/stable-id-strategy.md`.

## Extensibility

`POI_Topic` and `POI_Type` remain plain data values on the Entity. The Entity model does not define closed lists for either field. Dynamic Topic/Type handling therefore continues to consume values added in ArcGIS Online without changing the Entity structure.

## Website-managed metadata

An Entity may receive a `websiteMetadata` property after the ArcGIS snapshot and the website metadata sidecar are loaded. This property is **not** an ArcGIS-authored attribute and is never written back to ArcGIS Online.

```js
entity.websiteMetadata // object or null
```

The sidecar linkage uses the canonical `entity.entityId` (normalized ArcGIS `GlobalID`). ArcGIS properties remain available separately in `entity.properties`, preserving a clear provenance boundary between source data and website-managed information.
