# Data Semantics and Extensibility

## `POI_Topic`

`POI_Topic` represents **research-project or research-topic affiliation**.

The special value:

```text
General
```

means that the Entity has **no specific research affiliation**. It must not be interpreted as a research project in its own right.

The set of Topic values is expected to evolve over time as research activity changes.

## `POI_Type`

`POI_Type` is an independent classification axis describing **what kind of entity/site the record represents**.

The special value:

```text
General Site
```

means a generic site type. It does not indicate whether the record is research-related.

A POI can therefore combine any valid Topic and Type independently.

Example:

```text
POI_Topic = Historical Earthquakes
POI_Type  = Structure/Building
```

## Extensibility rule

Neither field is a hard-coded closed list in the website architecture.

### New Topic values

When a new `POI_Topic` appears in exported ArcGIS data:

- it must appear automatically in the Research Topics filter;
- it must remain selectable/filterable;
- if `config.json` has an explicit Topic style, that style is used;
- otherwise the default configured marker style is used;
- data QA emits `TOPIC_STYLE_MISSING` as a WARNING until an explicit style is added, if desired.

A Topic must never disappear from the site solely because a style entry is missing.

### New Type values

`POI_Type` filter values are derived from the loaded Entity dataset. A new Type therefore appears automatically after data refresh and requires no structural frontend change.

Placeholder-like values such as `Undefined` are not silently corrected by the website. Data QA flags them for review in ArcGIS Online, which remains authoritative.

## Code versus display label

ArcGIS coded-value domains may distinguish between stored Code and displayed Label. The website must match exported source values correctly and should not assume that changing an ArcGIS Label necessarily rewrites existing stored record values.

When a Topic is renamed in ArcGIS, confirm that existing feature values have migrated to the intended stored Code before removing legacy website configuration. Otherwise the data-driven filter correctly exposes both old and new source values.

## Stable identity

Classification values are attributes, not identifiers.

The website never uses Topic, Type, name, coordinates, or `OBJECTID` as canonical identity. Entity relationships use normalized ArcGIS `GlobalID` through `entity.entityId`.

## Provenance boundary

ArcGIS-authored fields remain authoritative source attributes.

Website-managed or externally derived attributes must remain distinguishable from source attributes. Current website-managed metadata lives in:

```text
data/site/poi-meta.json
```

Future external enrichment should retain source, retrieval time, external identifier, matching method, and confidence where applicable.

## Geometry independence

The Topic/Type semantics apply to all geometry families. When line and polygon exports are activated later, their Entities should participate in the same classification, stable-ID, filtering, and QA contracts unless their ArcGIS schemas require an explicitly reviewed mapping.
