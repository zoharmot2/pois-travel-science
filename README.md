# POIS Travel Science

POIS Travel Science is a static, Leaflet-based geospatial application for exploring field-collected Points of Interest and related line/polygon features sourced primarily from Esri Field Maps and ArcGIS Online. The project is designed to evolve into a combined research tool, personal travel journal, analytical/decision-support environment, and later a public discovery layer linked to a personal/academic website.

The authoritative collection system remains **ArcGIS Online / Field Maps**. The website does not write back to ArcGIS and must not require disruptive changes to the ArcGIS schema or collection workflow.

> **Current release:** **1.4.0 — Multi-Geometry UI**. This release activates Point, Line, and Polygon publication together, redesigns the map controls around `POI_Type`, adds unified Type × Geometry filtering, multi-geometry search and Detail Panel behavior, media-aware attachments, and multi-dataset QA.

---

## Core principles

- **ArcGIS Online / Field Maps is authoritative.** Website features adapt around the existing collection structure.
- **English-only presentation.** Authored website UI is English and left-to-right.
- **Static runtime.** The browser loads repository-hosted JSON/GeoJSON and local attachments; it does not query ArcGIS during normal browsing.
- **Stable identity.** ArcGIS `GlobalID` is the canonical stable website Entity ID.
- **Extensible classifications.** `POI_Topic` and `POI_Type` remain data-driven and are not treated as closed hard-coded lists.
- **Multi-geometry publication.** Points, Lines, and Polygons are active first-class datasets.
- **One codebase, two display modes.** The application supports Standalone and Embedded presentation.
- **Derived website information stays separate.** Website-managed metadata and future Trips, Collections, Routes, enrichment, analytics, and publication rules remain outside the authoritative ArcGIS schema unless explicitly approved otherwise.

---

## v1.4.0 capabilities

Version 1.4.0 builds on the v1.3 Foundation and adds:

- simultaneous publication of `data/pois.geojson`, `data/lines.geojson`, and `data/polygons.geojson`;
- shared `POI_Type` symbology across Point, Line, and Polygon geometry families;
- integrated map controls ordered as **POI Types → Search → Geometry → Map Utilities**;
- unified `POI_Type AND Geometry` filtering with dynamic facet counts and `All | None` actions;
- a UI-only `Unspecified` bucket for blank source `POI_Type` values without rewriting ArcGIS data;
- multi-result search across currently visible Point/Line/Polygon Entities with keyboard navigation;
- geometry-aware focus behavior: Point center/zoom and Line/Polygon `fitBounds`;
- geometry-aware Detail Panel with coordinates for Points and derived map center/extent for Lines/Polygons;
- local image and audio attachment synchronization for all geometry families;
- remote handling for video and unsupported attachment types;
- structured attachment-media metadata and media-specific Detail Panel rendering;
- per-layer metadata/domain harvesting from the public Hosted Feature Layer View;
- multi-dataset QA covering Entity counts, geometry families, domains, stable IDs, attachments/media, and source-service consistency;
- full Standalone/Embedded desktop/mobile regression coverage.

Still deferred beyond v1.4.0: full analytics dashboards, DBSCAN/clustering, external enrichment, Trips/travel timeline, active Collections/Routes, public/private build separation, and SEO/public discovery pages.

---

## Data semantics

The two primary classification fields have different meanings and must remain independent:

- **`POI_Topic` — Research Topic / project affiliation.** `General` means no specific research-project affiliation.
- **`POI_Type` — Entity/site type.** `General Site` means a generic site type and is not a research-project designation.

In v1.4.0, `POI_Type` drives the primary map legend and symbology. `POI_Topic` remains research metadata used in the Entity model, search/detail context, and future analytics.

New values may appear in ArcGIS Online. Unknown Types remain visible using the configured fallback style and generate a QA/runtime warning rather than being silently discarded or merged.

See `docs/data-semantics.md`, `docs/filtering.md`, and `docs/symbology-v1.4.md`.

---

## Architecture and data flow

```text
Esri Field Maps / ArcGIS Online
        │
        │ authoritative collection data
        ▼
Public Hosted Feature Layer View
FeatureServer /0 Points /1 Lines /2 Polygons
        │
        ▼
GitHub Actions (weekly + manual)
        │
        ├── preserve previous spatial baseline
        ├── scripts/fetch_data.py
        ├── scripts/qa_data.py
        └── scripts/qa_frontend.py
        │
        ▼
Repository-hosted generated snapshot
        │
        ├── data/pois.geojson
        ├── data/lines.geojson
        ├── data/polygons.geojson
        ├── data/derived/layers-metadata.json
        ├── data/attachments/
        │   ├── points at legacy root paths
        │   ├── lines/
        │   └── polygons/
        ├── data/pois.csv
        └── data/pois.pdf
        │
        ▼
Static Leaflet application
        │
        ├── generic Entity normalization
        ├── Type × Geometry filtering
        ├── multi-geometry search
        ├── popup + Detail Panel
        └── Standalone / Embedded UI
```

The public website source is the Hosted Feature Layer View:

```text
https://services5.arcgis.com/eJYUV73IZAY87Jwy/arcgis/rest/services/POI_Feature_Layer_view/FeatureServer
```

Layers:

```text
/0  POI_Point_Layer
/1  POI_Line_Layer
/2  POI_Polygon_Layer
```

The browser consumes the repository snapshot only. ArcGIS synchronization occurs in the Python/GitHub Actions pipeline.

