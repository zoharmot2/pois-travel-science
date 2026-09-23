# Website Metadata Sidecar

## Purpose

The metadata sidecar provides a version-controlled place for website-specific information that should not be added to, or written back into, the authoritative ArcGIS Online / Field Maps collection schema.

This infrastructure is intentionally minimal in v1.3 Stage 5. It establishes stable linkage only. Trips, Collections, Routes, publication/privacy rules, travel-journal fields, and other future metadata structures remain outside the Stage 5 scope.

## File location

The canonical sidecar file is:

```text
data/site/poi-meta.json
```

The weekly ArcGIS export pipeline must treat this file as website-managed content and must not overwrite or regenerate it as part of the POI snapshot refresh.

## Current schema

```json
{
  "schemaVersion": 1,
  "entities": {
    "01234567-89ab-4cde-8fab-0123456789ab": {
      "exampleFutureField": "value"
    }
  }
}
```

`entities` is an object keyed by the website's canonical stable Entity ID. The key is the normalized ArcGIS `GlobalID`: lowercase UUID form without braces.

The metadata value for each Entity must be a JSON object. Stage 5 deliberately does not standardize fields inside that object yet.

## Loading and linkage

The website loads three independent sources:

```text
config.json
ArcGIS-derived data/pois.geojson
website-managed data/site/poi-meta.json
```

The ArcGIS data is normalized into Entity objects first. Stable IDs are indexed, then sidecar records are matched by `entity.entityId` and attached as:

```js
entity.websiteMetadata
```

If an Entity has no sidecar record, `entity.websiteMetadata` is `null`.

## Integrity rules

- A missing `poi-meta.json` is tolerated during development and produces a console warning; the application continues with an empty sidecar.
- `schemaVersion` must currently equal `1`.
- Sidecar keys must be valid UUID/GlobalID values.
- Different raw keys that normalize to the same UUID are rejected as duplicates.
- Metadata values must be JSON objects.
- A valid metadata ID that is not present in the current ArcGIS snapshot is reported as an orphan reference.
- Metadata is never used as a fallback identity source. ArcGIS `GlobalID` remains authoritative for Entity identity.

The formal v1.3 QA stage will later decide which integrity conditions are warnings and which should block publication.

## Provenance boundary

The separation is intentional:

```text
ArcGIS / Field Maps          Website sidecar
--------------------         ----------------
Authoritative field data     Website-specific metadata
POI_Topic / POI_Type         Future Trips / Collections / Routes
Geometry                     Future publication metadata
Attachments                  Future travel/research annotations
GlobalID                     References entities by GlobalID
```

Website metadata must not silently overwrite ArcGIS-authored properties. Future features should preserve source/provenance information whenever derived or external values are introduced.

## Extensibility

The sidecar is keyed by stable ID rather than by POI name, OBJECTID, coordinates, or array position. This allows future metadata to survive weekly ArcGIS refreshes and name/attribute edits as long as the authoritative ArcGIS `GlobalID` remains unchanged.

The same pattern can later be extended to line and polygon entities because they use the same generic Entity/stable-ID contract.
