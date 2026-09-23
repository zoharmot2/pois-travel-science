# POIS Travel Science

POIS Travel Science is a static, Leaflet-based geospatial application for exploring Points of Interest collected primarily through Esri Field Maps and ArcGIS Online. The project is designed to evolve into a combined research tool, personal travel journal, analytical/decision-support environment, and later a public discovery layer linked to a personal/academic website.

The authoritative collection system remains **ArcGIS Online / Field Maps**. The website does not write back to ArcGIS and must not require disruptive changes to the ArcGIS schema or collection workflow.

> **Current release:** **1.3.0** — the Foundation release that establishes the modular Entity architecture, stable IDs, extensible Topic/Type filtering, Detail Panel, multi-geometry readiness, and automated QA pipeline.

---

## Core principles

- **ArcGIS Online / Field Maps is authoritative.** Website features adapt around the existing ArcGIS collection structure.
- **English-only presentation.** All authored website UI is English and left-to-right.
- **Static runtime.** The browser loads repository-hosted JSON/GeoJSON and attachments; it does not query the ArcGIS Feature Service directly during normal browsing.
- **Stable identity.** ArcGIS `GlobalID` is the canonical stable website Entity ID.
- **Extensible classifications.** `POI_Topic` and `POI_Type` are not hard-coded closed lists.
- **Multi-geometry-ready architecture.** Points are published now; existing ArcGIS line and polygon layers are planned for later export and publication.
- **One codebase, two display modes.** The application supports both standalone and embedded use.
- **Derived website information stays separate.** Website-managed metadata, future Trips, Collections, Routes, enrichment, and publication rules are kept outside the authoritative ArcGIS schema unless explicitly approved otherwise.

---

## v1.3 Foundation capabilities

The v1.3 release establishes the architectural foundation required for later research, travel-journal, analytical, and public-facing features:

- modular HTML/CSS/JavaScript frontend rather than a monolithic `index.html`;
- generic `Entity` model supporting point, line, and polygon geometry families conceptually;
- normalized ArcGIS `GlobalID` stable Entity IDs;
- website-managed metadata sidecar linked by stable ID;
- independent **Research Topic** (`POI_Topic`) and **POI Type** (`POI_Type`) filters;
- data-driven filter values with safe fallback behavior for future Topics/Types;
- concise map popups plus a richer Entity Detail Panel;
- search integrated with the Entity model and active filters;
- geometry-aware navigation and rendering readiness for future line/polygon datasets;
- automated data QA for the weekly GitHub Actions refresh;
- automated frontend regression checks;
- formal standalone and embedded display behavior.

The following remain outside v1.3: full analytics dashboards, analytical clustering, OSM/Nominatim enrichment, Trips, travel timelines, active Collections, Routes, public/private publication builds, SEO content pages, and actual line/polygon publication.

---

## Data semantics

The two main classification fields have different meanings and must remain independent:

- **`POI_Topic` — Research Topic / project affiliation.** `General` means that the Entity has no specific research-project affiliation.
- **`POI_Type` — Entity/site type.** `General Site` means a generic site type and is not a research-project designation.

A record can therefore be, for example, `Historical Earthquakes` as its Research Topic and `Structure/Building` as its POI Type.

New Topic and Type values may be added in ArcGIS Online in the future. The website must continue to load them without structural code changes. A new Topic without explicit styling appears with the configured default symbol and generates a QA warning; new Types are derived directly from the exported data.

See `docs/data-semantics.md` and `docs/filtering.md` for details.

---

## Architecture and data flow

```text
Esri Field Maps / ArcGIS Online
        │
        │ authoritative collection data
        ▼
GitHub Actions (weekly + manual)
        │
        ├── preserve previous spatial snapshot for QA deltas
        ├── scripts/fetch_data.py
        ├── scripts/qa_data.py
        └── scripts/qa_frontend.py
        │
        ▼
Repository-hosted generated data
        │
        ├── data/pois.geojson
        ├── data/pois.csv
        ├── data/pois.pdf
        ├── data/attachments/
        └── future: data/lines.geojson / data/polygons.geojson
        │
        ▼
Static Leaflet application
        │
        ├── Entity normalization
        ├── filters + search
        ├── popup + Detail Panel
        └── standalone / embedded UI
```

The browser loads the current repository snapshot. ArcGIS synchronization happens only in the Python/GitHub Actions pipeline.

See `docs/architecture.md` for the detailed contract.

---

## Repository structure

