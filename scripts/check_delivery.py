"""Check the frozen results, website references and source/sample consistency."""
from pathlib import Path
import json,sys,collections,gzip,re,hashlib,argparse
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));from validation import validate
p=argparse.ArgumentParser();p.add_argument('--raw-dir',type=Path);a=p.parse_args();rows=json.loads((ROOT/'data/results/results.json').read_text());sources=json.loads((ROOT/'data/sources/sources.json').read_text());assert len(rows)==50;assert len({r['blind_id'] for r in rows})==50
for r in rows:
 assert not validate(r,r['blind_id']),(r['blind_id'],validate(r,r['blind_id']));assert (ROOT/'docs'/r['video']).exists()
 for e in r['evidence']:assert (ROOT/'docs/composition-eval/operator-run-50-v1/inputs'/r['blind_id']/'frames'/f"frame-{e['frame_index']+1:04d}.jpg").exists()
 with gzip.open(ROOT/'data/measurements'/r['blind_id']/'measurements.json.gz','rt') as f:m=json.load(f)
 assert len(m)==80 and all(abs(x['time']-x['frame_index']/4)<1e-9 for x in m)
 if a.raw_dir:
  source=next(s for s in sources if s['blind_id']==r['blind_id']);file=a.raw_dir/Path(r['video']).name;assert hashlib.sha256(file.read_bytes()).hexdigest()==source['original_sha256']
counts=dict(collections.Counter(r['grade'] or r['status'] for r in rows));assert counts=={'middle':29,'high':20,'low':1}
for file in (ROOT/'docs').rglob('*.html'):
 for ref in re.findall(r'(?:src|href)=["\']([^"\']+)',file.read_text()):
  if any(x in ref for x in ['${','://','mailto:']) or ref.startswith('#'):continue
  assert (file.parent/ref.split('#')[0]).exists(),(file.name,ref)
print('PASS: 50 cases; 4000 timestamped measurement rows; distribution 20/29/1; page assets and optional original hashes.')
