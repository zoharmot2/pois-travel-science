# v1.4 Multi-Dataset QA Contract

Stage 11 strengthens Data QA now that Points, Lines, and Polygons are all active publication datasets.

## Authoritative source

The exporter must harvest all three sublayers from the public hosted view:

`https://services5.arcgis.com/eJYUV73IZAY87Jwy/arcgis/rest/services/POI_Feature_Layer_view/FeatureServer`

- `0` — Points
- `1` — Lines
- `2` — Polygons

The QA layer explicitly checks this source URL so an accidental return to the protected source service is blocked before publication.

## Dataset-to-metadata consistency

`data/derived/layers-metadata.json` is treated as a generated contract rather than informational output only. QA cross-checks it against the three GeoJSON datasets.

For each dataset QA verifies:

- configured layer ID;
- source dataset name;
- geometry family;
- public-view sublayer URL;
- entity count against the GeoJSON feature count;
- availability of the Common Entity fields;
- harvested coded-value domains;
- harvested observed values against the actual exported values;
- attachment/media summary against `attachment_media` in GeoJSON.

An inconsistency between generated metadata and generated GeoJSON is an `ERROR` because the two outputs were produced by the same refresh and must describe the same snapshot.

## Common Entity fields

The required common ArcGIS field contract is:

- `GlobalID`
- `OBJECTID`
- `POI_Name`
- `POI_Type`
- `POI_Topic`
- `POI_Description`
- `Collection_date`
- `Collect_Name`
- `CreationDate`
- `Creator`
- `EditDate`
- `Editor`

The fields must exist in all three ArcGIS sublayers. Their values may be null for individual entities; missing values continue to be handled by the existing data-quality rules.

Layer-specific fields remain valid and are not rejected.

## Domain behavior

The coded-value domains checked in Stage 11 are:

- `POI_Type`
- `POI_Topic`
- `Collect_Name`

The current ArcGIS layers use aligned domains, but alignment is **not** a permanent requirement. Future domain divergence is allowed.

The QA report therefore records, for each domain field:

- values per dataset;
- the union of codes across Points, Lines, and Polygons;
- whether the three coded-value lists are currently aligned.

A difference between layers is informational and does not itself generate a warning or error.

However, an exported nonblank value that is not present in its own layer's current coded-value domain generates `DOMAIN_VALUE_OUTSIDE_CODED_LIST`. This is a warning because it can indicate a legacy stored value after a domain change, as occurred previously with a renamed research-topic value.

Malformed coded-value metadata or duplicate stored codes are errors.

## Attachment/media consistency

Stage 10 introduced structured `attachment_media`. Stage 11 additionally verifies that each dataset's `layers-metadata.json` `attachmentSummary` agrees with the media metadata in the corresponding GeoJSON dataset.

This covers:

- total media references;
- local media;
- remote media;
- image count;
- audio count;
- video count;
- other attachment count.

The existing missing-file and orphan-file protections remain unchanged.

## Publication behavior

The existing weekly/manual GitHub Action already runs `scripts/qa_data.py` after the ArcGIS export. No workflow change is needed for Stage 11. Any new Stage 11 `ERROR` returns exit code `1` and blocks the subsequent automated commit/push. Domain divergence by itself remains allowed.
