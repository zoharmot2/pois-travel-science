# v1.4 map user interface

Version 1.4 reorganizes the map interface around the meaning of the data rather than around the ArcGIS source layer.

## Primary visual hierarchy

The integrated left-side map control follows this order:

1. **POI Types** — the primary legend and visibility control.
2. **Search** — name search across the currently rendered entities.
3. **Geometry** — independent visibility controls for Points, Lines, and Polygons.
4. **Map Utilities** — Day/Night, Time Zones, and live cursor coordinates.

`POI_Topic` is intentionally not part of the primary legend. It remains research metadata in the Entity model and Detail Panel and is reserved for future research/analytics functions.

## POI Type legend

The legend is data-driven. Counts are calculated across every loaded Entity dataset, so once line and polygon ingestion is active a single Type count represents the combined number of matching Points, Lines, and Polygons.

Turning a Type off hides every Entity with that `POI_Type`, regardless of geometry family.

The Type swatch communicates the shared Type color. Geometry itself is communicated by the rendered feature and by the separate Geometry control, avoiding a legend that implies that a Type belongs only to points.

Unknown/new ArcGIS Type values remain visible and filterable with the default style and generate QA/runtime warnings until explicit presentation is configured.

## Geometry control

Geometry is a separate visibility dimension:

- Points
- Lines
- Polygons

All three are enabled by default. During Stage 5 only the currently exported point dataset has a non-zero count. The control is already geometry-independent so the counts and filtering will update automatically once line and polygon datasets are loaded in later v1.4 stages.

Type and Geometry combine with AND logic. For example, enabling only `River/Lake/Delta` and `Polygons` will show only polygon entities with that Type once polygon data is active.

## Search and utilities

Search is located immediately below the Type legend and retains the debounced single-best-result behavior introduced during v1.3. Search works on currently rendered entities, so Type and Geometry visibility constrain the searchable set.

Day/Night and Time Zones are grouped under **Map Utilities**. Live cursor coordinates are displayed in the same section.

## Responsive and embedded behavior

The same codebase serves standalone and embedded modes. The map panel is slightly narrower in embedded mode. At viewport widths of 700 px or less, the panel can collapse to a compact header so the map remains usable on narrow screens.

The Entity Detail Panel remains independent of the left map-control panel and retains its desktop, embedded, and bottom-overlay mobile behavior.
