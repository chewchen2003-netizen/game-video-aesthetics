"""Rebuild the same trial RGB inputs from its published original clips, no answers read."""
from pathlib import Path
import argparse,json,sys,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from frames import extract
p=argparse.ArgumentParser();p.add_argument('--run-dir',required=True,type=Path);p.add_argument('--bundle',type=Path,default=ROOT/'docs/results/rubric-trial3');a=p.parse_args();d=a.run_dir.resolve();d.mkdir(parents=True,exist_ok=True)
if (d/'inputs').exists():raise SystemExit('Choose a new run directory; inputs already exist')
selection=json.loads((a.bundle/'selection.json').read_text())
for row in selection:
 video=a.bundle/row['trial_id']/'original.mp4'
 if hashlib.sha256(video.read_bytes()).hexdigest()!=row['original_sha256']:raise ValueError('Original clip hash differs')
 extract(video,d,row['trial_id'],row['clip_start'])
for name in ['selection.json','selection-policy.json','config.json']:shutil.copyfile(a.bundle/name,d/name)
(d/'assignments').mkdir(exist_ok=True)
print('Prepared',d)
