# Release 1.4.0 — Multi-Geometry UI

## Purpose

Version 1.4.0 converts the multi-geometry readiness established in v1.3 into an active production workflow. The website now exports, validates, renders, filters, searches, and inspects Point, Line, and Polygon Entities together while preserving ArcGIS Online / Field Maps as the authoritative collection system.

## Highlights

- Active multi-layer export from the public Hosted Feature Layer View:
  - `/0` Points → `data/pois.geojson`
  - `/1` Lines → `data/lines.geojson`
  - `/2` Polygons → `data/polygons.geojson`
- Shared `POI_Type` color semantics across Point/Line/Polygon rendering.
- Primary map legend simplified to **POI Type**; Research Topic remains metadata.
- Separate Geometry controls for Points, Lines, and Polygons.
- Unified `POI_Type AND Geometry` filtering with dynamic cross-filter counts.
- UI-only `Unspecified` bucket for blank Type values without source-data rewriting.
- Multi-result search across visible Entities, keyboard navigation, and geometry-aware focus.
- Detail Panel refined for Point coordinates and Line/Polygon extent/derived map center.
- Images and audio synchronized locally for all three geometry families.
- Video and unsupported media retained as remote ArcGIS references.
- Structured attachment-media metadata and media-specific rendering.
- Attachment cleanup removes files no longer referenced after a successful refresh.
- Per-layer metadata/domain harvesting and multi-dataset QA.
- Source-view validation prevents accidental use of the protected non-view Feature Service.
- Standalone and Embedded layouts regression-tested on desktop and narrow/mobile widths.
- English-only authored UI preserved.

## Authoritative-source boundary

No disruptive ArcGIS schema change is required. ArcGIS Online / Field Maps remains authoritative. The website continues to adapt around the existing collection workflow and does not write website-owned metadata back to ArcGIS.

## Current publication scope

All three geometry families are active:

```text
Points
Lines
Polygons
```

The exact Entity/attachment counts are data-snapshot values and may change during normal weekly refreshes; they are not release-version constants.

## Filtering and classification

`POI_Type` is the primary visual/filter axis in v1.4.0. A selected Type applies consistently to Points, Lines, and Polygons. Geometry visibility is controlled independently.

`POI_Topic` remains research-project/topic metadata and is retained for Detail Panel display and later analytical workflows.

## Media policy

```text
Image → local
Audio → local
Video → remote ArcGIS URL
Other unsupported media → remote ArcGIS URL
```

Cleanup is fail-safe: if attachment querying/downloading fails, the refresh fails before stale-file cleanup runs.

## QA and release validation

The v1.4.0 release gate includes:

- `py scripts\qa_data.py`
- `py scripts\qa_frontend.py`
- full manual Standalone/Embedded desktop/mobile matrix in `docs/regression-qa.md`
- post-push manual GitHub Actions run
- confirmation that Data QA has 0 errors
- confirmation that Frontend Regression QA has 0 errors

Known source-data warnings may remain when explicitly understood and non-blocking; they should be corrected in ArcGIS Online when appropriate.

## Deferred beyond v1.4.0

Intentionally deferred:

- full research analytics dashboard;
- DBSCAN/analytical clustering;
- OSM/Nominatim or other external enrichment;
- Trips and travel timeline;
- active Collections and Routes;
- natural-disaster route product integration;
- public/private build separation;
- SEO/public discovery pages;
- advanced analytical exports;
- a new backend/database or heavy frontend framework.

## Release procedure

1. Apply the final v1.4.0 release patch.
2. Confirm `VERSION` and the HTML title are `1.4.0`.
3. Run local data/frontend QA.
4. Confirm the application loads in Standalone and Embedded modes.
5. Commit to `main` with `Release v1.4.0`.
6. Push origin.
7. Run **Sync ESRI Data Weekly** manually in GitHub Actions.
8. Confirm 0 Data QA errors and 0 Frontend Regression QA errors.
9. Confirm the live site/repository reflects v1.4.0.
10. Create tag `v1.4.0` from the release commit and publish the GitHub Release.
