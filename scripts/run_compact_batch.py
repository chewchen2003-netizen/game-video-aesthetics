"""Frozen, single-rule compact 50-case rerun using raw CV caches and 3 VLM workers."""
from pathlib import Path
import argparse,json,os,sys,shutil,time,threading,concurrent.futures,hashlib,traceback,collections
PROJECT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run-dir',required=True,type=Path);a=ap.parse_args();d=a.run_dir.resolve();d.mkdir(parents=True,exist_ok=True)
 if (d/'process.json').exists():
  pid=json.loads((d/'process.json').read_text())['pid']
  try:os.kill(pid,0)
  except OSError:pass
  else:raise RuntimeError('A batch process is already running')
 start=time.time();save0=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
 save0(d/'process.json',{'pid':os.getpid(),'start_epoch':start});runtime=d/'runtime';runtime.mkdir(exist_ok=True)
 for name in ['scripts','src','rubrics']:
  if not (runtime/name).exists():shutil.copytree(PROJECT/name,runtime/name,ignore=shutil.ignore_patterns('__pycache__'))
 sys.path[:0]=[str(runtime/'scripts'),str(runtime/'src')]
 import run_five_calibration as m
 m.ROOT=PROJECT;m.D=d
 rulepath=runtime/'rubrics/composition_rubric.json';rule=m.load_rubric(rulepath);model_rule=m.compact_rubric(rule)
 for key in ['known_limits','freeze','judge']:model_rule.pop(key,None)
 assert 'R11' not in json.dumps(model_rule,ensure_ascii=False),'Case-specific feedback must not enter the grading rubric input'
 m.save(d/'model-rubric-input.json',model_rule)
 rulehash=hashlib.sha256(rulepath.read_bytes()).hexdigest();mu=threading.Lock();state={f'R{i:02d}':{'state':'queued'} for i in range(1,51)}
 selection=json.loads((PROJECT/'data/sources/selection.json').read_text());sources={x['blind_id']:x for x in json.loads((PROJECT/'data/sources/sources.json').read_text())};m.save(d/'selection.json',selection);m.save(d/'run-contract.json',{'rubric_version':rule['version'],'rubric_sha256':rulehash,'model':'gpt-6.1-sol','workers':3,'base_fps':2,'supplemental_fps':4,'output':'14 indicator records + events + temporal comparisons + final grade','cv':'reuse raw, uncurated measurement caches, not prior accept/reject decisions','timing':'new evidence preparation and VLM calls; cached CV not recomputed','human_answers_used':False,'previous_predictions_used':False,'rerun_all_50':True})
 def update(sid,phase_state,**extra):
  with mu:
   state[sid]={'state':phase_state,'epoch':time.time(),**extra};done=[x for x in state.values() if x['state']=='complete'];failed=[x for x in state.values() if x['state']=='failed'];elapsed=time.time()-start
   m.save(d/'progress.json',{'pid':os.getpid(),'rubric_version':rule['version'],'compact':True,'completed':len(done),'failed':len(failed),'total':50,'updated_epoch':time.time(),'elapsed_seconds':elapsed,'estimated_remaining_seconds':elapsed/len(done)*(50-len(done)) if done else None,'grades':dict(collections.Counter(x.get('grade') or x.get('status') for x in done)),'cases':state.copy()})
   with (d/'progress-events.jsonl').open('a') as f:f.write(json.dumps({'sample':sid,'state':phase_state,'epoch':time.time(),**extra},ensure_ascii=False)+'\n')
   if phase_state=='complete' and len(done)%5==0:m.save(d/'milestones'/f'{len(done):02d}.json',{'completed':len(done),'failed':len(failed),'elapsed_seconds':elapsed,'estimated_remaining_seconds':elapsed/len(done)*(50-len(done)),'grades':dict(collections.Counter(x.get('grade') or x.get('status') for x in done))})
 def task(s):
  sid=s['blind_id']
  try:
   work=d/'model-calls'/sid/'judge';out=work/'result.json'
   if (work/'validation.json').exists():
    r=json.loads(out.read_text());update(sid,'complete',grade=r['overall']['grade'],status=r['overall']['status'],resumed=True);return
   update(sid,'prepare',detail='复核来源，准备2FPS序列与原始测量缓存')
   raw=Path('/Users/minimax/game-video-review')/s['video'];assert hashlib.sha256(raw.read_bytes()).hexdigest()==sources[sid]['original_sha256'],'Source clip hash differs'
   evidence,images=m.bundle(sid)
   prompt='你是游戏视频构图评审。禁止工具调用与额外文件读取，仅用本次图像和文本。没有提供任何人工档位或既有预测，不预设档位分布。第一张是有序RGB序列，第二张是分割质量联系表，后面3张为0/10/19.5秒附近的清晰原帧。基础2FPS，部分时段补4FPS；原网格帧号不连续，必须按清单时间引用。先从RGB确认主体、陪体、环境与阶段，再核对缓存分割及测量，不把命名当真值；本轮未重跑CV。拒绝不可靠分割，拒绝项的派生数值不得作为依据。所有measurement_id逐项给accept/reject。未提供的时刻不声称看过；不编造光流、心理或数值。\n全片每个指标仅记录一次，共14项；baseline检查适用基础条件，enhancement检查进一步效果。通过events描述具体阶段及变化，各指标引用事件，不为每个阶段重复抄42行。condition_ids使用Rubric原子条件，至少引相关B条件；基础失败引用L，增强成立引用H。事件覆盖该指标重要阶段的变化和例外。基础明确失败判低；基础不确定且影响判档时无法判断；基础成立而增强未证明判中。技术手法未识别不扣档。仅给简洁可核查证据和理由，不写内部思维过程，不平均、投票或计手法数量。按下面这版规则判断，不能为追求某种分布强行升降档。尽量控制在4000token，必须保留14项、全部给定测量QA、时序对照和最终理由。实际附件别名Image #1至Image #5按上述顺序映射，但尽量引用rgb/measure清单中的精确ID。\nRubric:\n'+json.dumps(model_rule,ensure_ascii=False,separators=(',',':'))+'\nEvidence:\n'+json.dumps(evidence,ensure_ascii=False,separators=(',',':'))
   update(sid,'judge',detail=f'{len(evidence["RGB_frames"])}个时刻，14项精简评审；CV缓存已准备')
   for attempt in range(1,3):
    try:
     r=m.call(work,prompt,m.SCHEMA,images,out);report=m.validate(r,rule,evidence)
     manifest=json.loads((work/'input-images.json').read_text());m.save(work/'attachment-id-map.json',{'aliases':{'Image #'+str(i+1):v for i,v in enumerate(manifest)},'origin':'Actual supplied attachment order'})
     m.save(work/'validation.json',report);m.save(d/sid/'prediction.json',r);update(sid,'complete',grade=r['overall']['grade'],status=r['overall']['status'],attempts=attempt);return
    except Exception:
     (d/'logs').mkdir(exist_ok=True);(d/'logs'/f'{sid}-attempt-{attempt}.txt').write_text(traceback.format_exc())
     if work.exists():work.rename(work.with_name(f'judge-failed-{attempt}-{time.time_ns()}'))
     if attempt==2:raise
  except Exception as ex:update(sid,'failed',error=str(ex) or type(ex).__name__)
 update('batch','starting')
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(task,selection))
 results=[json.loads((d/s['blind_id']/'prediction.json').read_text()) for s in selection if (d/s['blind_id']/'prediction.json').exists()];m.save(d/'results.json',results);m.save(d/'distribution.json',dict(collections.Counter(r['overall']['grade'] or r['overall']['status'] for r in results)));p=json.loads((d/'progress.json').read_text());p.update(finished=True,finished_epoch=time.time());m.save(d/'progress.json',p)
if __name__=='__main__':main()
