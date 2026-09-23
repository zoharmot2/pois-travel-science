# Entity Detail Panel

Version 1.3 Stage 7 introduces an entity-centric Detail Panel while retaining a concise Leaflet popup.

## Interaction model

1. Selecting a marker opens a concise popup with the POI name, Research Topic, POI Type, and a **View details** button.
2. **View details** opens the persistent Detail Panel.
3. The panel can be closed with the close button or the `Escape` key.
4. If the currently open entity is removed from the map by Topic/Type filtering, the Detail Panel closes automatically.

## Panel content

The panel presents existing data only; it does not create or write any ArcGIS attributes. Current sections include:

- Description
- Classification (`POI_Topic`, `POI_Type`)
- Location (coordinates and geometry type)
- Field Record (collection date, collector, ArcGIS creation/edit dates when available)
- Attachments / photographs
- Collapsible technical details (stable Entity ID and ArcGIS OBJECTID)

Website-managed metadata remains separate in `entity.websiteMetadata` and is not exposed by Stage 7 because no public metadata fields have yet been defined.

## Standalone and embedded behavior

Desktop standalone mode displays the panel beside the map so the map remains usable. The map is resized after the panel opens/closes.

Embedded mode uses the same component with a slightly more compact width. On narrow screens the panel becomes a bottom overlay to preserve map space.

## Scope boundary

Stage 7 does not add Trips, Collections, Routes, external enrichment, analytics, editing, or public/private publication rules. The panel is designed so those capabilities can be added later without changing the core Entity model.
