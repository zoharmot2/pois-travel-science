# v1.4 Standalone + Embedded Full Regression QA

Stage 12 is the browser-facing release gate for the complete v1.4 interface. It verifies that the site behaves correctly with Points, Lines, and Polygons in both supported presentation modes and at desktop and narrow/mobile widths.

The automated static QA is necessary but not sufficient. Stage 12 is complete only after the manual four-mode browser matrix passes.

## Automated gates

From the repository root in Command Prompt:

```cmd
py scripts\qa_data.py
py scripts\qa_frontend.py
```

Publication-level expectation:

```text
Data QA: 0 Errors
Frontend regression QA: PASS (0 Errors)
```

Known source-data quality warnings such as blank names, blank Topic, or blank Type may remain warnings. They must not be confused with application failures.

The frontend static gate verifies the v1.4 source contracts for:

- English-only authored UI and LTR layout;
- Standalone header and `?embed=true` / `?embed=1` behavior;
- desktop and narrow/mobile layout contracts;
- five basemaps and existing map utilities;
- active Point, Line, and Polygon datasets;
- POI Type primary symbology and legend;
- independent Geometry controls;
- unified Type + Geometry filtering and dynamic counts;
- multi-result search and keyboard navigation;
- geometry-aware map focus;
- Detail Panel behavior and responsive placement;
- structured image/audio/video/other attachment presentation;
- GlobalID stable IDs, sidecar metadata, cache busting, and required files.

## Browser matrix

Start the site locally:

```cmd
py -m http.server 8000
```

Run every required cell below in a current browser. For narrow/mobile, use browser responsive-device mode or resize the viewport to 700 px wide or less.

| Mode | URL | Desktop | Narrow/mobile |
|---|---|---:|---:|
| Standalone | `http://localhost:8000/` | Required | Required |
| Embedded | `http://localhost:8000/?embed=true` | Required | Required |

Also verify once that:

```text
http://localhost:8000/?embed=1
```

behaves identically to `?embed=true`.

## 1. Initial load and dataset integrity

For each required matrix cell:

- The map renders without a fatal error.
- The entity count finishes loading rather than remaining on `Loading...`.
- The total entity count matches the current Data QA report, not a hard-coded historical count.
- Point, Line, and Polygon data all load when present in the current ArcGIS snapshot.
- No required local JSON file returns 404 in the browser console/network panel.
- The configured initial extent is sensible and the map remains interactive.

Standalone mode must show the page header and entity-count badge. Embedded mode must hide the header and use the available viewport height for the application.

## 2. Main control panel

The control panel must appear in this order:

```text
Map Controls
  POI Types
  Search
  Geometry
  Map Utilities
```

Confirm:

- `POI Types` is the only primary classification legend.
- Research Topic is not displayed as a main map filter; it remains Entity metadata.
- `All` and `None` work for POI Types.
- `All` and `None` work independently for Geometry.
- Geometry contains Points, Lines, and Polygons.
- An `Unspecified` Type bucket appears only when current source data contains a blank `POI_Type`.
- A new unconfigured Type remains visible/filterable using fallback symbology.
- Scrolling inside the control panel does not unexpectedly zoom the map.

## 3. Unified filtering and counts

The effective visibility rule must remain:

```text
POI Type AND Geometry
```

Test at least the following sequence:

1. Start with all Types and all Geometry enabled.
2. Disable Points: only Lines and Polygons remain; Type counts recalculate for the active geometries.
3. Re-enable Points and disable Lines: line features disappear and search no longer returns lines.
4. Re-enable Lines and disable one populated POI Type: all Point/Line/Polygon entities of that Type disappear.
5. Use Geometry `None`, then `All`.
6. Use POI Type `None`, then `All`.

The summary must update, for example:

```text
Showing 84 of 1206 entities
```

The exact numbers are data-dependent and may change after weekly ArcGIS synchronization.

## 4. Multi-geometry rendering and symbology

Inspect at least one visible entity from every geometry family currently present.

- Point uses the configured Type color/point shape.
- Line uses the same Type color as its stroke.
- Polygon uses the same Type color for outline and translucent fill.
- Points remain visually above Lines and Polygons where features overlap.
- Lines remain above Polygons.
- Pan/zoom does not detach or duplicate vector features.

## 5. Search

Use a specific query and a broader query that returns multiple current entities.

