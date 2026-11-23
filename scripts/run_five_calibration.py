"""Paired five-clip calibration: identical evidence and compact output, two rule arms.
No prior aesthetic labels, prior predictions or human comments enter model inputs.
Raw uncurated CV caches are reused and their origin is recorded, not timed as new CV.
"""
from pathlib import Path
import sys,json,time,os,shutil,threading,concurrent.futures,collections,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from rubric_format import load_rubric,compact_rubric
from adaptive_frames import prepare
from run_rubric_trial import call,obj,arr,enum,S,N,I,B
from PIL import Image,ImageDraw
D=ROOT/'runs/composition-five-calibration';IDS=['R01','R05','R11','R12','R49'];ARMS={'baseline':'baseline-v2.2.0','candidate':'candidate-v2.3.0'}
STATE=enum('met','not_met','insufficient_evidence','not_applicable');NULLGRADE={'type':['string','null'],'enum':['low','middle','high',None]}
SCHEMA=obj(sample_id=S,roles=arr(obj(object_id=S,role=enum('subject','supporting_element','foreground','background','unknown'),time_range=arr(N),description=S,uncertainty=S)),stages=arr(obj(stage_id=S,time_range=arr(N),necessary_information=S,input_evidence_ids=arr(S))),segmentation_review=arr(obj(measurement_id=S,accepted=B,reason=S)),indicators=arr(obj(indicator_id=S,baseline=STATE,enhancement=STATE,condition_ids=arr(S),event_ids=arr(S),uncertainty=S)),events=arr(obj(event_id=S,time_ranges=arr(arr(N)),input_evidence_ids=arr(S),observation=S,effect=S,exceptions_checked=S)),temporal_analysis=arr(obj(before_evidence_ids=arr(S),after_evidence_ids=arr(S),visible_change=S,spatial_or_attention_effect=S,expressive_effect=S)),overall=obj(status=enum('scored','uncertain','not_applicable'),grade=NULLGRADE,condition_ids=arr(S),decisive_event_ids=arr(S),reason=S,adjacent_grade_explanation=S,uncertainties=arr(S)))
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+f'.{threading.get_ident()}.tmp');tmp.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bundle(sid):
 current=ROOT/'runs/composition-v22-batch50-fps2';old=Path('/Users/minimax/game-video-review/composition-eval/operator-run-50-v1');base=current if (current/sid/'measurements.json').exists() else old;source=old/'inputs'/sid
 if (current/'inputs'/sid/'frames.json').exists():shutil.copytree(current/'inputs'/sid,D/'inputs'/sid,dirs_exist_ok=True)
 else:prepare(source,D,sid)
 frames=json.loads((D/'inputs'/sid/'frames.json').read_text());source_start=next(x['source_start'] for x in json.loads((ROOT/'data/sources/selection.json').read_text()) if x['blind_id']==sid)
 for frame in frames:frame.setdefault('source_time',source_start+frame['time'])
 fullrows=json.loads((base/sid/'measurements.json').read_text());frame_map={f['frame_index']:f for f in frames};available=[r for r in fullrows if r['frame_index'] in frame_map];chosen=[]
 for t in [0,4,8,12,16,19.5]:
  row=min(available,key=lambda r:abs(r['time']-t))
  if row['frame_index'] not in [r['frame_index'] for r in chosen]:chosen.append(row)
 dest=D/'evidence'/sid;dest.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/sid/'measurements.json',dest/'raw-measurements.json')
 values=[];qa=Image.new('RGB',(1280,384*((len(chosen)+1)//2)),'#14222d');draw=ImageDraw.Draw(qa)
 for k,row in enumerate(chosen):
  index=row['frame_index'];raw=Image.open(D/'inputs'/frame_map[index]['image']).convert('RGB');overlay=raw.copy()
  import numpy as np
  rgb=np.array(overlay)
  for j,o in enumerate(row['objects']):
   mask=base/o['mask_file'] if o.get('mask_file') else None
   if mask and mask.exists():
    m=np.array(Image.open(mask))>0;rgb[m]=(rgb[m]*.65+np.array([(60+83*j)%255,(200+47*j)%255,(120+97*j)%255])*.35).astype('uint8')
   pos=o.get('position',{});sep=o.get('background_separation',{});dep=o.get('depth',{});pose=o.get('pose',{});joints=pose.get('joints') or {}
   values.append({'id':f'measure-{index:04d}-{o["object_id"]}','frame_index':index,'time':row['time'],'object_id':o['object_id'],'valid':o.get('valid'),'bbox':pos.get('bbox_xyxy'),'center':pos.get('center'),'edge_distances':pos.get('edge_distances'),'visible_ratio':o.get('area',{}).get('visible_ratio'),'color_JS':sep.get('color_JS_distance'),'boundary_Lstar_median':(sep.get('boundary_Lstar') or {}).get('median'),'relative_inverse_depth_median':(dep.get('values') or {}).get('median') if dep.get('valid') else None,'joints':{n:v['xy'] for n,v in joints.items() if v.get('valid')},'occlusion_ratio':None})
  overlay=Image.fromarray(rgb);od=ImageDraw.Draw(overlay)
  for o in row['objects']:
   b=o.get('position',{}).get('bbox_xyxy')
   if b:od.rectangle(b,outline='#ffac5b',width=3);od.text((b[0],max(0,b[1]-16)),o['object_id'],fill='#ffac5b')
  overlay.thumbnail((640,360));x=k%2*640;y=k//2*384;qa.paste(overlay,(x,y));draw.text((x+5,y+362),f'{sid} mask QA #{index} {row["time"]:.2f}s',fill='white')
 qa.save(dest/'mask-qa.jpg',quality=92)
 images=[D/'inputs'/sid/'input-sequence.jpg',dest/'mask-qa.jpg']
 for t in [0,10,19.5]:
  f=min(frames,key=lambda x:abs(x['time']-t));images.append(D/'inputs'/f['image'])
 evidence={'sample_id':sid,'RGB_frames':[{'id':f'rgb-{f["frame_index"]:04d}','frame_index':f['frame_index'],'time':f['time'],'source_time':f['source_time']} for f in frames],'measurements':values,'units':'center/edge/area normalized to frame; visible mask area is not bbox area; Lab JS 0..1, L* difference 0..100; relative monocular inverse depth, not meters; no amodal mask, no occlusion percent','provenance':{'measurement_cache_sha256':sha(base/sid/'measurements.json'),'measurement_cache_kind':'raw, uncurated CV results; no old accept/reject decisions or grades supplied','cache_origin':str(base),'cv_recomputed':False,'sampled_frames':len(frames)}}
 save(dest/'model-evidence.json',evidence);save(dest/'input-files.json',[{'name':x.name,'sha256':sha(x)} for x in images]);return evidence,images

def validate(r,rule,evidence):
 known={i['id'] for f in rule['factors'] for i in f['indicators']};points={p['id']:p['indicator_id'] for f in rule['factors'] for g in f['scoring_guidance'].values() for p in g['checks']};assert len(r['indicators'])==14 and {x['indicator_id'] for x in r['indicators']}==known
 refs={x['id'] for x in evidence['RGB_frames']}|{x['id'] for x in evidence['measurements']}|{'Image #'+str(i) for i in range(1,6)};measure={x['id'] for x in evidence['measurements']};events={x['event_id'] for x in r['events']};assert len(events)==len(r['events'])
 assert {x['measurement_id'] for x in r['segmentation_review']}==measure
 for e in r['events']:
  assert e['input_evidence_ids'] and set(e['input_evidence_ids'])<=refs
  for lo,hi in e['time_ranges']:assert 0<=lo<=hi<=20
 for x in r['indicators']:
  assert all(points[c]==x['indicator_id'] for c in x['condition_ids']);assert set(x['event_ids'])<=events
  if x['baseline']=='not_met' or x['enhancement']=='met':assert x['event_ids'] and x['condition_ids']
 for t in r['temporal_analysis']:assert t['before_evidence_ids'] and t['after_evidence_ids'] and set(t['before_evidence_ids']+t['after_evidence_ids'])<=refs
 assert r['temporal_analysis']
 o=r['overall'];assert (o['status']=='scored')==(o['grade'] in ['low','middle','high']);assert set(o['decisive_event_ids'])<=events
 core=[x for x in r['indicators'] if not x['indicator_id'].startswith('technique-')]
 if any(x['baseline']=='not_met' for x in core):assert o['grade']=='low'
 if o['grade'] in ['middle','high']:assert all(x['baseline'] in ['met','not_applicable'] for x in core)
 if o['grade']=='high':assert any(x['enhancement']=='met' for x in r['indicators']) and o['decisive_event_ids']
 return {'passed':True,'indicators':14,'temporal_records':len(r['temporal_analysis']),'measurement_QA_records':len(measure)}

def main():
 D.mkdir(exist_ok=True);save(D/'process.json',{'pid':os.getpid(),'start_epoch':time.time()});start=time.time();mu=threading.Lock();state={s:{'state':'queued'} for s in IDS};prepared={};counts={s:0 for s in IDS};rules={a:load_rubric(D/'rubrics'/(name+'.json')) for a,name in ARMS.items()}
 save(D/'design.json',{'samples':IDS,'arms':ARMS,'same_inputs_between_arms':True,'same_compact_output_between_arms':True,'human_labels_in_model_inputs':False,'selection':'Two current middles plus previously discussed human reference cases; calibration only, not independent test','timing_scope':'model calls plus evidence preparation; cached CV not rerun or claimed as newly measured'})
 def update(sid,phase_state,**kwargs):
  with mu:
   state[sid]={'state':phase_state,'epoch':time.time(),**kwargs};done=sum(v['state']=='complete' for v in state.values());failed=sum(v['state']=='failed' for v in state.values());save(D/'progress.json',{'pid':os.getpid(),'rubric_version':'v2.2 vs v2.3-candidate','completed':done,'failed':failed,'total':5,'comparison':True,'updated_epoch':time.time(),'elapsed_seconds':time.time()-start,'estimated_remaining_seconds':None,'cases':state.copy()})
 for sid in IDS:update(sid,'prepare');prepared[sid]=bundle(sid)
 def worker(pair):
  sid,arm=pair;work=D/'model-calls'/sid/arm;out=work/'result.json';rule=rules[arm];evidence,images=prepared[sid]
  try:
   update(sid,'judge',detail='同输入双规则对照；精简14项输出')
   prompt='你是游戏视频构图评审。禁止工具调用与额外文件读取，仅用本次图像和文本。没有提供任何人工档位或既有预测，不预设档位分布。第一张是有序RGB序列，第二张是分割质量联系表，后面3张为0/10/19.5秒附近的清晰原帧。基础2FPS，部分时段补4FPS；原网格帧号不连续，必须按清单时间引用。先从RGB确认主体、陪体、环境与阶段，再核对缓存分割及测量，不把命名当真值；本轮未重跑CV。拒绝不可靠分割，拒绝项的派生数值不得作依据。所有measurement_id逐项给accept/reject。未提供的时刻不声称看过；不编造光流、心理或数值。\n采用精简无损组织：全片每个指标仅记录一次，共14项；baseline检查当前适用基础条件，enhancement检查进一步效果。通过events描述具体阶段或前后变化，各指标引用事件，不重复为每个阶段抄42行。condition_ids对应Rubric原子条件，至少引相关B条件；基础失败引用L，增强成立引用H。事件覆盖该指标在重要阶段的变化和例外。基线明确失败判低，基线不确定且影响判档时无法判断，基线成立而增强未证明判中。技术手法未识别不扣档。仅给简洁的可核查证据与理由，不写内部思维过程，不用平均/投票或手法计数。所有论断按下面这版规则，不能自行降低或抬高门槛。尽量将输出控制在4000token以内，但必须保留14项、全部给定测量QA、前后时序证据和最终理由。\nRubric:\n'+json.dumps(compact_rubric(rule),ensure_ascii=False,separators=(',',':'))+'\nEvidence:\n'+json.dumps(evidence,ensure_ascii=False,separators=(',',':'))
   result=call(work,prompt,SCHEMA,images,out);report=validate(result,rule,evidence);save(work/'validation.json',report)
   with mu:counts[sid]+=1;complete=counts[sid]==2
   if complete:
    results={a:json.loads((D/'model-calls'/sid/a/'result.json').read_text()) for a in ARMS};save(D/sid/'comparison.json',results);update(sid,'complete',grade=results['candidate']['overall']['grade'],status=results['candidate']['overall']['status'])
  except Exception as e:update(sid,'failed',error=f'{arm}: {e}')
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(worker,[(s,a) for s in IDS for a in ARMS]))
 p=json.loads((D/'progress.json').read_text());p.update(finished=True,finished_epoch=time.time());save(D/'progress.json',p)
if __name__=='__main__':main()
