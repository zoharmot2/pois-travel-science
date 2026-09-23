# Documentation Index

This directory documents the v1.3 Foundation architecture and operating workflow for POIS Travel Science.

## System and data contracts

- [`architecture.md`](architecture.md) — overall architecture, authoritative-source boundary, runtime/build separation, display modes, and future expansion rules.
- [`data-semantics.md`](data-semantics.md) — meaning of `POI_Topic` and `POI_Type`, extensibility rules, and provenance boundaries.
- [`entity-model.md`](entity-model.md) — normalized geometry-independent Entity model.
- [`stable-id-strategy.md`](stable-id-strategy.md) — ArcGIS `GlobalID` as canonical Entity identity.
- [`metadata-sidecar.md`](metadata-sidecar.md) — website-managed metadata linked by stable Entity ID.
- [`multi-geometry-readiness.md`](multi-geometry-readiness.md) — readiness for the existing ArcGIS line and polygon layers.

## User-interface behavior

- [`filtering.md`](filtering.md) — independent Research Topic and POI Type filtering.
- [`detail-panel.md`](detail-panel.md) — concise popup plus persistent Entity Detail Panel.

## Development, QA, and release process

- [`development-workflow.md`](development-workflow.md) — local development with GitHub Desktop, local HTTP preview, weekly refreshes, and release discipline.
- [`qa-pipeline.md`](qa-pipeline.md) — generated-data validation integrated into GitHub Actions.
- [`regression-qa.md`](regression-qa.md) — standalone/embedded frontend regression matrix.

## Current release boundary

The current official release is **1.3.0 (Foundation)**. Actual line/polygon export, analytics, clustering, external enrichment, Trips, Collections, Routes, and public/private publication logic remain later work.

See [`release-1.3.0.md`](release-1.3.0.md) for the release summary.
