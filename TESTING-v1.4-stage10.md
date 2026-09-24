# v1.4 Stage 10 — Media / Attachment Test Checklist

Stage 10 changes generated GeoJSON media metadata, the Detail Panel, and Data QA. Re-run the ArcGIS export before running Data QA.

## 1. Local export

From the repository root in Command Prompt:

```cmd
py scripts\fetch_data.py
```

Confirm that the export completes for all three datasets and that image/audio synchronization completes without an exception.

## 2. Generated data contract

Open one current entity with attachments in each available geometry dataset and verify that its GeoJSON properties contain both:

```text
attachments
attachment_media
```

Each `attachment_media` item should contain `url`, `name`, `contentType`, `kind`, `storage`, ArcGIS attachment/object IDs, and `sourceDataset`.

Check `data/derived/layers-metadata.json` and confirm each dataset includes `attachmentSummary`.

## 3. Data QA

Run:

```cmd
py scripts\qa_data.py
```

Expected:

- 3 active datasets;
- 0 Errors;
- `Attachment references` and `Attachment media metadata` have the same count;
- Missing local attachments = 0;
- Orphan local attachments = 0;
- media counts appear for Images / Audio / Video / Other media.

Known ArcGIS data-quality warnings such as missing POI names/types/topics may remain warnings.

## 4. Frontend QA

```cmd
py scripts\qa_frontend.py
```

Expected:

```text
Frontend regression QA: PASS
Errors: 0 | Warnings: 0
```

## 5. Browser media regression

Start the local server:

```cmd
py -m http.server 8000
```

Test both:

```text
http://localhost:8000/
http://localhost:8000/?embed=true
```

For entities with media, verify:

- Point photos render under **Photos**;
- Line/Polygon photos render under **Photos**;
- audio renders under **Audio** with working browser controls and an Open audio file link;
- video remains under **Other Attachments** as an Open video link;
- unsupported attachments remain explicit links rather than broken images;
- media filenames remain readable;
- opening/closing the Detail Panel still behaves correctly.

If the current live dataset contains no audio or video, validate the relevant Data QA counts and defer browser playback/link testing until such media is present.

## 6. GitHub Actions

After the local checks pass, commit/push and manually run **Sync ESRI Data Weekly**. Confirm:

- Fetch Points, Lines and Polygons succeeds;
- Data QA has 0 Errors;
- Frontend Regression QA passes;
- the automated data commit includes any changed local media and updated GeoJSON/metadata outputs.
