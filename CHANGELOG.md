# Changelog

## 1.4.0 — Multi-Geometry UI

- Activated simultaneous Point, Line, and Polygon export/publication.
- Switched primary map symbology/legend to `POI_Type`.
- Added separate Geometry controls and unified Type × Geometry filtering.
- Added dynamic cross-filter counts and `Unspecified` handling for blank Types.
- Added multi-result, multi-geometry search with keyboard navigation.
- Refined geometry-aware Detail Panel behavior.
- Added local image/audio synchronization for Lines and Polygons as well as Points.
- Added structured media metadata and video/other remote-link handling.
- Added attachment cleanup safeguards and Git persistence checks.
- Added per-layer metadata/domain harvesting and multi-dataset QA.
- Expanded Standalone/Embedded desktop/mobile regression QA.

## 1.3.0 — Foundation

- Modularized the frontend.
- Added generic Entity model and normalized GlobalID stable identity.
- Added website metadata sidecar.
- Added filtering, Detail Panel, multi-geometry readiness, data QA, frontend QA, and formal Standalone/Embedded modes.

## 1.5.0 — Data Enrichment (implementation candidate)

- Added an incremental, GlobalID-keyed, non-destructive enrichment pipeline.
- Added rate-limited Nominatim reverse geocoding of point features, with per-record administrative location, source citations and timestamps.
- Recorded OSM nearest-feature identity only as an **unverified candidate**, never a verified match inferred from proximity alone.
- Added manual candidate approvals in `data/site/enrichment-reviews.json`; provenance is preserved.
- Extended standalone/embedded detail panels with concise External Geographic Information and Enrichment Notes sections.
- Extended GitHub Actions with incremental enrichment, QA, and persistent output artifacts.
- Corrected 13 archived attachment filenames whose ZIP names used `#U...` substitutions, to match the existing references.
- Network enrichment is inactive until a contactable `ENRICHMENT_USER_AGENT` is configured; no live external retrieval was performed in this release package.
- The OSM feature matching/scoring module described in the full specification requires additional implementation and live validation before v1.5.0 can be declared fully accepted.
