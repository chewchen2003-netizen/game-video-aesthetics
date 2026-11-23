"""Verify frozen rubric identity, atomic checks and reference integrity (stdlib)."""
from pathlib import Path
import hashlib,json

ROOT=Path(__file__).resolve().parents[1]

def check():
    path=ROOT/'rubrics/composition_rubric.json'
    rubric=json.loads(path.read_text())
    lock=json.loads((ROOT/'rubrics/composition_rubric.lock.json').read_text())
    assert hashlib.sha256(path.read_bytes()).hexdigest()==lock['sha256'],'Frozen rubric changed: create a new version rather than replacing the lock.'
    assert rubric['version']==lock['version'] and rubric['rubric_id']==lock['rubric_id']
    assert rubric['freeze']['state']=='frozen_for_validation'
    assert len(rubric['factors'])==4
    indicators=[];checks=[]
    for factor in rubric['factors']:
        ids={x['id'] for x in factor['indicators']}
        indicators.extend(ids)
        assert 'weight' not in factor
        for grade in ['low','middle','high']:
            points=factor['scoring_guidance'][grade]['checks']
            assert len(points)==len(ids)
            assert {x['indicator_id'] for x in points}==ids
            assert all(isinstance(x['indicator_id'],str) and x['condition'] and x['required_evidence'] for x in points)
            checks.extend(x['id'] for x in points)
        assert factor['scoring_guidance']['high']['inherits']=='middle'
    assert len(indicators)==len(set(indicators))==lock['indicator_count']==14
    assert len(checks)==len(set(checks))==lock['checkpoint_count']==42
    overall=rubric['overall_scoring_guidance']
    known=set(checks)|{x['id'] for grade in ['low','middle','high'] for x in overall[grade]['checks']}
    for grade in ['low','middle','high']:
        for point in overall[grade]['checks']:
            assert set(point.get('references',[]))<=known,point['id']
    assert overall['high']['inherits']=='middle'
    assert rubric['scope']['numeric_aesthetic_score'] is False
    public=ROOT/'docs/rubrics/composition_rubric.json'
    if public.exists():assert public.read_bytes()==path.read_bytes(),'Public rule copy differs'
    return rubric,lock

if __name__=='__main__':
    _,lock=check()
    print(f"PASS: rubric v{lock['version']}; 4 factors; 14 indicators; 42 atomic checks; frozen SHA256 and references verified.")
