#!/usr/bin/env python3
"""Offline v1.5.0 completion gate and counts."""
from pathlib import Path
import json, sys
from enrich_data import snapshot
root=Path(__file__).resolve().parents[1]
records=json.loads((root/'data/derived/enrichment.json').read_text(encoding='utf-8'))['entities']
sources=snapshot()
missing=set(sources)-set(records)
extra=set(records)-set(sources)
eligible=[uid for uid,source in sources.items() if source['location'] is not None]
completed=[uid for uid in eligible if records.get(uid,{}).get('provenance',{}).get('enrichment_status')=='completed']
print(f'Eligible point POIs: {len(eligible)}; completed: {len(completed)}; remaining: {len(eligible)-len(completed)}')
if missing or extra: print(f'ERROR: mismatch of GlobalIDs (missing={len(missing)}, extra={len(extra)})'); sys.exit(1)
if len(completed)!=len(eligible): print('NOT READY for v1.5.0 release: administrative backfill incomplete.');sys.exit(1)
print('PASS: all eligible point POIs enriched and linked by GlobalID.')
