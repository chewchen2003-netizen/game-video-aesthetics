"""Publish frozen compact50 predictions and their actual input evidence."""
from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[1];run=ROOT/'runs/composition-v23-compact50-clean';out=ROOT/'docs/results/composition-v23-review';out.mkdir(parents=True,exist_ok=True)
sources={s['blind_id']:s for s in json.loads((ROOT/'data/sources/sources.json').read_text())};items=[]
for sid in [f'R{x:02}' for x in range(1,51)]:
 dest=out/sid;dest.mkdir(exist_ok=True);src=sources[sid];pred=json.loads((run/sid/'prediction.json').read_text());frames=json.loads((run/'inputs'/sid/'frames.json').read_text())
 for f in frames:
  p=run/'inputs'/f['image'];target=dest/'frames'/p.name;target.parent.mkdir(exist_ok=True);shutil.copyfile(p,target);f['url']=f'{sid}/frames/{p.name}'
 for source,target in [(run/sid/'prediction.json','prediction.json'),(run/'inputs'/sid/'input-sequence.jpg','input-sequence.jpg'),(run/'evidence'/sid/'mask-qa.jpg','mask-qa.jpg'),(run/'evidence'/sid/'raw-measurements.json','raw-measurements.json'),(run/'evidence'/sid/'model-evidence.json','model-evidence.json')]:shutil.copyfile(source,dest/target)
 call=run/'model-calls'/sid/'judge';cd=dest/'call';cd.mkdir(exist_ok=True)
 for name in ['prompt.txt','schema.json','validation.json','attachment-id-map.json']:
  if (call/name).exists():shutil.copyfile(call/name,cd/name)
 video=ROOT/'docs'/src['video'];assert video.exists(),video
 items.append(dict(id=sid,game=src['game'],original=src['sample_number'],video='../../'+src['video'],source_start=src['source_start'],frames=frames,prediction=pred))
(out/'data.json').write_text(json.dumps(items,ensure_ascii=False,separators=(',',':')))
shutil.copyfile(run/'model-rubric-input.json',out/'model-rubric-input.json')
print('Published',len(items),'cases')
