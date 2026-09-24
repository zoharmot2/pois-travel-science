# Entity Model — v1.4.0

The in-browser `Entity` model provides one geometry-independent contract for the three active ArcGIS-derived datasets: Points, Lines, and Polygons.

## Purpose

ArcGIS Online contains separate geometry layers, while the website needs common behavior for identity, classification, filtering, search, detail display, media, and navigation. The Entity model provides that common contract without changing the authoritative ArcGIS Online / Field Maps schema.

## Data flow

```text
ArcGIS-derived GeoJSON source(s)
        ↓
createEntity(feature, source options)
        ↓
Generic Entity
        ↓
filtering / search / Detail Panel / map rendering
```

The original GeoJSON Feature is retained on `entity.feature` so Leaflet can consume standard GeoJSON geometry and source properties remain available.

## Active sources

```text
points   → data/pois.geojson
lines    → data/lines.geojson
polygons → data/polygons.geojson
```

Each Entity records its `sourceDataset` so source-specific behavior can be audited without changing the generic UI contract.

## Current Entity shape

```text
Entity
├── entityId               Canonical stable website ID (normalized ArcGIS GlobalID)
├── entityIdSource         `GlobalID` when valid
├── sourceDataset          points / lines / polygons
├── feature                Original GeoJSON Feature
├── properties             Original ArcGIS-derived properties
├── geometry               Original GeoJSON geometry
├── geometryType           Point / MultiPoint / LineString / Polygon / etc.
├── geometryFamily         point / line / polygon / unknown
├── bounds                 Geographic extent or null
│   ├── west
│   ├── south
│   ├── east
│   └── north
├── representativePoint    Navigation/display helper or null
│   ├── latitude
│   ├── longitude
│   └── method             point or bounds-center
├── sourceIds
│   ├── featureId
│   ├── objectId
│   ├── globalId
│   └── normalizedGlobalId
├── name
├── topic                  POI_Topic
├── type                   POI_Type
├── description
├── creationDate
├── collectionDate
├── latitude               Single Point coordinate only; otherwise null
├── longitude              Single Point coordinate only; otherwise null
├── attachments[]          Backward-compatible URL list
├── attachmentMedia[]      Structured media descriptors
└── websiteMetadata        Website-managed sidecar record or null
```

## Geometry families

The model recognizes:

- `Point`, `MultiPoint` → `point`
- `LineString`, `MultiLineString` → `line`
- `Polygon`, `MultiPolygon` → `polygon`
- missing/other geometry → `unknown`

## Geometry-independent spatial helpers

Every supported geometry may expose `bounds` and a `representativePoint`.

For a single `Point`, `representativePoint` is the point itself. For MultiPoint, Line, and Polygon geometries, it is derived from the geometry extent for UI/navigation purposes only. It is **not** a scientific centroid and must not be used as an analytical measurement.

The `latitude` and `longitude` Entity properties remain single-Point coordinates only.

## Stable identity

The canonical website identifier is `entity.entityId`, derived from ArcGIS `GlobalID` and normalized to lowercase UUID form without braces.

`OBJECTID`, FID, feature order, names, and coordinates are source/representation details and must not be used as stable identity.

A record without a usable GlobalID may still be renderable, but stable-ID-dependent workflows cannot safely reference it. Duplicate stable IDs are publication errors because they make cross-Entity references ambiguous.

## Classification extensibility

`POI_Topic` and `POI_Type` remain plain source values; the Entity model does not define closed lists.

- `POI_Type` drives v1.4 primary map symbology/filtering.
- `POI_Topic` remains research metadata.
- blank Type values are not rewritten by the Entity model; the filter UI may expose them through a synthetic `Unspecified` bucket.

## Attachments/media

`attachments[]` is retained for backward compatibility. `attachmentMedia[]` is the normalized current representation and may include:

```text
url
name
contentType
kind       image / audio / video / other
storage    local / remote
attachmentId
parentObjectId
sourceDataset
```

The browser uses media metadata when available rather than guessing solely from URL suffixes.

## Website-managed metadata

An Entity may receive `websiteMetadata` after the ArcGIS snapshot and the website sidecar are loaded.

```js
entity.websiteMetadata // object or null
```

The sidecar linkage uses canonical `entity.entityId`. ArcGIS properties remain separate in `entity.properties`, preserving provenance between collection data and website-owned information.
