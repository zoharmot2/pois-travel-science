# v1.4 Multi-Layer ArcGIS Ingestion

Version 1.4 activates export of all three authoritative ArcGIS Online sublayers from a single hosted FeatureServer:

| Dataset | ArcGIS layer | Geometry family | Website output |
| --- | ---: | --- | --- |
| Points | `FeatureServer/0` | point | `data/pois.geojson` |
| Lines | `FeatureServer/1` | line | `data/lines.geojson` |
| Polygons | `FeatureServer/2` | polygon | `data/polygons.geojson` |

Base service:

`https://services5.arcgis.com/eJYUV73IZAY87Jwy/arcgis/rest/services/POI_Feature_Layer_view/FeatureServer`

## Design rules

- ArcGIS Online / Field Maps remains authoritative. The export does not alter fields, domains, relationships, or collection workflows.
- The same ingestion code path is used for all three sublayers.
- Each layer is queried with pagination and exported as WGS84 GeoJSON.
- The exporter validates the expected ArcGIS geometry type before accepting a layer.
- All source properties are preserved. The shared Entity fields are not used to discard layer-specific attributes.
- `GlobalID` remains the canonical website stable ID; uniqueness across datasets is enforced by Data QA.
- Point CSV/PDF products remain point-based for backward compatibility.
- Attachment synchronization is active across Points, Lines, and Polygons. Images and audio are downloaded locally; video/other media remain direct ArcGIS URLs.

## Common Entity fields

The current shared field contract is:

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

The exporter records field availability rather than assuming the domains will always stay identical across layers.

## Domain and schema harvesting

Every export also writes:

`data/derived/layers-metadata.json`

This contains, per dataset:

- ArcGIS layer ID/name/source URL
- geometry family and ArcGIS geometry type
- entity count
- attachment support
- `maxRecordCount`
- object/global ID field names
- available field names
- availability of the common Entity fields
- coded-value domains for `POI_Type`, `POI_Topic`, and `Collect_Name`
- values actually observed in the exported features

The website can therefore derive future cross-layer catalogues from ArcGIS rather than assuming that coded domains always remain identical.

## Publication safety

All three layers are fetched and processed before GeoJSON output files are rewritten. A sublayer failure therefore raises an error rather than silently publishing a partially refreshed three-layer snapshot. The GitHub Actions Data QA stage then treats points, lines, and polygons as required datasets and validates geometry families and stable IDs before commit/push.

## Stage boundary

Stage 6 produces and validates the multi-layer files. It does **not** yet activate line/polygon loading in the browser. Rendering begins in Stage 7, using the multi-geometry Entity architecture prepared in v1.3.

## Attachment synchronization and deletion semantics

Stage 6.2 extends attachment synchronization to all three datasets.

- Image and audio attachments are downloaded locally for points, lines, and polygons.
- Existing point media keep the historical `data/attachments/<OBJECTID>_<attachmentId>_<name>` path to avoid a mass rewrite.
- New line media are stored under `data/attachments/lines/` and polygon media under `data/attachments/polygons/` so attachment/object IDs from different ArcGIS sublayers cannot collide.
- Media other than images and audio (for example video) remain direct public ArcGIS attachment URLs rather than local copies. Stage 10 additionally exports structured `attachment_media` metadata so the browser and QA do not need to infer media type from a URL alone.
- Attachment metadata retrieval and local image/audio download failures abort the refresh. The exporter never interprets a failed ArcGIS attachment request as an empty attachment set.

The export is a synchronization, not an append-only archive. Every successful run builds the current attachment reference set from the authoritative AGOL view and then removes local image files that are no longer referenced. Therefore:

- deleting an entity in AGOL removes it from the rewritten GeoJSON output;
- all locally cached image/audio attachments that belonged only to that deleted entity are removed;
- deleting an image/audio attachment from a surviving AGOL entity removes the local copy on the next successful refresh;
- GitHub Actions stages these file deletions because it commits `data/` with `git add data/`.

### Downloaded media types

The local static archive downloads both image and audio media. Audio detection uses either the ArcGIS attachment MIME type (`audio/*`) or common audio filename extensions such as `.mp3`, `.wav`, `.m4a`, `.aac`, `.ogg`, `.flac`, `.opus`, `.aiff`, `.amr`, and `.m4b`. Audio files are preserved byte-for-byte and are not transcoded. Video and other unsupported media remain direct ArcGIS URLs.

Website-managed metadata sidecar records are intentionally not auto-deleted when an ArcGIS entity disappears. Data QA reports such records as sidecar orphans so they can be reviewed rather than destructively removed.