```text
.
├── .git/                         # Local Git metadata
├── .github/
│   └── workflows/
│       └── sync.yml              # Weekly/manual ArcGIS refresh + QA workflow
├── css/
│   └── app.css                   # Application styles
├── data/
│   ├── attachments/              # Local image attachments
│   ├── derived/                  # Generated QA/derived outputs
│   ├── site/
│   │   └── poi-meta.json         # Website-managed metadata sidecar
│   ├── pois.geojson              # Current point dataset used by the map
│   ├── pois.csv                  # Tabular export
│   └── pois.pdf                  # PDF export
├── docs/                         # Architecture and development documentation
├── js/
│   ├── app.js                    # Application orchestration
│   ├── data.js                   # Data-source loading and Entity creation
│   ├── details.js                # Entity Detail Panel
│   ├── embed.js                  # Embedded-mode behavior
│   ├── entities.js               # Generic Entity model and stable-ID helpers
│   ├── filters.js                # Topic/Type filtering
│   ├── map.js                    # Leaflet rendering, search, and map utilities
│   └── metadata.js               # Metadata-sidecar loading/linkage
├── scripts/
│   ├── fetch_data.py             # ArcGIS synchronization/export pipeline
│   ├── qa_config.json            # Data QA configuration
│   ├── qa_data.py                # Generated-data QA
│   └── qa_frontend.py            # Static frontend regression QA
├── .gitattributes
├── config.json                   # Map settings and Topic symbology
├── index.html                    # Application shell
├── README.md
└── VERSION                       # Official application version
```

The future line and polygon exports are intentionally not active in v1.3, but the Entity model, data-source loader, navigation logic, and QA configuration already anticipate them.

---

## Local development

Work from the repository root. A local HTTP server is required because the application loads JSON/GeoJSON with browser requests; do not open `index.html` directly with `file://`.

Using Windows Command Prompt:

```cmd
py -m http.server 8000
```

Open the standalone application:

```text
http://localhost:8000/
```

Open embedded mode:

```text
http://localhost:8000/?embed=true
```

`?embed=1` is also supported.

The project is normally edited locally and committed/pushed with GitHub Desktop.

---

## Local QA

Run generated-data QA:

```cmd
py scripts\qa_data.py
```

Run frontend regression QA:

```cmd
py scripts\qa_frontend.py
```

`qa_data.py` returns:

- `PASS` — no issues detected;
- `WARNING` — publication may continue, but source/configuration review is recommended;
- `ERROR` — publication should be blocked.

The generated report is written to:

```text
data/derived/qa-report.json
```

The weekly GitHub Actions workflow also publishes a readable job summary and uploads the QA report as an Actions artifact. The report itself is not committed merely because its timestamp changed.

See `docs/qa-pipeline.md` and `docs/regression-qa.md`.

---

## Weekly GitHub Actions refresh

The workflow can run manually and is scheduled weekly. Its current sequence is:

```text
Checkout
  ↓
Set up Python
  ↓
Install dependencies
  ↓
Preserve previous point/line/polygon snapshots for delta QA
  ↓
Fetch ArcGIS data and attachments
  ↓
Validate generated data
  ↓
Validate frontend regression structure
  ↓
Upload QA report artifact
  ↓
Commit and push refreshed data if validation did not fail
```

Warnings do not block publication. QA errors return a non-zero exit status and prevent the later commit/push step from running.

Weekly automated data-refresh commits should be distinguished from application-code/configuration commits when reviewing project history.

---

## Standalone and embedded modes

The same application code supports both modes.

### Standalone

```text
/
```

Displays the full header and complete map experience.

### Embedded

```text
/?embed=true
```

Hides the global header and uses a more compact layout suitable for iframe embedding. The map, filters, search, popup, and Detail Panel remain functional.

Every frontend release must be regression-tested in both modes and at desktop and narrow/mobile widths.

---

## Stable identity and website metadata

ArcGIS `GlobalID` is normalized to lowercase UUID form without braces and exposed as `entity.entityId`.

`OBJECTID`, GeoJSON feature order, POI name, and coordinates are not used as stable website identity.

Website-specific metadata is stored separately in:

```text
data/site/poi-meta.json
```

The weekly ArcGIS export must not overwrite this sidecar. It is linked to current Entities by stable ID and is designed to support future Trips, Collections, Routes, travel/research annotations, and publication metadata without modifying the ArcGIS collection schema.

See `docs/stable-id-strategy.md` and `docs/metadata-sidecar.md`.

---

## Documentation

Start with `docs/README.md` for the documentation index.

Key documents include:

- `docs/architecture.md` — system architecture and non-negotiable constraints
- `docs/data-semantics.md` — `POI_Topic`, `POI_Type`, provenance, and extensibility
- `docs/development-workflow.md` — local/GitHub workflow and release discipline
- `docs/entity-model.md` — generic Entity contract
- `docs/stable-id-strategy.md` — GlobalID identity policy
- `docs/metadata-sidecar.md` — website-managed metadata linkage
- `docs/filtering.md` — Topic/Type filter logic
- `docs/detail-panel.md` — Entity Detail Panel behavior
- `docs/multi-geometry-readiness.md` — point/line/polygon architectural readiness
- `docs/qa-pipeline.md` — weekly generated-data QA
- `docs/regression-qa.md` — standalone/embedded release checks

---

## Versioning

Current official release: **1.3.0**.

The v1.3 Foundation release synchronizes `VERSION`, the HTML page title/version metadata, documentation, and release notes. Weekly ArcGIS data refreshes are data updates and do not increment the application version.
