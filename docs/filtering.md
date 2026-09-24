# Filtering model (v1.4 Stage 8)

The Entity model treats `POI_Topic`, `POI_Type`, and geometry family as distinct dimensions with different roles.

## Semantics

- **Research Topic (`POI_Topic`)**: research-project/topic affiliation. `General` means no specific research affiliation.
- **POI Type (`POI_Type`)**: the kind of site/entity. `General Site` means a generic site type and is not a research-project designation.
- **Geometry family**: how the Entity is represented spatially: point, line, or polygon.

## Primary map filtering

The primary map filter is:

`POI_Type AND Geometry family`

Values within the POI Type dimension are combined with OR logic. Geometry-family choices are also combined with OR logic. The two dimensions then combine with AND logic.

Examples:

- `Structure/Building` with all geometry families enabled shows every matching Point, Line, and Polygon.
- `River/Lake/Delta` with only Polygons enabled shows only matching polygon entities.

`POI_Topic` is not shown as a primary map legend/filter. It remains preserved in the Entity model, popups/Detail Panel, and future research/analytics workflows.

## Unified cross-filter counts

Stage 8 makes the two visible filter dimensions interact without changing their logical meaning:

- Each **POI Type count** is recalculated from the currently enabled Geometry families.
- Each **Geometry count** is recalculated from the currently enabled POI Types.
- The panel summary reports `Showing X of Y entities` after every filter change.
- The standalone header shows the total entity count when unfiltered and `X / Y entities` when a filter is active.

The count next to a disabled item therefore still indicates how many entities would be available if that item were re-enabled under the current selection in the opposite dimension.

## Missing POI Type values

A blank/null source `POI_Type` is not converted to `General Site` and is never silently repaired. Stage 8 exposes such records through a UI-only **Unspecified** Type bucket.

- The Entity's ArcGIS-derived `POI_Type` remains unchanged.
- `Unspecified` uses the default symbology.
- It can be enabled/disabled like any other Type.
- Existing Data QA warnings for missing `POI_Type` remain authoritative and should be resolved in ArcGIS Online when appropriate.
- The synthetic `Unspecified` bucket is not treated as a new unconfigured ArcGIS domain value.

## All / None actions

Both filter sections provide independent `All` and `None` actions:

- **POI Types — All / None** affects every current Type, including data-driven and Unspecified values.
- **Geometry — All / None** affects Points, Lines, and Polygons.

This allows fast isolation of a subset without conflating Type with geometry representation.

## Type extensibility

The Type model is configuration-assisted but data-driven:

1. Types defined under `config.json > symbology.types` retain their configured order, label, visibility, color, and point symbol.
2. Any `POI_Type` observed in loaded ArcGIS-derived Entity datasets but missing from configuration is appended automatically.
3. An unconfigured Type remains visible and filterable, uses the default style, and generates a QA/runtime warning.
4. No unknown Type is silently discarded or automatically merged with another value.
5. Point, Line, and Polygon layers may use partially different coded-value domains in the future; the website works from the union of observed Types across active datasets.

## Topic extensibility

Research Topic values remain source metadata and do not require a visual-style configuration. Future differences in Topic domains across the ArcGIS layers therefore do not require structural website changes.

## Geometry extensibility

The Geometry control contains the three supported geometry families: Points, Lines, and Polygons. Counts are driven by the loaded Entity datasets and the current Type selection.
