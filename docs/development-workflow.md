# Development and Release Workflow

## Working model

The project is managed in GitHub and developed locally with GitHub Desktop.

The local working tree is the authoritative development workspace. ArcGIS Online / Field Maps remains the authoritative source for collected spatial data.

Application-code changes and weekly automated data-refresh changes are different classes of change and should remain distinguishable in Git history.

## Local preview

From the repository root, open Windows Command Prompt and run:

```cmd
py -m http.server 8000
```

Standalone mode:

```text
http://localhost:8000/
```

Embedded mode:

```text
http://localhost:8000/?embed=true
```

Alternative embedded flag:

```text
http://localhost:8000/?embed=1
```

Do not use `file://index.html`; the application loads JSON/GeoJSON resources over HTTP.

## Local validation before committing frontend/data-pipeline changes

Run:

```cmd
py scripts\qa_data.py
py scripts\qa_frontend.py
```

For frontend changes, also complete the browser regression matrix in `regression-qa.md` in both standalone and embedded modes at desktop and narrow/mobile widths.

## GitHub Desktop flow

A normal manual code/configuration change is:

```text
Edit locally
   ↓
Run local server / QA
   ↓
Review GitHub Desktop Changes
   ↓
Commit with a descriptive message
   ↓
Push origin
   ↓
If workflow-related, run the GitHub Action manually once
```

Avoid committing generated `data/derived/qa-report.json` simply because a local QA timestamp changed.

## Weekly ArcGIS refresh

`.github/workflows/sync.yml` runs weekly and can also be started manually.

The workflow currently:

1. checks out the repository;
2. configures Python;
3. installs the export dependencies;
4. preserves current point/line/polygon GeoJSON files in a temporary QA baseline when they exist;
5. runs `scripts/fetch_data.py`;
6. runs `scripts/qa_data.py --baseline-root .qa-baseline`;
7. runs `scripts/qa_frontend.py`;
8. uploads `data/derived/qa-report.json` as a GitHub Actions artifact;
9. commits/pushes refreshed `data/` only if earlier required steps did not fail.

The QA artifact is retained separately and is removed from the staged data commit so a report timestamp does not create a meaningless repository change.

## QA severity and publication

- `PASS`: continue.
- `WARNING`: continue, but review the reported source/configuration issue.
- `ERROR`: the QA command exits non-zero, so the later commit/push step does not run.

Source-data warnings should normally be fixed in ArcGIS Online rather than silently rewritten in website code.

## Future line and polygon activation

The repository already anticipates:

```text
data/lines.geojson
data/polygons.geojson
```

The files are optional until export is activated. The future integration task should extend `fetch_data.py` and the GitHub Actions export step while keeping existing point behavior intact.

Before activating either dataset:

- confirm the ArcGIS source endpoint/layer;
- confirm `GlobalID` availability and uniqueness;
- map field names into the existing Entity contract;
- validate attachments if applicable;
- activate the source in the client loader;
- run data and frontend QA;
- complete manual regression checks.

## Versioning discipline

Weekly data refreshes do not increment the application version.

Application releases update all version references together only after regression validation is complete. The current official release is `1.3.0`.

A release should synchronize at least:

- `VERSION`;
- HTML title/version metadata;
- README version status;
- any release/tag notes used in GitHub.

## Release boundary for v1.3

Version 1.3.0 is the Foundation release. Later roadmap items remain deferred even though the architecture now permits them.

Deferred work includes full analytics, clustering, external enrichment, Trips, timeline, Collections, Routes, public/private builds, SEO pages, and actual line/polygon publication.
