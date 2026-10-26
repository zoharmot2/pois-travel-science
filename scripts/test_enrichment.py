"""Offline executable unit smoke tests for v1.5 enrichment."""
from enrich_data import norm, coordinates, empty_record, address_from_nominatim, candidate_from_nominatim, fingerprint


def test():
    uid = '{D7ADB267-C598-47C1-9452-E9C7BE402A96}'
    assert norm(uid) == 'd7adb267-c598-47c1-9452-e9c7be402a96'
    assert norm('not an ID') is None
    assert coordinates({'type':'Point','coordinates':[35,31]}) == (31,35)
    assert coordinates({'type':'LineString','coordinates':[[35,31],[36,32]]}) is None
    source={'family':'points','location':(31,35),'name':'Example'}
    assert fingerprint(source)!=fingerprint({**source,'name':'Renamed'})
    payload={'address':{'country':'Example Country','city':'Example City'},'display_name':'Example City, Example Country', 'osm_type':'way','osm_id':123,'category':'building','type':'yes'}
    admin=address_from_nominatim(payload)
    assert admin['country']=='Example Country' and admin['locality']=='Example City'
    assert empty_record(source)['osm_entity'] is None
    assert empty_record(source)['provenance']['preferred_language'] == 'en'
    print('PASS: offline enrichment smoke tests')

if __name__=='__main__': test()

def test_completed_record_reuse():
    from enrich_data import completed_record_action
    old = {'source_fingerprint':'abc', 'provenance': {'enrichment_status':'completed'}}
    assert completed_record_action(old,'abc',True,False)=='reuse'
    assert completed_record_action(old,'abc',True,True)=='refresh'
    assert completed_record_action(old,'abc',False,True)=='reuse'
    assert completed_record_action(old,'different',True,False) is None
    old['provenance']['preferred_language']='en'
    assert completed_record_action(old,'abc',True,True)=='reuse'
    print('PASS: completed records survive zero-budget language refresh')

if __name__=='__main__': test_completed_record_reuse()


