# Multi-Geometry Readiness — v1.3 Foundation

Version 1.3 prepares the website architecture for the existing ArcGIS Online line and polygon collection layers without publishing those layers yet and without changing ArcGIS Online / Field Maps.

## Current scope

The live website data source remains:

```text
data/pois.geojson → points
```

The ArcGIS line and polygon layers already exist as collection layers, but their records are not yet exported by `fetch_data.py` and are not yet published by the website.

The QA configuration already reserves optional future inputs:

```text
data/lines.geojson
data/polygons.geojson
```

Missing optional files do not currently warn or fail.

## What is geometry-agnostic

The application supports a common normalization/navigation contract for:

- Point / MultiPoint
- LineString / MultiLineString
- Polygon / MultiPolygon

The following components no longer assume that every Entity is a point marker:

- Entity normalization;
- geographic bounds and representative map position;
- data-source combination;
- Topic-based map styling policy;
- popup/detail binding;
- search navigation;
- Detail Panel location summary;
- map fitting and initial bounds;
- stable-ID indexing;
- Topic and Type filtering;
- QA validation and cross-dataset stable-ID uniqueness.

## Rendering policy

Points retain the existing Topic marker shape/color configured in `config.json`.

Future lines use the Topic color as stroke color. Future polygons use the Topic color for outline and a low-opacity fill. A missing Topic style uses the configured default style and is reported as a QA warning rather than hiding the Entity.

This policy does not activate line/polygon publication; it defines safe default behavior once those datasets are added.

## Navigation policy

Search and Detail Panel navigation are geometry-aware:

- point-like layer → focus by `getLatLng()`;
- line/polygon → fit layer `getBounds()`;
- fallback → use the Entity `representativePoint`.

For non-single-point geometries, `representativePoint` is the center of the geometry bounding box. It is a UI/navigation helper only and must not be treated as a scientific centroid.

## Data-source policy

`js/data.js` treats spatial exports as named sources. Version 1.3 activates only the `points` source.

Future activation should extend the source list after the export pipeline generates the new files. The rest of the application should not require structural rewriting.

## Stable IDs across geometry families

ArcGIS `GlobalID` remains the canonical identity for all geometry families. Data QA enforces global uniqueness across every active point, line, and polygon dataset, not merely uniqueness inside each file.

This is required so metadata, future Trips/Collections/Routes, deep links, and public pages can resolve one ID to exactly one Entity.

## Future activation checklist

When line or polygon publication is implemented:

1. identify and verify the authoritative ArcGIS layer endpoint;
2. extend `fetch_data.py` to export the layer without disrupting point export;
3. confirm every published feature has a valid `GlobalID`;
4. confirm field mapping into the Entity model;
5. generate the intended GeoJSON file;
6. activate the named source in `js/data.js`;
7. run `qa_data.py` and `qa_frontend.py`;
8. perform standalone/embedded browser regression QA;
9. verify rendering, filtering, search focus, and Detail Panel behavior for the new geometry family.

## Explicitly not included in v1.3

Version 1.3 does not:

- modify ArcGIS Online fields, domains, relationships, or Field Maps behavior;
- export line/polygon data from ArcGIS;
- publish line/polygon layers on the live site;
- add analytical length/area/centroid calculations;
- use derived navigation centers as scientific measurements.

Actual line/polygon export and publication remains a later implementation task.
