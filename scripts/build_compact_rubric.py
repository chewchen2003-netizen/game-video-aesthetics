"""Create/check a compact reading copy that expands exactly to frozen v2 JSON."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from rubric_format import compact_rubric,expand_rubric,dumps_readable
from check_composition_rubric import check

rubric,lock=check()
compact=compact_rubric(rubric)
assert expand_rubric(compact)==rubric,'Lossless round-trip failed'
text=dumps_readable(compact)
assert expand_rubric(json.loads(text))==rubric,'Serialized round-trip failed'
path=ROOT/'rubrics/composition_rubric.compact.json';path.write_text(text)
manifest={'format':compact['_storage']['format'],'rubric_version':rubric['version'],'compact_file':'rubrics/composition_rubric.compact.json','compact_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'expands_to':'rubrics/composition_rubric.json','frozen_source_sha256':lock['sha256'],'semantic_equivalence':'Parsed JSON objects equal after expansion; original frozen source unchanged.'}
(ROOT/'rubrics/composition_rubric.compact.lock.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
for name in [path.name,'composition_rubric.compact.lock.json']:
    (ROOT/'docs/rubrics'/name).write_bytes((ROOT/'rubrics'/name).read_bytes())
old_lines=len((ROOT/'rubrics/composition_rubric.json').read_text().splitlines())
print(f'PASS: {old_lines} -> {len(text.splitlines())} lines; {path.stat().st_size} bytes; all 42 checks and all fields preserved exactly after expansion.')
