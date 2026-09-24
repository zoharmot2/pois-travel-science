# v1.4 POI Type symbology model

## Purpose

v1.4 changes the primary visual classification from `POI_Topic` to `POI_Type`. The same Type must have a consistent visual identity across Point, Line, and Polygon representations.

`POI_Topic` remains research metadata and is not used to determine the primary map symbol.

## Configuration contract

`config.json` uses:

```json
{
  "symbology": {
    "field": "POI_Type",
    "default": {
      "color": "#64748B",
      "visible": true,
      "label": "Other Type",
      "point": { "shape": "circle", "radius": 7 },
      "line": { "weight": 4, "opacity": 0.85 },
      "polygon": { "weight": 2, "opacity": 0.9, "fillOpacity": 0.18 }
    },
    "types": {}
  }
}
```

Each configured Type may override the common color and point symbol. Geometry-specific settings inherit from the default object when omitted.

## Cross-geometry behavior

For one Type, the configured `color` is shared across geometry families:

- **Point**: SVG marker, with Type-specific point shape/radius.
- **Line**: stroke in the Type color; line width/opacity come from geometry defaults unless overridden.
- **Polygon**: outline and fill in the Type color; polygon opacity/fill opacity come from geometry defaults unless overridden.

This allows a Type such as `River/Lake/Delta` to retain one visual identity whether represented by a Point, Line, or Polygon.

## Extensibility and future domain divergence

The configuration is not a closed vocabulary. If ArcGIS Online later contains a Type that is not configured:

- the Type is included automatically;
- its entities are displayed using the default style;
- it remains filterable;
- Data QA emits `TYPE_STYLE_MISSING`;
- the runtime console emits an English warning.

No automatic aliasing or semantic merging is performed. If two differently spelled or coded values should be treated as equivalent, that must be an explicit future configuration decision.

## Current palette

Stage 4 defines explicit styles for the 12 currently approved `POI_Type` domain values. The palette is a presentation layer only and can be revised without changing ArcGIS Online or the Entity model.

## Transitional UI note

Stage 4 changes the map's visual symbology while retaining the v1.3 dual Topic/Type filter panel for regression safety. Stage 5 will implement the approved UI layout in which POI Type is the main legend, Search/Map Utilities appear below it, and Geometry has a separate Points/Lines/Polygons control.
