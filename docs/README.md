# Documentation Index

This directory documents the current **POIS Travel Science v1.4.0** architecture and preserves earlier foundation/stage documents where they remain useful for historical context.

## Current system and data contracts

- [`architecture.md`](architecture.md) — current multi-geometry architecture, authoritative-source boundary, runtime/build separation, and display modes.
- [`data-semantics.md`](data-semantics.md) — meaning of `POI_Topic` and `POI_Type`, extensibility rules, and provenance boundaries.
- [`entity-model.md`](entity-model.md) — normalized Point/Line/Polygon Entity model.
- [`stable-id-strategy.md`](stable-id-strategy.md) — ArcGIS `GlobalID` as canonical Entity identity.
- [`metadata-sidecar.md`](metadata-sidecar.md) — website-managed metadata linked by stable Entity ID.
- [`multi-layer-ingestion-v1.4.md`](multi-layer-ingestion-v1.4.md) — FeatureServer layers 0/1/2, domain harvesting, and export contract.
- [`multi-geometry-rendering-v1.4.md`](multi-geometry-rendering-v1.4.md) — active Point/Line/Polygon rendering model.

## User-interface behavior

- [`filtering.md`](filtering.md) — primary `POI_Type AND Geometry` filtering and dynamic counts.
- [`symbology-v1.4.md`](symbology-v1.4.md) — shared Type visual model across Points, Lines, and Polygons.
- [`ui-v1.4.md`](ui-v1.4.md) — integrated Type/Search/Geometry/Map Utilities layout and responsive behavior.
- [`detail-panel.md`](detail-panel.md) — current geometry-aware Entity Detail Panel behavior.
- [`search-detail-v1.4.md`](search-detail-v1.4.md) — multi-result multi-geometry search and navigation.
- [`media-attachments-v1.4.md`](media-attachments-v1.4.md) — image/audio/video/other media synchronization, rendering, and QA.

## Development, QA, and release process

- [`development-workflow.md`](development-workflow.md) — local development with GitHub Desktop, local HTTP preview, weekly refreshes, and release discipline.
- [`qa-pipeline.md`](qa-pipeline.md) — generated-data validation integrated into GitHub Actions.
- [`multi-dataset-qa-v1.4.md`](multi-dataset-qa-v1.4.md) — cross-dataset metadata/domain/media QA.
- [`regression-qa.md`](regression-qa.md) — Standalone/Embedded desktop/mobile release matrix.
- [`release-1.4.0.md`](release-1.4.0.md) — v1.4.0 release summary and final release procedure.

## Historical/reference documents

The following remain useful as development history but do not define the current publication scope:

- [`release-1.3.0.md`](release-1.3.0.md) — v1.3 Foundation release.
- [`multi-geometry-readiness.md`](multi-geometry-readiness.md) — v1.3 readiness work that preceded active v1.4 publication.
- `v1.4-checkpoint-stage*.md` — implementation checkpoints retained for traceability.

## Current release boundary

The current official release is **1.4.0 — Multi-Geometry UI**. Points, Lines, and Polygons are active. `POI_Type` is the primary visual/filtering axis; `POI_Topic` remains research metadata. Analytics, clustering, external enrichment, Trips, Collections, Routes, public/private publication builds, and SEO/public discovery remain later roadmap work.
