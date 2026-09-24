# Filtering model (v1.4 Stage 5)

The Entity model treats `POI_Topic`, `POI_Type`, and geometry family as distinct dimensions with different roles.

## Semantics

- **Research Topic (`POI_Topic`)**: research-project/topic affiliation. `General` means no specific research affiliation.
- **POI Type (`POI_Type`)**: the kind of site/entity. `General Site` means a generic site type and is not a research-project designation.
- **Geometry family**: how the Entity is represented spatially: point, line, or polygon.

## Primary map filtering

From v1.4 Stage 5, the primary map filter is:

`POI_Type AND Geometry family`

Values within the POI Type dimension are combined with OR logic. Geometry-family choices are also combined with OR logic. The two dimensions then combine with AND logic.

Examples:

- `Structure/Building` with all geometry families enabled shows every matching Point, Line, and Polygon.
- `River/Lake/Delta` with only Polygons enabled shows only matching polygon entities.

`POI_Topic` is no longer shown as a primary map legend/filter. It remains preserved in the Entity model, popups/Detail Panel, and future research/analytics workflows.

## Type extensibility

The Type model is configuration-assisted but data-driven:

1. Types defined under `config.json > symbology.types` retain their configured order, label, visibility, color, and point symbol.
2. Any `POI_Type` observed in loaded ArcGIS-derived Entity datasets but missing from configuration is appended automatically.
3. An unconfigured Type remains visible and filterable, uses the default style, and generates a QA/runtime warning.
4. No unknown Type is silently discarded or automatically merged with another value.

This remains valid if Point, Line, and Polygon layers later contain partially different coded-value domains. The website works from the union of observed Types across active datasets.

## Topic extensibility

Research Topic values remain source metadata and do not require a visual-style configuration. Future differences in Topic domains across the ArcGIS layers therefore do not require structural website changes.

## Geometry extensibility

The map UI always knows the three supported geometry families: Points, Lines, and Polygons. A family can have a zero count before its export is activated. Once the corresponding dataset is loaded, the control requires no structural change.
