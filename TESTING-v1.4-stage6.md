# v1.4 Stage 6 — Multi-Layer Fetch/Export Test Checklist

Run from the repository root in Command Prompt.

## 1. Static checks

```cmd
py -m py_compile scripts\fetch_data.py scripts\qa_data.py scripts\qa_frontend.py
py scripts\qa_frontend.py
```

Expected frontend QA: `PASS` with 0 errors.

## 2. Run the ArcGIS export

```cmd
py scripts\fetch_data.py
```

Expected outputs:

- `data/pois.geojson`
- `data/lines.geojson`
- `data/polygons.geojson`
- `data/pois.csv`
- `data/pois.pdf`
- `data/derived/layers-metadata.json`

The console should identify FeatureServer layers 0, 1, and 2 and report an entity count for each dataset.

The exporter must use the public `POI_Feature_Layer_view/FeatureServer` service for layers 0, 1, and 2; a `499 Token Required` error indicates the protected source service was used by mistake.

## 3. Inspect harvested metadata

Open `data/derived/layers-metadata.json` and verify:

- points: layer 0 / point
- lines: layer 1 / line
- polygons: layer 2 / polygon
- the three domain sections exist for `POI_Type`, `POI_Topic`, and `Collect_Name`
- common-field availability is recorded for every dataset

## 4. Verify attachment synchronization and deletion cleanup

The exporter now synchronizes attachments for points, lines, and polygons. Image and audio attachments for lines and polygons should appear under:

- `data/attachments/lines/`
- `data/attachments/polygons/`

Audio files are downloaded locally without transcoding. Video and other unsupported media remain direct ArcGIS URLs.

For a controlled deletion test, use a disposable ArcGIS test entity or attachment only:

1. Run the export and verify its GeoJSON feature and local image/audio attachment exist.
2. Delete that test entity (or one of its image/audio attachments) in AGOL.
3. Run `py scripts\fetch_data.py` again.
4. Verify the deleted entity is absent from the relevant GeoJSON and its no-longer-referenced local image file is removed.

Do not use a production research record for this test.

For an audio test, use a disposable attachment such as `.mp3`, `.wav`, or `.m4a` and confirm that the GeoJSON `attachments` array contains a local `data/attachments/...` path rather than an ArcGIS URL.

## 5. Run Data QA

```cmd
py scripts\qa_data.py
```

Expected:

- 3 active datasets
- 0 geometry-family errors
- 0 duplicate stable-ID errors
- no missing required output files

Known source-data warnings such as missing `POI_Name` may remain warnings.

Expected additionally:

- attachment references from all three datasets are validated;
- `Missing local attachments` is 0;
- `Orphan local attachments` is 0.

## 6. Browser regression

```cmd
py -m http.server 8000
```

Open:

- `http://localhost:8000/`
- `http://localhost:8000/?embed=true`

Stage 6 does not yet load lines/polygons into the frontend. The current point map must remain unchanged and operational. Geometry counts in the Stage 5 UI will still reflect browser-loaded entities only until Stage 7 activates the new datasets.

## 7. GitHub Actions validation

After commit/push, manually run `Sync ESRI Data Weekly` and verify:

1. `Preserve Previous Spatial Data for QA`
2. `Fetch Points, Lines and Polygons`
3. `Validate Generated Data`
4. `Validate Frontend Regression Structure`
5. `Commit and Push Updated Files`

The Data QA summary should report three active datasets after the first successful multi-layer export.
