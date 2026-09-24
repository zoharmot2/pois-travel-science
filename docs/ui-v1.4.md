# v1.4 Map User Interface

Version 1.4 reorganizes the map interface around the meaning of the data rather than around the ArcGIS source layer.

## Primary visual hierarchy

The integrated left-side map control follows this order:

1. **POI Types** — primary legend and visibility control.
2. **Search** — multi-result name search across currently visible Entities.
3. **Geometry** — independent visibility controls for Points, Lines, and Polygons.
4. **Map Utilities** — Day/Night, Time Zones, and live cursor coordinates.

`POI_Topic` is intentionally not part of the primary legend. It remains research metadata in the Entity model and Detail Panel and is reserved for future research/analytics functions.

## POI Type legend

The legend is data-driven across all active Entity datasets. A single Type count therefore represents matching Points, Lines, and Polygons under the currently active Geometry selection.

Turning a Type off hides every Entity with that `POI_Type`, regardless of geometry family.

The Type swatch communicates the shared Type color. Geometry is communicated by the rendered feature and the separate Geometry control.

Unknown/new ArcGIS Type values remain visible and filterable with the default style and generate QA/runtime warnings until explicit presentation is configured.

Blank/null source Types remain unmodified but are exposed through the UI-only **Unspecified** bucket so they can be controlled explicitly.

## Geometry control

Geometry is a separate visibility dimension:

- Points
- Lines
- Polygons

All three are enabled by default. Geometry counts are recalculated against the currently enabled POI Types. Type and Geometry combine with AND logic.

Each filter section provides independent `All | None` actions.

## Search

Search is located immediately below the Type legend and is constrained to Entities currently visible after Type × Geometry filtering.

The v1.4 search behavior:

- 180 ms debounce;
- up to eight ranked results;
- exact name matches before starts-with and contains matches;
- result rows identify geometry family and may show Type/Topic context;
- `Arrow Up` / `Arrow Down` navigate results;
- `Enter` selects a result;
- `Escape` closes the result list.

Navigation is geometry-aware:

```text
Point   → center/zoom
Line    → fitBounds
Polygon → fitBounds
```

Selecting a result opens/focuses the Entity and its Detail Panel.

## Map utilities

Day/Night and Time Zones are grouped under **Map Utilities**. Live cursor coordinates are displayed in the same section.

## Responsive and Embedded behavior

The same codebase serves Standalone and Embedded modes. Embedded mode hides the global header and uses a more compact control/detail layout. At viewport widths of 700 px or less, the map control can collapse and the Detail Panel becomes a bottom overlay so map space remains usable.

The release regression matrix validates both display modes at desktop and narrow/mobile widths.
