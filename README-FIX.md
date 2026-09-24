# v1.4 Stage 6.1 — Public View Source Fix

The multi-layer exporter must read from the public hosted view:

`POI_Feature_Layer_view/FeatureServer`

Sublayers:
- 0 — points
- 1 — lines
- 2 — polygons

This replaces the protected source service `POI_Feature_Layer/FeatureServer`, which returns ArcGIS REST error 499 (Token Required) for unauthenticated local/GitHub Actions use.

Replace these repository files:
- `scripts/fetch_data.py`
- `scripts/qa_frontend.py`
- `docs/multi-layer-ingestion-v1.4.md`
- `TESTING-v1.4-stage6.md`
