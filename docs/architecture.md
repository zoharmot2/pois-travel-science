# System Architecture — v1.4.0

## Purpose

POIS Travel Science is designed as a geospatial platform with four long-term roles:

1. personal research and fieldwork support;
2. personal travel journal;
3. research/decision-support analysis environment;
4. later, a public discovery layer linked to the personal/academic website.

Version 1.4.0 extends the v1.3 Foundation by activating the existing ArcGIS Point, Line, and Polygon layers as simultaneous website datasets while preserving the authoritative ArcGIS Online / Field Maps collection workflow.

## Non-negotiable architectural constraints

### ArcGIS Online / Field Maps remains authoritative

The existing ArcGIS Online layers, fields, coded domains, relationships, and Field Maps collection behavior remain the source system. Website development adapts around them.

Changes to ArcGIS fields, domains, relationships, or Field Maps behavior are exceptional and require explicit review before implementation.

### English-only website

All authored user-facing website UI is English and LTR. Source attributes may contain other languages; the website does not rewrite authoritative source text merely to satisfy the interface-language rule.

### Static runtime

The browser does not query ArcGIS directly during ordinary use. The runtime consumes repository-hosted generated files.

```text
ArcGIS Online / Field Maps
        ↓
Public Hosted Feature Layer View
        ↓
GitHub Actions / fetch_data.py
        ↓
Repository snapshot
        ↓
Static Leaflet application
```

This keeps deployment simple and makes the published snapshot reproducible and testable.

## Source service and active layers

Website export uses the public Hosted Feature Layer View:

```text
https://services5.arcgis.com/eJYUV73IZAY87Jwy/arcgis/rest/services/POI_Feature_Layer_view/FeatureServer
```

Active sublayers:

```text
/0  POI_Point_Layer
/1  POI_Line_Layer
/2  POI_Polygon_Layer
```

The protected source service is not used by the static export workflow.

## Collection/build/runtime layers

### 1. Collection layer

ArcGIS Online / Field Maps contains the authoritative Point, Line, and Polygon records and their attachments.

### 2. Build/synchronization layer

`scripts/fetch_data.py` refreshes all three datasets, harvests layer metadata/domains, synchronizes supported attachments, and writes repository outputs only after the multi-layer fetch/process phase succeeds.

The weekly/manual GitHub Actions workflow surrounds that refresh with QA:

```text
previous Point/Line/Polygon snapshots
        ↓
fetch_data.py
        ↓
qa_data.py
        ↓
qa_frontend.py
        ↓
commit/push generated data
```

An `ERROR` blocks the later publication commit. A `WARNING` does not block it.

### 3. Website-data layer

ArcGIS-derived generated data and website-managed metadata remain separate.

```text
ArcGIS-derived
├── data/pois.geojson
├── data/lines.geojson
├── data/polygons.geojson
├── data/derived/layers-metadata.json
├── data/pois.csv
├── data/pois.pdf
└── data/attachments/
    ├── point attachment paths at the legacy root
    ├── lines/
    └── polygons/

Website-managed
└── data/site/poi-meta.json
```

Future external enrichment, Trips, Collections, Routes, annotations, and publication metadata should preserve this provenance separation.

### 4. Client application layer

The browser loads all active GeoJSON sources and normalizes them into generic Entities before filtering, search, detail display, or map navigation.

```text
Point/Line/Polygon GeoJSON
        ↓
js/data.js
        ↓
js/entities.js
        ↓
Entity objects
        ↓
Type × Geometry filters
        ↓
search / popup / Detail Panel / Leaflet rendering
```

## Generic Entity contract

An Entity has geometry-independent identity and source attributes. `geometryFamily` may be `point`, `line`, `polygon`, or `unknown`.

The canonical identity is `entity.entityId`, derived from normalized ArcGIS `GlobalID`. Names, coordinates, `OBJECTID`, and feature order are never treated as stable website identity.

See `entity-model.md` and `stable-id-strategy.md`.

## Classification and symbology model

`POI_Topic` and `POI_Type` remain independent semantic axes:

- `POI_Topic`: research-project/topic affiliation;
- `POI_Type`: kind of entity/site.

In v1.4.0, `POI_Type` is the primary map legend/filter/symbology field. A Type uses one color across geometry families:

- Point: configured marker symbol/color;
- Line: same Type color as stroke;
- Polygon: same Type color as outline plus translucent fill.

`POI_Topic` remains research metadata for display and future analytical use.

## Unified filtering

The primary visibility rule is:

```text
selected POI Types
        AND
selected Geometry families
```

Counts are faceted across the opposite dimension. Blank source Types remain blank in the Entity data but are exposed through a UI-only `Unspecified` bucket so they can be controlled without silently rewriting source values.

## Search and geometry-aware navigation

Search operates on currently visible Entities after Type × Geometry filtering. The current interface provides up to eight ranked results and keyboard navigation.

Navigation behavior:

```text
Point   → center/zoom
Line    → fitBounds
Polygon → fitBounds
```

For non-point geometries, any derived map center is a UI/navigation helper based on extent and is not a scientific centroid.

## Attachments/media

Supported local synchronization:

- image: local download, optional optimization;
- audio: local download unchanged.

Remote-reference handling:

- video;
- other unsupported media.

`attachment_media` preserves structured kind/storage/source metadata. Cleanup runs only after successful synchronization so temporary ArcGIS failures do not trigger mass local deletion.

## Standalone and Embedded presentation

One codebase supports both modes.

- Standalone: full header and controls.
- Embedded: `?embed=true` or `?embed=1`, with reduced chrome suitable for iframe use.

All three geometry families, filtering, search, popup/detail behavior, media, and map utilities are regression-tested in both modes at desktop and narrow/mobile widths.

## QA architecture

The release/data-refresh gate combines:

- geometry/schema validation;
- stable-ID uniqueness;
- required output checks;
- layer metadata/source consistency;
- domain comparison without requiring all layers to remain identical;
- attachment/media validation;
- missing/orphan local file checks;
- baseline add/remove deltas;
- static frontend contract regression;
- manual browser regression for releases.

## Future analytical architecture

Later releases may add analytics, clustering, external enrichment, Trips/timelines, Collections, Routes, public/private publication builds, and indexable public pages. These should be derived around the existing ArcGIS system, linked by stable Entity ID, and preserve explicit provenance.