Confirm:

- Search remains responsive with the 180 ms debounce.
- Up to eight ranked results are shown.
- Each result identifies Point, Line, or Polygon.
- Result metadata includes Type and Topic when available.
- `Arrow Up` / `Arrow Down` move through results.
- `Enter` selects the active result.
- `Escape` closes the result list.
- Search only considers entities currently visible after Type + Geometry filtering.
- Selecting a Point centers/zooms appropriately.
- Selecting a Line or Polygon uses its bounds rather than treating it as a point.
- The selected Entity opens in the Detail Panel.

## 6. Popup and Detail Panel

Test a Point, a Line, and a Polygon where current data permits.

Confirm:

- Popup remains concise and offers `View details`.
- Detail Panel title uses the Entity name, or `Unnamed Point`, `Unnamed Line`, or `Unnamed Polygon` when the name is blank.
- POI Type and Research Topic are displayed correctly.
- Blank Type/Topic values display as `Unspecified` without altering ArcGIS data.
- Description and field-record information render when present.
- Point shows real coordinates.
- Line/Polygon show `Map Center (derived)` and `Extent`; the derived map center is not labeled as a scientific centroid.
- Technical details include Stable Entity ID, ArcGIS OBJECTID, Source Dataset, and GeoJSON Geometry.
- `×` closes the panel.
- `Esc` closes the panel.
- Filtering the active Entity out closes the panel automatically.

## 7. Attachments and media

Use current entities with attachments where available, including Line/Polygon attachments if present.

- Photos appear as thumbnails and open the original/local media.
- Audio appears in an HTML5 audio player and the file link is usable.
- Video is presented as a link to the remote ArcGIS attachment, not as a broken image.
- Other unsupported media is presented as a generic attachment link.
- Media belonging to Points, Lines, and Polygons behaves consistently.
- No missing local-media request appears in the console/network panel.

## 8. Basemaps and utilities

Confirm all five basemaps can be selected:

1. OpenStreetMap
2. Satellite (Esri World Imagery)
3. Topographic (Esri Topo)
4. Light (Esri Light Gray)
5. Historic (NatGeo/Esri)

Also verify:

- Day/Night toggles on and off.
- Time Zones toggles on and off; a remote timezone-service failure must not crash the application.
- Coordinate display updates as the pointer moves over the map.

## 9. Standalone and embedded layout

### Standalone desktop

- Header is visible.
- Control panel remains readable and scrollable.
- Opening the Detail Panel creates a right-side sibling of the map.
- Map resizes correctly after opening and closing the panel.

### Embedded desktop

- Header is absent.
- Control panel is more compact than Standalone mode.
- Detail Panel remains usable without consuming the full map.
- Search, filters, utilities, popups, and media remain usable.

### Narrow/mobile — both modes

- Control panel collapse button is visible and works.
- Collapsed state leaves a compact summary rather than covering the map.
- Detail Panel becomes a bottom overlay.
- Detail close button remains reachable.
- Detail content scrolls when necessary.
- Map controls remain reachable around the overlay.
- No horizontal page scrolling is introduced.

## 10. Browser console gate

Acceptable console output includes documented warnings for source-data conditions or a newly observed Type that uses fallback styling.

Treat any of the following as a Stage 12 failure:

- uncaught JavaScript exception;
- failed required local JSON/GeoJSON load;
- duplicate Stable Entity ID error;
- missing required frontend module;
- Point/Line/Polygon dataset failing to load;
- Detail Panel or search interaction throwing an exception;
- attachment/media local-file 404;
- Hebrew authored user-interface text.

## Stage 12 acceptance criteria

Stage 12 is complete only when all of the following are true:

1. `py scripts\qa_data.py` reports 0 Errors.
2. `py scripts\qa_frontend.py` reports 0 Errors.
3. Standalone desktop passes.
4. Standalone narrow/mobile passes.
5. Embedded desktop passes.
6. Embedded narrow/mobile passes.
7. `?embed=1` matches `?embed=true`.
8. Point/Line/Polygon rendering, filtering, search, Detail Panel, and media all pass where relevant current data exists.
9. No blocking browser-console error is present.
10. No Hebrew authored UI text is visible.

After this gate passes, v1.4 can proceed to Stage 13 documentation cleanup and then Stage 14 release preparation.
