# v1.4 Stage 11 — Multi-Dataset QA Test Checklist

Stage 11 changes QA only. It does not change ArcGIS data, map rendering, filtering, search, media behavior, or the GitHub workflow sequence.

## 1. Refresh current ArcGIS data

From the repository root:

```cmd
py scripts\fetch_data.py
```

Confirm that Points, Lines, and Polygons export successfully and `data/derived/layers-metadata.json` is regenerated.

## 2. Run Data QA

```cmd
py scripts\qa_data.py
```

Expected publication-level conditions:

- `Active datasets: 3`;
- 0 Errors;
- layer metadata dataset count = 3;
- stable IDs equal the total exported entity count;
- missing local attachments = 0;
- orphan local attachments = 0.

Known source-data warnings for blank names/topics/types may remain warnings.

## 3. Inspect the QA report

Open:

```text
data/derived/qa-report.json
```

Confirm that it contains:

```text
layerMetadataValidation
domainComparison
```

`layerMetadataValidation.featureServerUrl` must be the public `POI_Feature_Layer_view/FeatureServer` URL.

Under `domainComparison`, confirm entries for:

```text
POI_Type
POI_Topic
Collect_Name
```

At the current ArcGIS checkpoint these domains are expected to be aligned. If they diverge in the future, `alignedAcrossDatasets: false` is allowed and must not by itself fail QA.

## 4. Frontend regression structure

```cmd
py scripts\qa_frontend.py
```

Expected:

```text
Frontend regression QA: PASS
Errors: 0 | Warnings: 0
```

## 5. GitHub Actions

After local validation, commit/push the Stage 11 QA files and manually run **Sync ESRI Data Weekly**.

Confirm:

- Fetch Points, Lines and Polygons succeeds;
- Data QA has 0 Errors;
- the GitHub Step Summary includes a **Domain alignment** section;
- Frontend Regression QA passes;
- the automated data commit remains able to proceed when Data QA contains only known warnings.

No `.github/workflows/sync.yml` replacement is required for Stage 11; the existing workflow already runs the enhanced `qa_data.py`.
