# v1.3 Standalone + Embedded Regression QA

Stage 10 verifies that the v1.3 foundation work has not regressed the published v1.2 map experience and that every current feature works in both supported display modes.

## Automated static gate

Run from the repository root:

```cmd
py scripts\qa_frontend.py
```

The check is network-independent and validates the source-level contracts for:

- English-only authored frontend UI (`lang="en"`, LTR, no Hebrew in authored HTML/JavaScript)
- Standalone header and embedded `?embed=true` / `?embed=1` behavior
- modular CSS/JavaScript entry points
- five v1.2 basemaps
- POI name search and the Stage 3.1 performance fix
- Day/Night, Time Zones, and coordinate controls
- separate, extensible Research Topic and POI Type filters
- Entity Detail Panel and keyboard close behavior
- GlobalID-based stable IDs
- website metadata sidecar linkage
- future line/polygon Entity/navigation readiness
- no-store/cache-busted JSON loading
- VERSION / page-title consistency

An ERROR returns exit code 1. A WARNING returns exit code 0.

## Manual browser release matrix

Run a local server from the repository root:

```cmd
py -m http.server 8000
```

Test all four combinations below in a current desktop browser. Repeat the mobile-width checks using the browser's responsive device mode or a narrow window.

| Mode | URL | Desktop | Narrow/mobile |
|---|---|---:|---:|
| Standalone | `http://localhost:8000/` | Required | Required |
| Embedded | `http://localhost:8000/?embed=true` | Required | Required |

`?embed=1` should behave identically to `?embed=true`.

## Regression checklist

### A. Initial load

- No fatal error appears in the browser console.
- The map renders and the POI count finishes loading.
- The displayed POI count matches the current unfiltered dataset count reported by data QA.
- Standalone mode shows the page header.
- Embedded mode hides the page header and gives the map the available height.
- The map opens at the configured initial extent.

### B. Basemaps and utilities

Confirm all five basemaps can be selected:

1. OpenStreetMap
2. Satellite (Esri World Imagery)
3. Topographic (Esri Topo)
4. Light (Esri Light Gray)
5. Historic (NatGeo/Esri)

Also verify:

- mouse movement updates the coordinate display
- Day/Night toggles on and off
- Time Zones toggles on and off; if the primary timezone GeoJSON endpoint is unavailable, the existing fallback must not break the map

### C. Research Topic and POI Type filters

- Both filter sections are visible and independently collapsible.
- `All` and `None` work independently in each dimension.
- Multiple values within one dimension behave as OR.
- Topic and Type dimensions combine as AND.
- Counts remain visible beside values.
- Scrolling inside Filters does not zoom the map.
- `POI_Type = Undefined` may appear as a source-data value until corrected in ArcGIS Online; it must not break filtering.
- A POI Type missing explicit config styling remains filterable and uses the default style across geometry families.

### D. Search

Use several queries, including a broad query and a specific POI such as `Stonehenge` if it is still present in the current dataset.

- Typing remains responsive and does not hang.
- Only one best match is opened per search.
- Exact / prefix / partial matching works.
- Enter performs an immediate search.
- Search operates only on entities that remain visible after active Topic/Type filters.

### E. Popup and Detail Panel

For a POI with a description and photographs (for example `Stonehenge` in the development snapshot):

- Popup is concise and contains `View details`.
- `View details` opens the right-hand Detail Panel.
- Topic and Type are correct.
- Description is readable.
- Coordinates and Geometry are shown.
- Field Record values render when present.
- Attachment thumbnails load and open the original attachment.
- Technical details show a Stable Entity ID, ArcGIS OBJECTID, and Source Dataset.
- `×` closes the panel.
- `Esc` closes the panel.
- Filtering the active entity out closes the panel automatically.

### F. Layout modes

Standalone desktop:

- Detail Panel is a right-side sibling of the map and does not cover the main Leaflet controls.
- Opening/closing the panel leaves the map correctly sized.

Embedded desktop:

- Header is absent.
- Filters, search, map controls, popups, and Detail Panel remain usable.
- Detail Panel is compact enough for embedding.

Narrow/mobile width (both modes):

- Detail Panel becomes a bottom overlay.
- The close button remains reachable.
- Filters remain scrollable and do not consume the entire viewport.
- Map controls are still reachable.

### G. Browser console

Warnings that describe known data conditions are acceptable (for example an unstyled new Topic). Treat JavaScript exceptions, failed local JSON loads, duplicate stable-ID errors, or missing required application files as failures.

## Stage 10 acceptance criteria

Stage 10 is complete when:

1. `py scripts\qa_frontend.py` returns PASS or WARNING with 0 errors.
2. `py scripts\qa_data.py` returns PASS/WARNING with 0 errors.
3. The manual matrix passes in Standalone and Embedded modes at desktop and narrow/mobile widths.
4. No v1.2 capability listed above is broken.
5. No Hebrew user-interface text is visible.

This regression matrix is the release gate used for v1.3.0. The official release synchronizes `VERSION` and the page title to 1.3.0 after the matrix passes.
