# System Architecture — v1.3 Foundation

## Purpose

POIS Travel Science is designed as a geospatial platform with four long-term roles:

1. personal research and fieldwork support;
2. personal travel journal;
3. research/decision-support analysis environment;
4. later, a public discovery layer that can direct visitors to the personal/academic website.

Version 1.3 establishes the common technical foundation for those roles without changing the authoritative ArcGIS Online / Field Maps collection workflow.

## Non-negotiable architectural constraints

### ArcGIS Online / Field Maps remains authoritative

The existing ArcGIS Online layers, fields, coded domains, relationships, and Field Maps collection behavior are the source system. Website development must adapt around them.

A website feature that would require changing ArcGIS fields/domains/relationships or Field Maps behavior is exceptional and must be reviewed explicitly before implementation.

### English-only website

All authored user-facing website UI is English and LTR. This includes headers, labels, buttons, filters, popups, Detail Panel text, errors, empty states, embedded-mode controls, and future public pages.

Source data may contain text in other languages. The English-only requirement applies to authored website interface/content presentation, not to the forced rewriting of authoritative source attributes.

### Static runtime

The browser does not query ArcGIS directly during ordinary use. The runtime consumes repository-hosted generated files.

```text
ArcGIS Online / Field Maps
        ↓
GitHub Actions / fetch_data.py
        ↓
Repository data snapshot
        ↓
Static Leaflet application
```

This keeps deployment simple and makes the published snapshot reproducible and testable.

## Collection/build/runtime layers

### 1. Collection layer

ArcGIS Online / Field Maps contains the authoritative spatial records and attachments.

Current public website input:

```text
Point layer → data/pois.geojson
```

Existing but not yet publicly exported/published:

```text
Line layer
Polygon layer
```

### 2. Build/synchronization layer

`scripts/fetch_data.py` refreshes the point dataset and attachments and creates the generated exports used by the repository.

The weekly GitHub Actions workflow adds QA around that refresh:

```text
previous snapshot
      ↓
fetch_data.py
      ↓
qa_data.py
      ↓
qa_frontend.py
      ↓
commit/push generated data
```

An ERROR prevents the later publication commit. WARNING does not.

### 3. Website-data layer

ArcGIS-authored generated data and website-managed data remain separate.

```text
ArcGIS-derived
├── data/pois.geojson
├── data/pois.csv
├── data/pois.pdf
└── data/attachments/

Website-managed
└── data/site/poi-meta.json
```

Future external enrichment, Trips, Collections, Routes, and publication metadata should preserve this separation and provenance.

### 4. Client application layer

The browser normalizes GeoJSON features into generic Entities before using them in search, filters, detail display, or map navigation.

```text
GeoJSON source(s)
      ↓
js/data.js
      ↓
js/entities.js
      ↓
Entity objects
      ↓
filters / search / popup / Detail Panel / Leaflet rendering
```

## Generic Entity contract

An Entity has geometry-independent identity and attributes. Its `geometryFamily` may be `point`, `line`, `polygon`, or `unknown`.

The canonical identity is `entity.entityId`, derived from normalized ArcGIS `GlobalID`.

The architecture deliberately avoids using POI name, coordinates, `OBJECTID`, or feature order as stable identity.

See `entity-model.md` and `stable-id-strategy.md`.

## Classification model

`POI_Topic` and `POI_Type` are independent axes.

- `POI_Topic`: research-project/topic affiliation; `General` means no specific research affiliation.
- `POI_Type`: kind of entity/site; `General Site` means a generic type.

Both remain extensible. The client and QA pipeline must never silently drop a new source value simply because the website configuration has not yet been updated.

See `data-semantics.md` and `filtering.md`.

## Standalone and embedded presentation

The project uses one codebase with two display modes.

### Standalone

Full application presentation with global header and complete controls.

### Embedded

Activated by `?embed=true` or `?embed=1`. The global header is hidden and the layout is compacted for iframe/host-page use.

All core interaction must work in both modes. Release QA covers both desktop and narrow/mobile layouts.

## Multi-geometry strategy

Version 1.3 publishes the point source only, but the core application already supports geometry-independent:

- Entity normalization;
- stable identity;
- Topic/Type filtering;
- search focus behavior;
- bounds and representative navigation points;
- Detail Panel location summaries;
- vector styling policy;
- QA configuration.

When ArcGIS line/polygon export is activated later, the preferred approach is to add named data sources such as:

```text
data/lines.geojson
data/polygons.geojson
```

and extend the synchronization workflow rather than restructure the application.

## Future analytical architecture

Later releases may add:

- current-view/selected-entity statistics;
- clustering and spatial decision support;
- OSM/Nominatim or other external enrichment;
- Trips and travel timelines;
- research Collections;
- curated Routes, including natural-hazard routes;
- public/private publication builds;
- indexable public pages and deep links.

These capabilities should be derived around the existing ArcGIS system, linked by stable Entity ID, and should preserve explicit provenance.
