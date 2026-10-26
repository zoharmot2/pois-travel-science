# v1.5.0 — Data Enrichment: implementation and deployment

## Status and limitations
This is an implementation candidate, **not a fully accepted production release**. The automatic, incremental **administrative** reverse geocoding pipeline is implemented. Nominatim's reverse API may return an OSM object close to a coordinate; that object is recorded as an unverified candidate and **must not be considered a verified entity match**. The full type/name/spatial matching and calibrated confidence-score engine from the approved specification is still outstanding. Points are eligible for reverse geocoding; non-point features are explicitly marked `unsupported_geometry` rather than assigning misleading center-based addresses.

The external source is OpenStreetMap via Nominatim. The data layer is separate from AGOL and keyed by normalized GlobalID; AGOL Notes and other authored fields are never modified. Data fields are nested under `administrative`, `osm_entity`, `candidates`, `match_quality`, and `provenance`. The visible detail panel only presents location, verified OSM name/category/subtype (if any), match state, and enrichment notes. Raw diagnostics remain available in the JSON sidecar.

## Initial offline snapshot
`scripts/enrich_data.py --offline` generates one safe enrichment record per current ArcGIS GlobalID; records are marked `pending` until an approved network run. Do not interpret a `pending` record as containing externally enriched information.

## Network setup
1. Review Nominatim's **current usage policy** and confirm the size and cadence of this project are acceptable for the selected provider. Large-scale weekly bulk geocoding of 1,200+ sites on public Nominatim must not be assumed permitted. Consider a self-hosted or contracted geocoding provider for systematic coverage.
2. In GitHub Settings → Secrets and variables → Actions, create a repository secret `ENRICHMENT_USER_AGENT` with a descriptive identity and a **real contact email**, e.g. `POIsTravelScience/1.5 (contact: team@example.org)` (replace the example with a real contact). This value is not embedded in the repository.
3. `config/enrichment.json` contains the network switch, `max_requests_per_run` (10), and delay between calls (1.5 s). A missing User-Agent turns networking off safely, even when `network_enabled` is `true`.
4. Start with a small, permitted test run: `ENRICHMENT_USER_AGENT='your contactable UA' python scripts/enrich_data.py --max-requests 2`. To validate without calling external services: `python scripts/enrich_data.py --offline`.
5. Validate: `python scripts/qa_enrichment.py`, `python scripts/qa_data.py`, and `python scripts/qa_frontend.py`.
6. Open `http://localhost:8000/` using `python -m http.server 8000` and inspect the standalone and `?embed=true` views.

The sync workflow runs enrichment after refreshing ArcGIS datasets, before QA and commit. External failures are explicitly reported; a failed run does not silently replace valid current data. All successful rows use cached completed values if the ArcGIS fingerprint is unchanged. Refresh / expiry and multi-provider production coverage require further policy decisions.

## Human reviewed OSM match
Add an entry keyed by exact lower-case ArcGIS GlobalID into `data/site/enrichment-reviews.json`:

```json
{"schema_version":"1.0","entities":{"xxxxxxxx-xxxx-4xxx-8xxx-xxxxxxxxxxxx":{"decision":"accept","osm_type":"way","osm_id":123456}}}
```

Replace the sample identifier with a real UUID and select a candidate actually recorded for the POI. If the candidate no longer matches, the script does not accept it. Rejection uses `"decision":"reject"`. The admin review document contains decisions, not AGOL edits.

## Attribution / limitations
OpenStreetMap contributors (ODbL 1.0) and Nominatim are identified in the website and JSON output. Reuse of OSM-derived databases may entail license obligations; verify before wider redistribution. Reverse geocoding does not certify a POI's identity or administrative boundary in contested areas. No private imagery, field notes, or attachments are transmitted: only geographic point coordinates.

## Preferred enrichment language (English)
New Nominatim requests specify `accept-language=en` (query and HTTP header), and request `namedetails=1`. English OSM names are preferred when present; the returned source spelling is retained as the fallback rather than machine-translated. Structured administrative names and display address are therefore in English where supported by Nominatim, but may remain in a local language when no English variant is available. Original AGOL values are unchanged.

Completed records from the earlier candidate without a `preferred_language` provenance marker are queued for refresh on a subsequent **permitted** network run; the configured request cap applies. This refresh may revisit the two pilot records before processing new records. `--offline` does not send any requests. Source attribution is only displayed on the POI detail panel when the record has source data.

## Stage 2: OSM candidate matching (experimental)

A separate, opt-in Overpass API search finds up to ten nearby tagged OSM objects for **point** POIs already enriched by reverse geocoding. Example (limited to two Overpass requests):

```cmd
py scripts/enrich_data.py --max-requests 0 --max-match-requests 2
```

This requires `ENRICHMENT_USER_AGENT` and Internet access. Default `--max-match-requests 0` makes no Overpass calls. Radius defaults to 40 metres and is bounded to 10–100 metres via `--match-radius-m`. Calls are sequential with a minimum delay of two seconds. Public Overpass capacity is shared and not guaranteed; keep batches small, review provider policy, and avoid using this as an unlimited background crawler. Never transmit AGOL notes or photos.

Candidates are ranked by approximate distance to OSM representative points, name similarity and limited OSM tag cues. Distances to ways/relations are approximate because `out center` uses a feature centre rather than its actual boundary. Scores are **heuristic rankings, not calibrated probabilities**. No candidate is automatically accepted: `match_status=review_required`, `osm_entity=null`, until explicitly reviewed in `data/site/enrichment-reviews.json`. Both name and tag relevance are language- and content-dependent; verify against the original OSM link. Overpass search results and provenance are retained for subsequent offline runs. Previously enriched administrative values remain untouched. Non-point geometries are intentionally excluded from this pilot.

The run report includes `osm_match_requests`, plus `updated_this_run` entries for each successful candidate search. If a provider fails the affected record remains unchanged and can be retried. This is a candidate-search implementation, **not a fully calibrated automatic entity-matching release**.
