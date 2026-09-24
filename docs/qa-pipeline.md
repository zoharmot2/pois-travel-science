# Data QA Pipeline

Version 1.3 introduces a dependency-free QA layer for generated website data. Its purpose is to detect source/export problems before a weekly refresh is committed while keeping ArcGIS Online / Field Maps authoritative.

## Files

- `scripts/qa_data.py` — validator and report generator.
- `scripts/qa_config.json` — data-source and validation configuration.
- `data/derived/qa-report.json` — generated machine-readable report.
- `.github/workflows/sync.yml` — weekly/manual refresh workflow that runs the validator after export.

## Current and future geometry datasets

The QA configuration is deliberately multi-geometry-ready:

- `points` → `data/pois.geojson` — required now.
- `lines` → `data/lines.geojson` — optional until line export is activated.
- `polygons` → `data/polygons.geojson` — optional until polygon export is activated.

Optional datasets are ignored when their files do not exist. Once line or polygon export is activated, the validator can check them without restructuring the QA engine. Paths can be changed in `scripts/qa_config.json` if the final export names differ.

Stable Entity IDs are checked globally across every active dataset, because future metadata, Trips, Collections, Routes, deep links, and public pages must resolve to exactly one Entity regardless of geometry family.

## Checks

The validator checks:

- required files;
- valid GeoJSON FeatureCollections;
- supported Point/MultiPoint, LineString/MultiLineString, and Polygon/MultiPolygon geometries;
- WGS84 coordinate ranges;
- expected geometry family for each configured dataset;
- present, valid, and globally unique ArcGIS `GlobalID` values;
- missing POI names, Research Topics, and POI Types;
- Research Topics present in data but missing explicit `config.json` styling;
- placeholder-like POI Type values such as `Undefined` as review warnings, without rewriting source data;
- attachment field structure;
- local attachment file existence and safe repository-relative paths;
- metadata-sidecar schema, IDs, record shape, duplicates, and orphan references;
- additions/removals compared with the pre-refresh repository snapshot when a baseline is supplied.

Remote `http`/`https` attachment URLs are counted but are not fetched during QA. This keeps validation deterministic and avoids treating temporary external-network failures as source-data corruption.

## Severity

`WARNING` means the website can still be published, but the issue should be reviewed. Typical examples include a missing POI name, a newly introduced POI Type with no custom style yet, a placeholder-like Type value, or an orphan sidecar reference.

`ERROR` means publication should be blocked. Typical examples include invalid/duplicate stable IDs, invalid geometries, missing required files, unsafe attachment paths, local attachment references whose files are missing, or an invalid sidecar schema.

The script exits with code `0` for PASS/WARNING and `1` for ERROR. `--fail-on-warnings` is available for stricter manual checks.

## Local use

From the repository root:

```cmd
py scripts\qa_data.py
```

The report is written to:

```text
data/derived/qa-report.json
```

## GitHub Actions integration

The production workflow is integrated in `.github/workflows/sync.yml` and runs weekly as well as through `workflow_dispatch`.

Current sequence:

```text
Check out repository
        ↓
Set up Python / dependencies
        ↓
Preserve existing point/line/polygon GeoJSON files in .qa-baseline
        ↓
Run scripts/fetch_data.py
        ↓
Run scripts/qa_data.py --baseline-root .qa-baseline
        ↓
Run scripts/qa_frontend.py
        ↓
Upload qa-report.json artifact (always)
        ↓
If no required step failed, commit/push refreshed data
```

If data QA returns ERROR, the GitHub job stops before the later commit/push step. WARNING status continues normally.

When run in GitHub Actions, `qa_data.py` also appends a compact Markdown report to `GITHUB_STEP_SUMMARY`.

The generated `data/derived/qa-report.json` is uploaded as an Actions artifact but explicitly removed from the staged data commit, preventing report timestamps from producing meaningless repository commits.

## Baseline delta counts

The workflow copies any existing:

```text
data/pois.geojson
data/lines.geojson
data/polygons.geojson
```

into `.qa-baseline` before the refresh. This allows the validator to report additions and removals between the previous and newly generated snapshots.

The line and polygon files are optional today, but this baseline mechanism is already prepared for their future export.

## Validated behavior

The real GitHub Actions integration has been tested successfully with WARNING status and zero errors. This confirmed that warnings do not block publication and that local attachment validation runs against the authoritative repository files rather than development ZIP artifacts.

## Extensibility

`POI_Topic` and `POI_Type` remain open-ended. The QA pipeline does not enforce closed domain lists. New Topics are accepted as research metadata without requiring visual style. New Types are counted automatically; if a Type has no explicit `config.json` style, QA emits `TYPE_STYLE_MISSING` and the website continues with the default Type style.

The QA layer never edits ArcGIS data. Source corrections remain an ArcGIS Online / Field Maps responsibility unless a value is explicitly defined as website-managed or externally derived metadata.

### Orphan attachment protection

Data QA also scans `data/attachments/` recursively after export. A local attachment file that is not referenced by any current point, line, or polygon entity is reported as `ATTACHMENT_FILE_ORPHAN` and is an `ERROR`. The exporter normally removes these files itself; the QA check is a second safety net that prevents stale media from being published if cleanup ever fails.
