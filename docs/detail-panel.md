# Entity Detail Panel — v1.4.0

The Detail Panel provides a persistent Entity-centric view while the Leaflet popup remains concise.

## Interaction model

1. Selecting a Point, Line, or Polygon opens a concise popup.
2. **View details** opens the persistent Detail Panel.
3. Search-result selection can open/focus the same Entity directly.
4. The panel can be closed with the close button or `Escape`.
5. If the open Entity becomes hidden by the active Type × Geometry filters, the panel closes rather than showing an Entity that is no longer present on the map.

## Common content

The panel may show:

- Entity name, with geometry-specific fallback such as `Unnamed Line`;
- Description;
- `POI_Type`;
- Research Topic (`POI_Topic`);
- collection date and collector;
- ArcGIS creation/edit information when present;
- geometry family;
- source dataset;
- attachments/media;
- collapsible technical identifiers/details.

Blank Type/Topic values may be displayed as `Unspecified` for readability without modifying the underlying ArcGIS value.

## Geometry-specific location content

### Point

Shows the actual Point coordinates.

### Line / Polygon

Shows:

- geometry family/type;
- derived map center for navigation/display;
- geographic extent/bounds;
- source dataset.

The derived center is an interface helper and must not be described or used as a scientific centroid.

## Media sections

Media is grouped by kind when metadata is available:

- **Photos** — local thumbnails with links to the full local file;
- **Audio** — local HTML5 audio player plus file link;
- **Other Attachments** — remote video and other unsupported media links.

The UI prefers structured `attachment_media`/`attachmentMedia` metadata and falls back to the legacy attachment URL list for backward compatibility.

## Standalone and Embedded behavior

Desktop Standalone mode displays the panel beside the map. Embedded mode uses a more compact desktop width. On narrow/mobile screens, both modes use a bottom overlay so map space remains available.

## Provenance boundary

The Detail Panel displays existing ArcGIS-derived and website-managed information only. It does not edit ArcGIS attributes. Future Trips, Collections, Routes, enrichment, analytics, and publication controls must preserve their own provenance rather than being silently written into ArcGIS fields.
