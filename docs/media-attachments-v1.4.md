# v1.4 Stage 10 — Media and Attachment Handling

Stage 10 formalizes attachment/media handling across the active point, line, and polygon datasets.

## Export contract

The ArcGIS export keeps the existing `attachments` array of canonical URLs/paths for backward compatibility and adds a structured `attachment_media` array for each entity.

Each media item contains:

- `url` — local repository path or direct public ArcGIS URL;
- `name` — original ArcGIS attachment name;
- `contentType` — ArcGIS MIME type when available;
- `kind` — `image`, `audio`, `video`, or `other`;
- `storage` — `local` or `remote`;
- `attachmentId` and `parentObjectId` — ArcGIS attachment linkage;
- `sourceDataset` — `points`, `lines`, or `polygons`.

`attachments` and `attachment_media[*].url` must match one-to-one.

## Storage policy

- Images are downloaded locally and optimized as before.
- Audio is downloaded locally without transcoding.
- Video remains a direct public ArcGIS URL.
- Other unsupported media remains a direct public ArcGIS URL.
- Point media keep the historical root attachment path.
- Line media use `data/attachments/lines/`.
- Polygon media use `data/attachments/polygons/`.

The synchronization cleanup from Stage 6 remains authoritative: deleting an ArcGIS entity or deleting one of its local image/audio attachments removes the corresponding local file after the next successful refresh. Cleanup never runs from an incomplete attachment query.

## Browser presentation

The Entity Detail Panel uses structured media metadata when available and retains a compatibility fallback for older exports.

- Photos render as thumbnail links.
- Audio renders with the browser's native HTML5 audio controls and an explicit file link.
- Video remains an external/open link rather than an embedded or locally downloaded video.
- Other attachments render as explicit links.

Media sections are grouped as **Photos**, **Audio**, and **Other Attachments** and are shared by Point, Line, and Polygon entities.

## Layer metadata

`data/derived/layers-metadata.json` now includes an `attachmentSummary` per dataset with total references, local/remote storage counts, and counts by media kind. This makes the weekly export auditable without requiring the browser to inspect every feature.

## QA contract

Data QA validates:

- `attachment_media` is an array of valid metadata objects for every exported feature;
- `kind` is one of `image`, `audio`, `video`, `other`;
- `storage` is `local` or `remote` and matches the URL form;
- the structured media URLs match the canonical `attachments` array one-to-one;
- local attachment files exist;
- no unreferenced local attachment file remains in the repository.

The QA report also exposes counts by media kind and local/remote storage.
