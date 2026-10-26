#!/usr/bin/env python3
"""Incremental, rate-limited Nominatim administrative enrichment. Never writes ArcGIS-authored data."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os, pathlib, re, time, urllib.error, urllib.parse, urllib.request, math, difflib

ROOT = pathlib.Path(__file__).resolve().parents[1]
UUID = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$')
SOURCES = [('points','data/pois.geojson'), ('lines','data/lines.geojson'), ('polygons','data/polygons.geojson')]
FIELDS = ('country','country_code','state','county','municipality','city','town','village','suburb','locality','road','house_number','postcode','display_address')


def load(path, default=None):
    p = ROOT / path
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default


def atomic_write(path, data):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + '.tmp')
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')
    tmp.replace(p)


def norm(value):
    x = str(value or '').strip().strip('{}').lower()
    return x if UUID.fullmatch(x) else None


def coordinates(geometry):
    if not isinstance(geometry, dict): return None
    if geometry.get('type') != 'Point': return None  # no misleading bbox-centre geocoding
    a = geometry.get('coordinates')
    if not isinstance(a, list) or len(a) < 2: return None
    try: lon, lat = float(a[0]), float(a[1])
    except (ValueError, TypeError): return None
    return (lat,lon) if -90 <= lat <= 90 and -180 <= lon <= 180 else None


def snapshot():
    found = {}
    for family, path in SOURCES:
        data = load(path, {'features': []})
        for f in data.get('features', []):
            props = f.get('properties') or {}
            raw = next((v for k,v in props.items() if k.lower() == 'globalid'), None)
            key = norm(raw)
            if key is None: continue
            if key in found: raise ValueError(f'Duplicate ArcGIS GlobalID: {key}')
            location = coordinates(f.get('geometry'))
            name = next((v for k,v in props.items() if k.lower() in ('poi_name','name') and v), '')
            found[key] = {'family': family, 'location': location, 'name': str(name or '')}
    return found


def fingerprint(source):
    return hashlib.sha256(json.dumps(source, sort_keys=True).encode()).hexdigest()[:24]


def request_json(url, user_agent, retries=2):
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': user_agent, 'Accept': 'application/json', 'Accept-Language': 'en'})
            with urllib.request.urlopen(req, timeout=25) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as ex:
            if ex.code in (429, 503) and attempt < retries:
                time.sleep(3 * (attempt + 1)); continue
            raise


def address_from_nominatim(payload):
    addr = payload.get('address') or {}
    out = {k: addr.get(k) for k in FIELDS if k != 'display_address'}
    out['locality'] = next((addr[k] for k in ('city','town','village','municipality','hamlet','suburb') if addr.get(k)), None)
    out['display_address'] = payload.get('display_name')
    return out


def candidate_from_nominatim(payload):
    """Reverse geocoder nearest object is only a candidate, NEVER an auto-verified entity."""
    kind = payload.get('osm_type'); ident = payload.get('osm_id')
    if kind not in ('node','way','relation') or not str(ident or '').isdigit(): return []
    addr = payload.get('address') or {}
    names = payload.get('namedetails') or {}
    tags = {'category': payload.get('category'), 'type': payload.get('type')}
    return [{'osm_type':kind, 'osm_id':int(ident), 'osm_url':f'https://www.openstreetmap.org/{kind}/{ident}',
             'osm_name':names.get('name:en') or payload.get('name') or addr.get('attraction') or addr.get('building') or addr.get('amenity'),
             'osm_category':payload.get('category'), 'osm_subtype':payload.get('type'), 'osm_tags':tags,
             'match_score':None, 'match_distance_m':None, 'match_method':'nominatim_nearest_reverse',
             'match_evidence':['Nominatim nearest object; identity not established'], 'match_status':'candidate'}]


# An OSM search is a separate, bounded operation. Never infer identity from a reverse-geocoding hit.
OSM_KEYS = ('historic', 'heritage', 'tourism', 'natural', 'geological', 'waterway', 'building', 'amenity', 'leisure', 'man_made', 'landuse', 'shop', 'railway')

def haversine_m(lat1, lon1, lat2, lon2):
    rad = math.pi / 180
    a = math.sin((lat2-lat1)*rad/2)**2 + math.cos(lat1*rad)*math.cos(lat2*rad)*math.sin((lon2-lon1)*rad/2)**2
    return 12742000 * math.asin(min(1, math.sqrt(a)))


def osm_type_relation(tags, source_name):
    # A weak semantic cue only; no authoritative AGOL classification mapping is assumed.
    name = (source_name or '').casefold()
    category = next((k for k in OSM_KEYS if tags.get(k) and tags[k] != 'no'), None)
    related = any(word in name for word in ('river', 'lake', 'stream', 'wadi')) and bool(tags.get('waterway') or tags.get('natural') == 'water')
    return category, related


def normalize_name(value):
    return ' '.join(re.findall(r'\w+', (value or '').casefold(), flags=re.UNICODE))


def overpass_candidates(payload, source, radius_m=40):
    lat, lon = source['location']
    result = []
    for element in payload.get('elements', []):
        kind, ident, tags = element.get('type'), element.get('id'), element.get('tags') or {}
        if kind not in ('node', 'way', 'relation') or not isinstance(ident, int): continue
        if not any(k in tags for k in OSM_KEYS) and not tags.get('name'): continue
        center = element.get('center') or element
        if 'lat' not in center or 'lon' not in center: continue
        distance = round(haversine_m(lat, lon, float(center['lat']), float(center['lon'])), 1)
        # Polygon centres are approximate; a polygon enclosing the POI can have a distant centre.
        osm_name = tags.get('name:en') or tags.get('name') or None
        similarity = (difflib.SequenceMatcher(None, normalize_name(source['name']), normalize_name(osm_name)).ratio()
                      if source['name'] and osm_name else None)
        category, related = osm_type_relation(tags, source['name'])
        proximity = max(0.0, 1.0 - distance / max(radius_m, 1))
        # A weak heuristic useful only for ranking candidates; never a calibrated probability.
        score = round(min(1., 0.45*proximity + 0.45*(similarity or 0) + 0.10*int(related)), 3)
        evidence = [f'OSM centre distance: {distance} m (approximate for ways/relations)']
        if similarity is not None: evidence.append(f'Name similarity: {similarity:.3f}')
        if category: evidence.append(f'OSM tag category: {category}={tags[category]}')
        if related: evidence.append('Weak category keyword agreement')
        result.append({'osm_type': kind, 'osm_id': ident, 'osm_url': f'https://www.openstreetmap.org/{kind}/{ident}',
                       'osm_name': osm_name, 'osm_name_en':tags.get('name:en'), 'osm_name_local': tags.get('name'),
                       'osm_category': category, 'osm_subtype': tags.get(category) if category else None,
                       'osm_tags':{k:v for k,v in tags.items() if k in OSM_KEYS or k in ('name','name:en','website','wikidata','wikipedia','description')},
                       'match_score':score, 'match_distance_m':distance,'match_method':'overpass_proximity_name_tags_v1',
                       'match_evidence':evidence, 'match_status':'candidate'})
    result.sort(key=lambda x:(-x['match_score'], x['match_distance_m'], x['osm_type'], x['osm_id']))
    return result[:10]


OVERPASS_ENDPOINTS = (
    'https://overpass-api.de/api/interpreter',
    'https://overpass.kumi.systems/api/interpreter',
)


class OSMSearchError(RuntimeError):
    """All configured Overpass attempts failed; includes per-server diagnostics."""
    def __init__(self, attempts):
        self.attempts = attempts
        super().__init__('; '.join(f"{a['server']}: {a['error']}" for a in attempts))


def request_overpass(source, agent, radius_m=40, endpoints=None, opener=None, sleep=None, timeout=25):
    """One bounded attempt per endpoint, after transient errors only.

    Endpoints are explicitly configurable and queried sequentially; no unbounded
    retries. Do not put private POIs through third-party services.
    """
    endpoints = tuple(endpoints if endpoints is not None else OVERPASS_ENDPOINTS)
    opener = opener or urllib.request.urlopen
    sleep = sleep or time.sleep
    lat,lon = source['location']
    # One indexed proximity selection rather than a union of 12 repeated scans.
    key_pattern = '^(' + '|'.join(OSM_KEYS) + ')$'
    query = (f'[out:json][timeout:20];'
             f'nwr(around:{int(radius_m)},{lat:.7f},{lon:.7f})[~"{key_pattern}"~"."];out center 80;')
    body = urllib.parse.urlencode({'data': query}).encode()
    attempts = []
    for idx, endpoint in enumerate(endpoints):
        try:
            req = urllib.request.Request(endpoint, data=body,
                  headers={'User-Agent':agent,'Accept':'application/json','Content-Type':'application/x-www-form-urlencoded'})
            with opener(req, timeout=timeout) as resp:
                payload = json.load(resp)
            if not isinstance(payload, dict) or not isinstance(payload.get('elements'), list):
                raise ValueError('Invalid Overpass JSON response (missing elements)')
            return payload, endpoint, attempts
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
            # Do not send malformed/auth or other permanent client errors to another server.
            if isinstance(exc, urllib.error.HTTPError) and 400 <= exc.code < 500 and exc.code != 429:
                raise OSMSearchError(attempts + [{'server':endpoint,'error':f'HTTP {exc.code}'}]) from exc
            attempts.append({'server':endpoint,'error':f'{type(exc).__name__}: {str(exc)[:180]}'})
            if idx + 1 < len(endpoints): sleep(2 * (idx + 1))
    raise OSMSearchError(attempts)

def apply_match_search(rec, source, agent, radius_m):
    payload, endpoint, prior_attempts = request_overpass(source, agent, radius_m)
    matches = overpass_candidates(payload, source, radius_m)
    # Keep the reverse-geocoder's nearest feature as a weaker fallback only.
    old = rec.get('candidates') or []
    known = {(c['osm_type'], c['osm_id']) for c in matches}
    rec['candidates'] = matches + [c for c in old if (c['osm_type'],c['osm_id']) not in known][:1]
    rec['match_quality'].update({'match_status':'review_required' if rec['candidates'] else 'no_match',
                                 'match_score':matches[0]['match_score'] if matches else None,
                                 'match_distance_m':matches[0]['match_distance_m'] if matches else None,
                                 'match_method':'overpass_proximity_name_tags_v1',
                                 'match_evidence':matches[0]['match_evidence'] if matches else [],
                                 'review_status':'not_reviewed'})
    timestamp=dt.datetime.now(dt.timezone.utc).isoformat()
    prov=rec['provenance']
    prov['osm_match_searched_at']=timestamp
    prov.pop('osm_match_last_error', None)
    rec['match_quality']['search_status'] = 'completed'
    prov['source_provenance'].append({'source':'OpenStreetMap / Overpass API','source_url':endpoint,
                                     'retrieved_at':timestamp,'method':'nearby_entity_candidate_search','license':'ODbL-1.0'})
    if 'OpenStreetMap / Overpass API' not in prov['enrichment_sources']: prov['enrichment_sources'].append('OpenStreetMap / Overpass API')
    prov['enrichment_notes'] += ' Nearby OpenStreetMap entities searched via Overpass; candidate scores are uncalibrated and require manual review.'
    return rec


def empty_record(source, state='pending'):
    return {'source_fingerprint': fingerprint(source), 'geometry_family':source['family'],
            'administrative':{}, 'osm_entity':None, 'candidates':[],
            'match_quality':{'match_status':'no_match','match_score':None,'match_distance_m':None,
                             'match_method':None,'spatial_relation':None,'match_evidence':[], 'review_status':'not_reviewed'},
            'provenance':{'enrichment_status':state,'enrichment_sources':[], 'enrichment_notes':'No external enrichment completed.',
                          'enriched_at':None,'source_retrieved_at':None,'enrichment_version':'1.5.0','preferred_language':'en','source_provenance':[]}}


def enrich_one(source, agent):
    record = empty_record(source)
    lat,lon = source['location']
    url = 'https://nominatim.openstreetmap.org/reverse?' + urllib.parse.urlencode({'lat':f'{lat:.7f}','lon':f'{lon:.7f}','format':'jsonv2','addressdetails':1,'zoom':18,'namedetails':1,'accept-language':'en'})
    payload = request_json(url, agent)
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    if 'error' in payload: raise ValueError(payload['error'])
    record['administrative'] = address_from_nominatim(payload)
    # Nearest reverse-geocoding result is NOT a verified POI entity match.
    record['provenance'].update({'enrichment_status':'completed','enrichment_sources':['OpenStreetMap / Nominatim'],
        'enrichment_notes':'Administrative location obtained from OpenStreetMap through Nominatim (reverse geocoding).',
        'enriched_at':stamp, 'source_retrieved_at':stamp, 'preferred_language':'en',
        'source_provenance':[{'source':'OpenStreetMap / Nominatim','source_url':url,'retrieved_at':stamp,
                              'method':'reverse_geocoding','license':'ODbL-1.0'}]})
    return record


def completed_record_action(old, fingerprint_value, enabled, remaining_reverse_budget):
    """Reuse valid completed records if language refresh cannot run this pass.

    This allows Overpass matching on already-completed administrative records
    even when --max-requests 0. A later run with a reverse budget can refresh
    records lacking English-language provenance.
    """
    if not old or old.get('source_fingerprint') != fingerprint_value:
        return None
    if old.get('provenance', {}).get('enrichment_status') != 'completed':
        return None
    if old.get('provenance', {}).get('preferred_language') == 'en':
        return 'reuse'
    if not enabled or not remaining_reverse_budget:
        return 'reuse'
    return 'refresh'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--offline', action='store_true', help='Update schema and queues without external calls')
    parser.add_argument('--max-requests', type=int, default=None)
    parser.add_argument('--require-complete', action='store_true', help='Fail if eligible points are not fully enriched')
    parser.add_argument('--max-match-requests', type=int, default=0, help=argparse.SUPPRESS) # legacy ignored
    args = parser.parse_args()
    config = load('config/enrichment.json', {})
    previous = load('data/derived/enrichment.json', {'entities':{}})
    previous_entities = previous.get('entities', {})
    current = snapshot()
    max_requests = max(0, args.max_requests if args.max_requests is not None else config.get('max_requests_per_run', 10))
    agent = os.getenv('ENRICHMENT_USER_AGENT', '').strip()
    enabled = not args.offline and config.get('network_enabled', False) and bool(agent)
    count = 0; failures = 0; reused = 0; records = {}; updated = []; errors = []
    for uid,source in sorted(current.items()):
        fp = fingerprint(source)
        attempted = False
        old = previous_entities.get(uid)
        action = completed_record_action(old, fp, enabled, count < max_requests)
        if action == 'reuse':
            rec = old; reused += 1
        elif source['location'] is None:
            rec = empty_record(source, 'unsupported_geometry' if source['family'] != 'points' else 'invalid_geometry')
            rec['provenance']['enrichment_notes'] = 'Automated reverse geocoding not supported for this geometry.'
        elif enabled and count < max_requests:
            count += 1
            attempted = True
            try: rec = enrich_one(source, agent)
            except Exception as exc:
                failures += 1
                rec = old if old and old.get('source_fingerprint') == fp else empty_record(source, 'retry_pending')
                if rec['provenance']['enrichment_status'] != 'completed':
                    rec['provenance']['enrichment_status'] = 'retry_pending'
                    rec['provenance']['enrichment_notes'] = 'External service temporarily unavailable; enrichment will be retried.'
                details = {'globalid':uid, 'name':source['name'] or None, 'error_type':type(exc).__name__, 'error':str(exc)[:220]}
                errors.append(details)
                print(f'Enrichment failed {uid}: {type(exc).__name__}: {exc}')
            time.sleep(max(1.2, float(config.get('request_interval_seconds', 1.2))))
        else:
            rec = old if old and old.get('source_fingerprint') == fp else empty_record(source, 'pending')
        # Historical OSM match data is excluded from the Nominatim-only release.
        rec['osm_entity'] = None
        rec['candidates'] = []
        rec['match_quality'] = empty_record(source)['match_quality']
        records[uid] = rec
        # Per-run ledger: actual network attempts only, not records reused from cache.
        if attempted:
            admin = rec.get('administrative') or {}
            location = admin.get('locality') or admin.get('city') or admin.get('town') or admin.get('village')
            updated.append({'globalid':uid, 'name':source['name'] or None, 'geometry_family':source['family'],
                            'country':admin.get('country'), 'locality':location,
                            'enrichment_status':rec['provenance']['enrichment_status'],
                            'action':'reverse_geocoding'})
    out = {'schema_version':'1.0','enrichment_version':'1.5.0','entities':records,
           'attribution':'© OpenStreetMap contributors (ODbL 1.0); Nominatim'}
    atomic_write('data/derived/enrichment.json', out)
    statuses = {}
    for rec in records.values():
        status = rec['provenance']['enrichment_status']; statuses[status] = statuses.get(status,0)+1
    eligible = sum(1 for source in current.values() if source['location'] is not None)
    complete = statuses.get('completed', 0)
    report = {'total':len(records),'eligible_points':eligible,'completed':complete,
              'remaining_eligible': max(0,eligible-complete),
              'completion_percent':round(100*complete/eligible,2) if eligible else 100,
              'network_requests':count,'failed_requests':failures,
              'reused':reused,'by_status':statuses,'network_enabled':enabled,
              'updated_this_run':updated, 'errors_this_run':errors,
              'release_ready': eligible == complete and failures == 0}
    atomic_write('data/derived/enrichment-report.json', report)
    print(f'Enrichment: {len(records)} records, {count} Nominatim reverse requests, {reused} reused, {failures} failures')
    if failures: print('WARNING: Some enrichment requests failed; results and diagnostics saved for later retry.')
    if args.require_complete and not report['release_ready']:
        raise SystemExit(f'Incomplete enrichment: {report["remaining_eligible"]} eligible POIs remain, {failures} requests failed')

if __name__ == '__main__': main()
