# Multi-Geometry Readiness — v1.3 Stage 8

Stage 8 prepares the website architecture for the existing ArcGIS Online line and polygon collection layers without publishing those layers yet and without changing ArcGIS Online / Field Maps.

## Scope

Stage 8 is an architectural readiness step. The live data source remains:

```text
data/pois.geojson → points
```

No line or polygon GeoJSON file is fetched by the website in v1.3, and the GitHub Actions export workflow is not changed in this stage.

## What is now geometry-agnostic

The application now supports a common rendering/navigation contract for:

- Point / MultiPoint
- LineString / MultiLineString
- Polygon / MultiPolygon

The following components no longer assume that every Entity is a marker:

- Entity normalization
- geographic bounds and representative map position
- data-source combination
- Topic-based map styling
- popup/detail binding
- search navigation
- Detail Panel location summary
- map fitting and initial bounds
- stable-ID indexing
- Topic and Type filtering

## Rendering policy

Points retain the existing topic marker shape/color configured in `config.json`.

Future line geometries use the Topic color as the stroke color. Future polygons use the Topic color for both outline and a low-opacity fill. Missing Topic styling continues to use the existing default style.

This does not activate line/polygon publication; it only defines safe behavior once those datasets are exported later.

## Navigation policy

Search and Detail Panel navigation now use the geometry type exposed by the Leaflet layer:

- point-like marker → focus by `getLatLng()`
- line/polygon → fit the geometry `getBounds()`
- fallback → use the Entity `representativePoint`

For non-single-point geometries, the Entity `representativePoint` is the center of the geometry bounding box. This is a UI/navigation helper only and is not an analytical centroid.

## Data-source policy

`js/data.js` now defines spatial exports as named sources. Stage 8 activates only:

```js
{ sourceDataset: 'points', path: 'data/pois.geojson' }
```

Later integration of line/polygon exports can extend this source list after the GitHub Actions pipeline is updated. The rest of the application should not need a structural rewrite.

## Detail Panel behavior

Single Points continue to display their actual coordinates.

Future MultiPoint/line/polygon entities can display:

- geometry type
- derived map center
- geographic extent
- source dataset

The derived map center is clearly labelled as derived.

## Explicitly not included

Stage 8 does **not**:

- modify ArcGIS Online fields, domains, relationships, or Field Maps
- export line/polygon data from ArcGIS
- add line/polygon files to GitHub Actions
- publish line/polygon layers on the live site
- add analytical length/area/centroid calculations
- change the official version from 1.2.0 during development

Actual line/polygon publication remains a later implementation task after the collection/export workflow is ready.
