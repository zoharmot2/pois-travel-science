# Release 1.3.0 — Foundation

## Purpose

Version 1.3.0 is the Foundation release for POIS Travel Science. It preserves the existing ArcGIS Online / Field Maps collection workflow and the static Leaflet deployment model while restructuring the website so later research, travel-journal, analytical, multi-geometry, and public-discovery features can be added without destabilizing the authoritative collection system.

## Highlights

- Modular static frontend (`css/` + `js/`) replacing the previous monolithic page structure.
- Generic geometry-independent Entity model with conceptual Point, Line, and Polygon support.
- ArcGIS `GlobalID` adopted as the canonical stable Entity ID.
- Website-managed metadata sidecar linked by stable ID and kept separate from ArcGIS-authored attributes.
- Independent, extensible Research Topic (`POI_Topic`) and POI Type (`POI_Type`) filters.
- Data-driven fallback behavior for newly introduced Topic/Type values.
- Concise map popup plus a richer Entity Detail Panel.
- Search performance fix using debounced single-best-match behavior.
- Geometry-aware navigation and rendering readiness for future line/polygon exports.
- Automated generated-data QA integrated into the weekly/manual GitHub Actions workflow.
- Automated static frontend regression QA.
- Formal Standalone and Embedded display modes from one codebase.
- English-only authored user interface.
- Expanded architecture, data-semantics, QA, and development documentation.

## Data-source boundary

ArcGIS Online / Field Maps remains authoritative. Version 1.3.0 does not require disruptive ArcGIS schema changes and does not write website metadata back to ArcGIS.

## Current spatial publication scope

Only the point dataset is currently exported and published by the website. Existing ArcGIS line and polygon collection layers remain future data sources. The Entity model, client data-source layer, map navigation logic, and QA configuration are already prepared for their later activation.

## Deferred beyond v1.3.0

The following are intentionally outside this release:

- full research analytics dashboard;
- analytical clustering / DBSCAN;
- OpenStreetMap / Nominatim enrichment;
- Trips and travel timeline;
- active Collections and Routes;
- natural-disaster route integration;
- public/private build separation;
- SEO/public discovery pages;
- advanced analytical export;
- actual line/polygon export and publication;
- a new backend/database or heavy frontend framework.

## Release validation

Before tagging the release:

1. Run `py scripts\qa_frontend.py` locally and confirm 0 errors.
2. Confirm the Standalone and Embedded browser regression matrix in `docs/regression-qa.md`.
3. Commit and push the release-version changes.
4. Manually run `Sync ESRI Data Weekly` in GitHub Actions.
5. Confirm Data QA has 0 errors and Frontend Regression QA has 0 errors. Warnings may remain only when they describe understood source-data conditions.
6. Confirm the live site displays the expected current data and version.
7. Create the Git tag / GitHub Release `v1.3.0`.
