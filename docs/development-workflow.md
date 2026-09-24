# Development and Release Workflow

## Working model

The project is managed in GitHub and developed locally with GitHub Desktop. Development is performed directly on `main` because the repository is maintained by a sole developer.

ArcGIS Online / Field Maps remains the authoritative source for collected spatial data. The local working tree is the authoritative application-development workspace.

Application-code changes and automated data-refresh commits are different classes of change and should remain distinguishable in Git history.

## Local preview

From the repository root, open Windows Command Prompt and run:

```cmd
py -m http.server 8000
```

Standalone:

```text
http://localhost:8000/
```

Embedded:

```text
http://localhost:8000/?embed=true
```

Alternative embedded flag:

```text
http://localhost:8000/?embed=1
```

Do not use `file://index.html`; the application loads JSON/GeoJSON resources over HTTP.

## Local validation before committing

Run:

```cmd
py scripts\qa_data.py
py scripts\qa_frontend.py
```

For release-affecting frontend changes, also complete `docs/regression-qa.md` in:

```text
Standalone desktop
Embedded desktop
Standalone narrow/mobile
Embedded narrow/mobile
```

## GitHub Desktop flow

A normal manual code/configuration change is:

```text
Edit locally
   ↓
Run local server / QA
   ↓
Review GitHub Desktop Changes
   ↓
Commit to main with a descriptive message
   ↓
Push origin
   ↓
If workflow/data-pipeline related, run the GitHub Action manually once
```

Avoid committing `data/derived/qa-report.json` merely because a local QA timestamp changed.

## Weekly ArcGIS refresh

`.github/workflows/sync.yml` runs weekly and can also be started manually.

The workflow:

1. checks out the repository;
2. configures Python and export dependencies;
3. preserves current Point/Line/Polygon GeoJSON files in a temporary QA baseline;
4. runs `scripts/fetch_data.py` against the public Hosted Feature Layer View;
5. runs `scripts/qa_data.py --baseline-root .qa-baseline`;
6. runs `scripts/qa_frontend.py`;
7. uploads the QA report as an Actions artifact;
8. stages `data/` with additions, modifications, and deletions;
9. verifies local Line/Polygon attachments are tracked/staged;
10. commits/pushes refreshed generated data if required validation did not fail.

## QA severity and publication

- `PASS`: continue.
- `WARNING`: continue, but review the reported source/configuration issue.
- `ERROR`: stop publication; QA exits non-zero so the later commit/push step does not run.

Source-data warnings should normally be fixed in ArcGIS Online rather than silently rewritten in website code.

## Versioning discipline

Weekly data refreshes do not increment the application version.

Application releases update all release references together after regression validation. Current official release: `1.4.0`.

Synchronize at least:

- `VERSION`;
- HTML title/version metadata;
- README current release;
- documentation index/current architecture wording;
- release notes;
- Git tag / GitHub Release name.

## v1.4.0 release flow

After the v1.4.0 release patch is applied locally:

```cmd
py scripts\qa_data.py
py scripts\qa_frontend.py
py -m http.server 8000
```

Reconfirm the release matrix if any release patch changed executable frontend code. The final v1.4.0 patch is documentation/version-only, so the previously completed Stage 12 manual regression remains the functional release gate; still confirm the version/title and that the application loads normally.

Then:

1. review the changes in GitHub Desktop;
2. commit to `main` with a release message such as `Release v1.4.0`;
3. push origin;
4. manually run **Sync ESRI Data Weekly**;
5. confirm Data QA has 0 errors and Frontend Regression QA has 0 errors;
6. confirm the live repository/site reflects `1.4.0`;
7. create tag `v1.4.0` from the release commit and publish the GitHub Release using `docs/release-1.4.0.md` as the release-note basis.

## Deferred beyond v1.4.0

Later roadmap work includes analytics/clustering, external enrichment, Trips/timeline, Collections, Routes, public/private builds, SEO/public discovery, and other derived research/travel features. These should be added around the stable ArcGIS/Entity foundation rather than by destabilizing the collection schema.
