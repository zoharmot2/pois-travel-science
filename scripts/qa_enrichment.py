#!/usr/bin/env python3
"""Validate enrichment shape, identifiers, cross-references and provenance."""
import json, pathlib, re, sys
from enrich_data import snapshot
ROOT = pathlib.Path(__file__).resolve().parents[1]


def validate():
    document = json.loads((ROOT/'data/derived/enrichment.json').read_text(encoding='utf-8'))
    records = document['entities']; entities = snapshot()
    assert document['schema_version'] == '1.0'
    assert set(records) == set(entities), f'Enrichment keys differ from ArcGIS snapshot: missing {len(set(entities)-set(records))}, stale {len(set(records)-set(entities))}'
    for key,rec in records.items():
        assert re.fullmatch(r'[a-f0-9-]{36}',key)
        assert rec['geometry_family'] == entities[key]['family']
        assert isinstance(rec['administrative'],dict)
        assert isinstance(rec['candidates'],list)
        assert rec['provenance']['enrichment_status'] in ('pending','completed','retry_pending','unsupported_geometry','invalid_geometry')
        if rec.get('osm_entity') is not None:
            assert rec['match_quality']['match_status'] == 'manually_verified', key
        if rec['provenance']['enrichment_status'] == 'completed':
            assert rec['provenance']['source_provenance'], key
        assert isinstance(rec['provenance']['enrichment_notes'],str)
    print(f'PASS: {len(records)} enrichment records; valid referential integrity and provenance')

if __name__=='__main__':
    try: validate()
    except Exception as exc:
        print(f'FAILED enrichment QA: {exc}',file=sys.stderr)
        raise SystemExit(1)
