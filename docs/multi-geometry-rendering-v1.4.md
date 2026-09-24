# v1.4 Stage 7 — Multi-Geometry Rendering

Stage 7 activates the three spatial exports produced by the ArcGIS Online public hosted view:

- `data/pois.geojson` — points (`FeatureServer/0`)
- `data/lines.geojson` — lines (`FeatureServer/1`)
- `data/polygons.geojson` — polygons (`FeatureServer/2`)

All three datasets pass through the same generic Entity model. The map therefore applies the same POI Type filtering, Geometry filtering, search, popup, Detail Panel, stable-ID, and website metadata logic to every geometry family.

## Rendering rules

POI Type remains the primary symbology dimension. A Type uses one configured color across all geometry families.

- **Point** — configured SVG marker shape and color.
- **Line** — configured Type color as the line stroke.
- **Polygon** — configured Type color as outline and transparent fill.

Polygons are rendered in a dedicated `polygonPane` below the dedicated `linePane`. Leaflet point markers remain in the standard marker pane above both vector families. This makes simultaneous rendering predictable and prevents polygon fills from visually covering linework.

## Interaction

All geometry families are interactive. Clicking a point, line, or polygon opens the concise popup. `View details` opens the common Entity Detail Panel. Search uses the same POI name logic across the currently rendered entities: points are centered, while lines and polygons are fit to their bounds.

## Visibility

The UI combines two independent visibility dimensions:

1. **POI Type** — one unified legend over points, lines, and polygons. Turning a Type off hides every geometry with that Type.
2. **Geometry** — separate toggles for Points, Lines, and Polygons.

The Type counts and Geometry counts are derived from all three loaded datasets.

## Source and publication constraints

ArcGIS Online / Field Maps remains authoritative. Stage 7 does not edit ArcGIS schema or data. `POI_Topic` remains research metadata and is not restored to the primary legend.

Attachments are not reimplemented in Stage 7; they continue to use the Stage 6 synchronization rules for points, lines, and polygons.
