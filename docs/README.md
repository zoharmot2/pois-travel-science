# Documentation Index

This directory documents the released v1.3 Foundation architecture and the active v1.4 development work for POIS Travel Science.

## System and data contracts

- [`architecture.md`](architecture.md) — overall architecture, authoritative-source boundary, runtime/build separation, display modes, and future expansion rules.
- [`data-semantics.md`](data-semantics.md) — meaning of `POI_Topic` and `POI_Type`, extensibility rules, and provenance boundaries.
- [`entity-model.md`](entity-model.md) — normalized geometry-independent Entity model.
- [`stable-id-strategy.md`](stable-id-strategy.md) — ArcGIS `GlobalID` as canonical Entity identity.
- [`metadata-sidecar.md`](metadata-sidecar.md) — website-managed metadata linked by stable Entity ID.
- [`multi-geometry-readiness.md`](multi-geometry-readiness.md) — readiness for the existing ArcGIS line and polygon layers.

## User-interface behavior

- [`filtering.md`](filtering.md) — Topic/Type semantics and the v1.4 transition to Type-based primary filtering/symbology.
- [`symbology-v1.4.md`](symbology-v1.4.md) — POI Type visual model shared across Points, Lines, and Polygons.
- [`ui-v1.4.md`](ui-v1.4.md) — integrated Type/Search/Geometry/Map Utilities control layout and responsive behavior.
- [`detail-panel.md`](detail-panel.md) — concise popup plus persistent Entity Detail Panel.

## Development, QA, and release process

- [`development-workflow.md`](development-workflow.md) — local development with GitHub Desktop, local HTTP preview, weekly refreshes, and release discipline.
- [`qa-pipeline.md`](qa-pipeline.md) — generated-data validation integrated into GitHub Actions.
- [`regression-qa.md`](regression-qa.md) — standalone/embedded frontend regression matrix.

## Current release boundary

The current official release is **1.3.0 (Foundation)**. v1.4 development is focused on the UI redesign plus actual Point/Line/Polygon ingestion and display. Analytics, clustering, external enrichment, Trips, Collections, Routes, and public/private publication logic remain later work.

See [`release-1.3.0.md`](release-1.3.0.md) for the release summary.

- [v1.4 Multi-Layer ArcGIS Ingestion](multi-layer-ingestion-v1.4.md) — FeatureServer layers 0/1/2, domain harvesting, and export contract.