See `docs/architecture.md` and `docs/multi-layer-ingestion-v1.4.md`.

---

## Repository structure

```text
.
├── .github/workflows/sync.yml    # Weekly/manual ArcGIS refresh + QA
├── css/app.css                   # Application styles
├── data/
│   ├── attachments/              # Local images/audio; line/polygon subfolders
│   ├── derived/                  # Layer metadata and QA outputs
│   ├── site/poi-meta.json        # Website-managed metadata sidecar
│   ├── pois.geojson              # Point dataset
│   ├── lines.geojson             # Line dataset
│   ├── polygons.geojson          # Polygon dataset
│   ├── pois.csv                  # Point-oriented CSV export
│   └── pois.pdf                  # Point-oriented PDF export when generated
├── docs/                         # Architecture/development/release documentation
├── js/
│   ├── app.js                    # Application orchestration
│   ├── data.js                   # Multi-source loading and Entity creation
│   ├── details.js                # Multi-geometry Detail Panel/media rendering
│   ├── embed.js                  # Embedded-mode behavior
│   ├── entities.js               # Generic Entity/stable-ID/geometry helpers
│   ├── filters.js                # Type × Geometry filtering and controls
│   ├── map.js                    # Leaflet rendering, search, map utilities
│   └── metadata.js               # Metadata-sidecar linkage
├── scripts/
│   ├── fetch_data.py             # ArcGIS synchronization/export pipeline
│   ├── qa_config.json            # Data QA configuration
│   ├── qa_data.py                # Multi-dataset generated-data QA
│   └── qa_frontend.py            # Static frontend regression QA
├── config.json                   # Map settings + POI Type symbology
├── index.html                    # Application shell
├── README.md
└── VERSION                       # Official application version
```

---

## Local development

From the repository root in Windows Command Prompt:

```cmd
py -m http.server 8000
```

Standalone:

```text
http://localhost:8000/
```

Embedded:

```text
http://localhost:8000/?embed=true
```

`?embed=1` is also supported.

The project is normally edited locally and committed/pushed with GitHub Desktop.

---

## Local QA

Run:

```cmd
py scripts\qa_data.py
py scripts\qa_frontend.py
```

`qa_data.py` returns:

- `PASS` — no issues detected;
- `WARNING` — publication may continue, but source/configuration review is recommended;
- `ERROR` — publication should be blocked.

The data QA report is written to:

```text
data/derived/qa-report.json
```

For a release, also complete the browser matrix in `docs/regression-qa.md` for Standalone and Embedded modes at desktop and narrow/mobile widths.

---

## Weekly GitHub Actions refresh

The workflow is scheduled weekly and can be started manually. Its sequence is:

```text
Checkout
  ↓
Set up Python + dependencies
  ↓
Preserve previous Point/Line/Polygon snapshots
  ↓
Fetch all ArcGIS layers + attachments/media
  ↓
Validate generated data
  ↓
Validate frontend regression structure
  ↓
Upload QA report artifact
  ↓
Stage all data additions/modifications/deletions
  ↓
Commit and push refreshed data if validation did not fail
```

Warnings do not block publication. Errors return a non-zero exit status and prevent the later commit/push step.

---

## Standalone and Embedded modes

The same application code supports both modes.

- **Standalone** (`/`) shows the full header/navigation shell.
- **Embedded** (`/?embed=true` or `/?embed=1`) hides the global header and uses a compact layout suitable for iframe embedding.

Core filtering, search, map utilities, popups, Detail Panel, and all three geometry families must work in both modes.

---

## Stable identity and website metadata

ArcGIS `GlobalID` is normalized to lowercase UUID form without braces and exposed as `entity.entityId`.

`OBJECTID`, feature order, names, and coordinates are not used as stable website identity.

Website-specific metadata is stored separately in:

```text
data/site/poi-meta.json
```

The ArcGIS synchronization pipeline must never overwrite this sidecar. It is linked by stable Entity ID and is intended to support future Trips, Collections, Routes, travel/research annotations, publication metadata, and other website-owned information.

---

## Attachments and media

For Points, Lines, and Polygons:

- images are downloaded locally and may be optimized;
- audio is downloaded locally unchanged;
- video and unsupported media remain remote ArcGIS URLs;
- structured `attachment_media` metadata records media type/storage/source context;
- successful refreshes remove local attachment files that are no longer referenced by any current Entity;
- attachment-query/download failures stop the refresh before cleanup to avoid accidental mass deletion.

See `docs/media-attachments-v1.4.md`.

---

## Documentation

Start with `docs/README.md`.

Key current documents include:

- `docs/architecture.md`
- `docs/data-semantics.md`
- `docs/entity-model.md`
- `docs/filtering.md`
- `docs/symbology-v1.4.md`
- `docs/ui-v1.4.md`
- `docs/search-detail-v1.4.md`
- `docs/media-attachments-v1.4.md`
- `docs/multi-dataset-qa-v1.4.md`
- `docs/development-workflow.md`
- `docs/qa-pipeline.md`
- `docs/regression-qa.md`
- `docs/release-1.4.0.md`

---

## Versioning

Current official release: **1.4.0**.

Weekly ArcGIS data refreshes do not increment the application version. Application releases synchronize `VERSION`, the HTML title/version metadata, README/release documentation, regression QA, Git tag, and GitHub Release.

See `docs/release-1.4.0.md`.
