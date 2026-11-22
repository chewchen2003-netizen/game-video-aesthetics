"""Portable pipeline. Replay is offline; measure/review are explicit operations."""
from pathlib import Path
import argparse,json,os,sys,subprocess,shutil,gzip,collections
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from validation import validate

def dump(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2))
def replay(ids,run):
 results=json.loads((ROOT/'data/results/results.json').read_text());results=[r for r in results if r['blind_id'] in ids]
 for r in results:
  errors=validate(r,r['blind_id'])
  if errors:raise ValueError((r['blind_id'],errors))
  d=run/r['blind_id'];d.mkdir(parents=True,exist_ok=True)
  for name in ['measurements.json','accepted-measurements.json','summary.json']:
   with gzip.open(ROOT/'data/measurements'/r['blind_id']/(name+'.gz'),'rt') as f:obj=json.load(f)
   dump(d/name,obj)
  accepted=json.loads((d/'accepted-measurements.json').read_text());counts=collections.Counter(o['object_id'] for row in accepted for o in row['objects'] if o.get('valid'))
  dump(d/'accepted-coverage.json',{'valid_mask_frames_by_object':dict(counts),'sample_count':len(accepted),'scope':'recomputed from accepted object flags; does not certify segmentation semantics'})
 dump(run/'results.json',results);dump(run/'distribution.json',dict(collections.Counter(r.get('grade') or r['status'] for r in results)));print('Replayed saved measurements and fixed predictions:',len(results),'samples; no model call.')

def main():
 p=argparse.ArgumentParser();p.add_argument('--mode',choices=['replay','prepare','measure','review'],default='replay');p.add_argument('--ids',nargs='+');p.add_argument('--run-dir',type=Path,default=ROOT/'runs/reproduction');p.add_argument('--raw-dir',type=Path);p.add_argument('--use-preview',action='store_true');p.add_argument('--model',default='gpt-6.1-sol');a=p.parse_args();run=a.run_dir.resolve();run.mkdir(parents=True,exist_ok=True)
 selection=json.loads((ROOT/'data/sources/selection.json').read_text());known={r['blind_id'] for r in selection};ids=a.ids or [r['blind_id'] for r in selection]
 if not set(ids)<=known:p.error('Unknown case ID')
 selection=[r for r in selection if r['blind_id'] in ids];dump(run/'selection.json',selection);cfg=json.loads((ROOT/'data/measurement-config.json').read_text());cfg['samples']=ids;dump(run/'config.json',cfg)
 (run/'assignments').mkdir(exist_ok=True)
 for bid in ids:shutil.copy2(ROOT/'data/assignments'/f'{bid}.json',run/'assignments'/f'{bid}.json')
 os.environ['GAME_EVAL_RUN_DIR']=str(run);os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK','1')
 if a.mode=='replay':replay(ids,run);return
 if a.mode in ['prepare','measure']:
  from frames import extract
  for r in selection:
   if a.raw_dir:
    video=a.raw_dir/Path(r['video']).name
    if not video.exists():video=a.raw_dir/(r['blind_id']+'.mp4')
   elif a.use_preview:video=ROOT/'docs'/r['video']
   else:p.error('Pass --raw-dir raw-inputs/videos, or explicitly --use-preview for a non-identical preview demonstration')
   if not video.exists():raise FileNotFoundError(video)
   extract(video,run,r['blind_id'],r['source_start'])
  dump(run/'input-provenance.json',{'kind':'compressed_web_preview' if a.use_preview and not a.raw_dir else 'original_clip','identical_to_original':bool(a.raw_dir),'note':'Preview measurements will differ from original-clip measurements.'})
  if a.mode=='prepare':print('Prepared',len(selection),'clips at 4 FPS');return
  subprocess.run([sys.executable,str(ROOT/'src/cv_measure.py')],check=True)
  for bid in ids:subprocess.run([sys.executable,str(ROOT/'src/summarize_measurements.py'),bid],check=True)
  print('Measurements ready; aesthetic grades require the separate review step.');return
 if a.mode=='review':
  codex=os.environ.get('CODEX_BIN') or shutil.which('codex')
  if not codex:p.error('Install/sign in to Codex CLI, or set CODEX_BIN to its executable')
  from build_review_task import task,SCHEMA
  schema=run/'terminal-output-schema.json';dump(schema,SCHEMA);results=[]
  for bid in ids:
   d=run/bid
   if not (d/'measurements.json').exists():p.error('Run measure before review: '+bid)
   subprocess.run([sys.executable,str(ROOT/'src/summarize_measurements.py'),bid],check=True);prompt=task(bid).read_text();request=run/'requests'/bid;request.mkdir(parents=True,exist_ok=True);out=request/'prediction.json';args=[codex,'exec','--ignore-user-config','--ephemeral','--sandbox','read-only','--skip-git-repo-check','-C',str(request),'--model',a.model,'--output-schema',str(schema),'--json','-o',str(out)]
   for pic in [run/'inputs'/bid/'overview.jpg',run/'inputs'/bid/'input-1.jpg',run/'inputs'/bid/'input-2.jpg',d/'measurement-qa.jpg']:args+=['-i',str(pic)]
   with (request/'cli-log.jsonl').open('w') as log:subprocess.run(args+['-'],input=prompt,text=True,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=900)
   for line in (request/'cli-log.jsonl').read_text().splitlines():
    try:event=json.loads(line)
    except ValueError:continue
    if event.get('item',{}).get('type') in ['command_execution','mcp_tool_call','web_search','file_change']:raise RuntimeError('Unexpected tool use; reject this inference and inspect isolation')
   result=json.loads(out.read_text());errors=validate(result,bid)
   if errors:raise ValueError((bid,errors))
   raw=json.loads((d/'measurements.json').read_text());rejects=result['measurement_qa']['rejections']
   for row in raw:
    for o in row['objects']:
     for q in rejects:
      if o['object_id']==q['object_id'] and (not q['frame_indices'] or row['frame_index'] in q['frame_indices']):
       if q['scope']=='mask':o['valid']=False;o['quality_rejection']=q['reason']
       elif q['scope']=='pose':o['rejected_pose']=o.get('pose');o['pose']={'valid':False,'joints':None,'reason':q['reason']}
       elif q['scope']=='depth' and o.get('depth'):o['depth'].update(valid=False,values=None,reason=q['reason'])
    accepted={o['object_id'] for o in row['objects'] if o.get('valid')};row['overlap_pairs']=[v for v in row['overlap_pairs'] if set(v['objects'])<=accepted]
   dump(d/'accepted-measurements.json',raw);result['requested_model']=a.model;result['human_labels_used']=False;dump(d/'pipeline-result.json',result);results.append(result)
  dump(run/'results.json',results);dump(run/'distribution.json',dict(collections.Counter(r.get('grade') or r['status'] for r in results)));print('Reviewed',len(results),'samples; source results not overwritten.')
if __name__=='__main__':main()
