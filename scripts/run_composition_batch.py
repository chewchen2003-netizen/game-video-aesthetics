"""Detached, resumable 50-case pipeline with bounded model/GPU concurrency."""
import argparse,concurrent.futures,collections,json,os,shutil,subprocess,sys,threading,time,traceback,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');t.replace(p)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run-dir',type=Path,required=True);ap.add_argument('--thread-id',default='');a=ap.parse_args();d=a.run_dir.resolve();d.mkdir(parents=True,exist_ok=True)
 if (d/'process.json').exists():
  old=json.loads((d/'process.json').read_text())
  try:os.kill(old['pid'],0)
  except OSError:pass
  else:raise RuntimeError('Batch process is already running')
 save(d/'process.json',{'pid':os.getpid(),'start_epoch':time.time(),'thread_id':a.thread_id})
 runtime=d/'runtime';runtime.mkdir(exist_ok=True)
 for name in ['scripts','src','rubrics']:
  if not (runtime/name).exists():shutil.copytree(ROOT/name,runtime/name,ignore=shutil.ignore_patterns('__pycache__'))
 (runtime/'data').mkdir(exist_ok=True);shutil.copyfile(ROOT/'data/measurement-config.json',runtime/'data/measurement-config.json')
 selection=json.loads((ROOT/'data/sources/selection.json').read_text());sources={x['blind_id']:x for x in json.loads((ROOT/'data/sources/sources.json').read_text())};save(d/'selection.json',selection)
 cfg=json.loads((ROOT/'data/measurement-config.json').read_text());cfg.update(measurement_fps=2,adaptive_sampling=True,input_batch='inputs',samples=[s['blind_id'] for s in selection],human_answers_used=False);save(d/'config.json',cfg);(d/'assignments').mkdir(exist_ok=True)
 lock=json.loads((runtime/'rubrics/composition_rubric.lock.json').read_text());save(d/'run-contract.json',{'rubric_version':lock['version'],'rubric_sha256':lock['sha256'],'model':'gpt-6.1-sol','workers':3,'model_parallelism':2,'cv_parallelism':1,'fps':2,'adaptive_fps':4,'max_frames':56,'human_answers_used':False,'old_predictions_used':False,'same_original_50':True,'input_mode':'lean-measurements-v1; full raw measurements saved; original RGB sequence retained','temporal_analysis_required':True,'notification_every':5})
 mu=threading.Lock();llm=threading.Semaphore(2);gpu=threading.Lock();notify_lock=threading.Lock();state={x['blind_id']:{'state':'queued'} for x in selection};start=time.time();notified=set();events=d/'progress-events.jsonl'
 def update(sid,phase_state,**extra):
  with mu:
   state[sid]={'state':phase_state,'epoch':time.time(),**extra};done=[x for x in state.values() if x['state']=='complete'];fail=[x for x in state.values() if x['state']=='failed'];elapsed=time.time()-start
   snapshot={'pid':os.getpid(),'rubric_version':lock['version'],'updated_epoch':time.time(),'completed':len(done),'failed':len(fail),'total':50,'elapsed_seconds':elapsed,'estimated_remaining_seconds':elapsed/len(done)*(50-len(done)) if done else None,'grades':dict(collections.Counter(x.get('grade') or x.get('status') for x in done)),'cases':state.copy()};save(d/'progress.json',snapshot)
   with events.open('a') as f:f.write(json.dumps({'sample':sid,'state':phase_state,'epoch':time.time(),**extra},ensure_ascii=False)+'\n')
   n=len(done)
   if n and (n%5==0 or n==50) and n not in notified:
    notified.add(n);message=f"后台构图复跑进度：已完成 {n}/50，失败 {len(fail)} 条；档位分布 {snapshot['grades']}；运行 {elapsed/60:.1f} 分钟。剩余时间粗估 {snapshot['estimated_remaining_seconds']/60:.0f} 分钟（小样本估计会波动）。详情：{d/'progress.json'}。这是用户要求的每5条进度通知，不改变当前聊天任务。"
    save(d/'milestones'/f'{n:02d}.json',{'completed':n,'message':message,'epoch':time.time()})
    threading.Thread(target=deliver,args=(n,message),daemon=True).start()
 def deliver(n,message):
  try:
   from batch_progress_notify import notify
   result=notify(a.thread_id,message) if a.thread_id else {'delivered':False,'reason':'no target thread'}
  except Exception as exc:result={'delivered':False,'reason':str(exc)}
  save(d/'milestones'/f'{n:02d}-delivery.json',result)
 def invoke(sid,phase):
  script=runtime/'scripts/run_rubric_trial.py';cmd=[sys.executable,str(script),'--run-dir',str(d),'--ids',sid,'--phase',phase,'--lean','--temporal'];env=os.environ.copy();env.update(GAME_EVAL_RUN_DIR=str(d),GAME_EVAL_SAMPLE_IDS=sid,GAME_EVAL_MODELS_DIR='/Users/minimax/game-video-review/composition-eval/operator-run-50-v1/models',HF_HUB_OFFLINE='1',PYTORCH_ENABLE_MPS_FALLBACK='1')
  semaphore=gpu if phase=='measure' else llm
  with semaphore:
   update(sid,phase)
   for attempt in range(1,3):
    log=d/'logs'/f'{sid}-{phase}-{attempt}.log';log.parent.mkdir(exist_ok=True)
    with log.open('w') as f:proc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=env,timeout=2400)
    if proc.returncode==0:return
    work=d/'model-calls'/sid/phase
    if work.exists():work.rename(work.with_name(phase+f'-failed-{int(time.time())}'))
    if attempt==2:raise RuntimeError(f'{phase} failed twice; see {log}')
 def worker(s):
  sid=s['blind_id']
  try:
   if (d/sid/'prediction.json').exists():
    r=json.loads((d/sid/'prediction.json').read_text());update(sid,'complete',grade=r['overall']['grade'],status=r['overall']['status'],resumed=True);return
   update(sid,'prepare')
   raw=Path('/Users/minimax/game-video-review')/s['video'];assert hashlib.sha256(raw.read_bytes()).hexdigest()==sources[sid]['original_sha256'],'Source video differs'
   old_inputs=Path('/Users/minimax/game-video-review/composition-eval/operator-run-50-v1/inputs')/sid
   sys.path.insert(0,str(runtime/'src'))
   from adaptive_frames import prepare,supplement
   if not (d/'inputs'/sid/'frames.json').exists():prepare(old_inputs,d,sid)
   frames=json.loads((d/'inputs'/sid/'frames.json').read_text());assert 40<=len(frames)<=56 and all(e['frame_index']%2==0 for e in frames if e.get('sampling_reason')=='base_2fps')
   # No old assignments, predictions, accepted/rejected decisions or human notes copied.
   invoke(sid,'identify')
   assfile=d/'assignments'/f'{sid}.json';ass=json.loads(assfile.read_text());requests=ass.get('supplemental_frame_requests',[])
   if requests:
    added=supplement(old_inputs,d,sid,requests)
    for o in ass['objects']:
     if o['role']=='subject':o['active_frame_ranges']=[[min(f['frame_index'] for f in added if seg['range'][0]<=f['time']<seg['range'][1]),max(f['frame_index'] for f in added if seg['range'][0]<=f['time']<seg['range'][1])] for seg in ass['segments'] if o['id'] in seg['primary'] and any(seg['range'][0]<=f['time']<seg['range'][1] for f in added)]
    save(assfile,ass)
   invoke(sid,'measure');invoke(sid,'judge')
   r=json.loads((d/sid/'prediction.json').read_text());update(sid,'complete',grade=r['overall']['grade'],status=r['overall']['status'])
  except Exception as exc:update(sid,'failed',error=str(exc));(d/'logs'/f'{sid}-error.txt').write_text(traceback.format_exc())
 update('batch','starting')
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(worker,selection))
 snapshot=json.loads((d/'progress.json').read_text());snapshot['finished']=True;snapshot['finished_epoch']=time.time();save(d/'progress.json',snapshot)
 # Allow a queued final notification to finish without holding the actual workers.
 for t in threading.enumerate():
  if t is not threading.current_thread() and t.daemon:t.join(timeout=2)
if __name__=='__main__':main()
