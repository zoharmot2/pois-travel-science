# Filtering model (v1.3 Stage 6)

The website treats `POI_Topic` and `POI_Type` as two independent classification dimensions.

## Semantics

- **Research Topic (`POI_Topic`)**: research-project/topic affiliation. `General` means no specific research affiliation.
- **POI Type (`POI_Type`)**: the kind of site/entity. `General Site` means a generic site type and is not a research-project designation.

Within one dimension, enabled values are combined with **OR** logic. The Topic and Type dimensions are combined with **AND** logic.

Example: enabling only `Historical Earthquakes` under Research Topics and only `Structure/Building` under POI Types shows entities that satisfy both conditions.

## Extensibility

The filter UI is data-driven.

### New POI_Topic values

Configured topics retain their configured marker style and order. If ArcGIS data contains a new `POI_Topic` that is not yet present in `config.json`, the value:

1. appears automatically in the Research Topics filter after the next data refresh;
2. remains visible by default;
3. uses the default marker symbology from `config.json`; and
4. produces an English console warning so a dedicated style can be added later if desired.

The new value is never silently omitted because of missing symbology configuration.

### New POI_Type values

`POI_Type` filter values are derived from the current Entity dataset. A new type added in ArcGIS therefore appears automatically after the next data refresh without a structural code change.

## Counts

The number shown beside each filter value is the count in the full currently loaded dataset. Counts are informational and do not change when other filters are toggled in Stage 6.

## Scope

Stage 6 filters the currently loaded point entities. The filter architecture operates on the generic Entity model and is therefore ready to be reused when line and polygon layers are activated in a later release.
