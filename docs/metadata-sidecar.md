# Website Metadata Sidecar

## Purpose

The metadata sidecar provides a version-controlled place for website-specific information that should not be added to, or written back into, the authoritative ArcGIS Online / Field Maps collection schema.

Version 1.3 established the stable linkage contract. Version 1.4 keeps that schema unchanged while applying it to active Point, Line, and Polygon Entities. Trips, Collections, Routes, publication/privacy rules, travel-journal fields, and other future metadata structures remain later work.

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

`entities` is an object keyed by the website's canonical stable Entity ID: the normalized ArcGIS `GlobalID` in lowercase UUID form without braces.

The metadata value for each Entity must be a JSON object. The current schema deliberately does not standardize application-specific fields inside that object yet.

## Loading and linkage

The website loads independent source categories:

```text
config.json
ArcGIS-derived spatial data
data/site/poi-meta.json
```

The ArcGIS data is normalized into Entity objects first. Stable IDs are indexed, then sidecar records are matched by `entity.entityId` and attached as:

```js
entity.websiteMetadata
```

If an Entity has no sidecar record, `entity.websiteMetadata` is `null`.

## Integrity rules

Application/runtime behavior:

- a missing sidecar is tolerated during development and produces an English console warning;
- `schemaVersion` must equal `1`;
- sidecar keys must be valid UUID/GlobalID values;
- different raw keys that normalize to the same UUID are invalid duplicates;
- metadata values must be JSON objects;
- metadata is never used as a fallback identity source.

Automated data QA applies publication severity:

- missing sidecar → WARNING;
- unsupported schema / invalid JSON / invalid IDs / duplicate IDs / non-object records → ERROR;
- valid metadata ID not present in current exported datasets → WARNING (`SIDECAR_ORPHAN_ID`).

The orphan condition is a warning because an ArcGIS feature may have been removed while historical website metadata still needs review rather than automatic deletion.

## Provenance boundary

The separation is intentional:

```text
ArcGIS / Field Maps          Website sidecar
--------------------         ----------------
Authoritative field data     Website-specific metadata
POI_Topic / POI_Type         Future Trips / Collections / Routes
Geometry                     Future publication metadata
Attachments                  Future travel/research annotations
GlobalID                     References Entities by GlobalID
```

Website metadata must not silently overwrite ArcGIS-authored properties. Future features should preserve source/provenance information whenever derived or external values are introduced.

## Extensibility

The sidecar is keyed by stable ID rather than by POI name, `OBJECTID`, coordinates, or array position. This allows website metadata to survive weekly ArcGIS refreshes and ordinary name/attribute edits as long as the authoritative ArcGIS `GlobalID` remains unchanged.

The same pattern applies to the active Point, Line, and Polygon Entities because all geometry families use the same Entity and stable-ID contract.
