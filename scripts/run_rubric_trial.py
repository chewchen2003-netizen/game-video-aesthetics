"""Isolated two-pass RGB identification -> CV measurements -> rubric VLM evaluation.
Uses Codex CLI authentication, not a claimed public API integration. No old answers copied.
"""
import argparse,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from rubric_format import load_rubric
CLI=os.environ.get('CODEX_BIN',shutil.which('codex') or '/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex')
def obj(**kw):return {'type':'object','properties':kw,'required':list(kw),'additionalProperties':False}
def arr(x):return {'type':'array','items':x}
S={'type':'string'};N={'type':'number'};I={'type':'integer'};B={'type':'boolean'}
def enum(*v):return {'type':'string','enum':list(v)}
RANGE=arr(N)
ASSIGN=obj(objects=arr(obj(id=S,kind=enum('humanoid','vehicle','scene_region','object'),description=S,role=enum('subject','supporting_element','foreground','background'),anchors=arr(obj(frame_index=I,box=arr(N))))),segments=arr(obj(id=S,range=RANGE,primary=arr(S),necessary_information=S,visible_content=S,evidence_frames=arr(I))),uncertainties=arr(S))
CHECK=obj(checkpoint_id=S,indicator_id=S,stage_id=S,state=enum('met','not_met','insufficient_evidence','not_applicable'),time_ranges=arr(RANGE),input_evidence_ids=arr(S),observation=S,impact=S,context_support=S,exceptions_checked=arr(S),event_ids=arr(S),uncertainty=S)
EVENT=obj(event_id=S,object_ids=arr(S),time_ranges=arr(RANGE),arrangement=S,basic_or_expressive_effect=S,context_support=S,checkpoint_ids=arr(S))
QA=obj(frame_index=I,object_id=S,mask_accepted=B,reason=S)
RESULT=obj(sample_id=S,stages=arr(obj(stage_id=S,time_range=RANGE,subject_ids=arr(S),supporting_element_ids=arr(S),foreground_ids=arr(S),background_ids=arr(S),necessary_information=S,key_stage_reason=S,input_evidence_ids=arr(S))),segmentation_review=arr(QA),checks=arr(CHECK),events=arr(EVENT),factors=arr(obj(factor_id=S,grade={'type':['string','null'],'enum':['low','middle','high',None]},recognition=enum('present','not_identified','uncertain','not_applicable'),reason=S)),overall=obj(status=enum('scored','uncertain','not_applicable'),grade={'type':['string','null'],'enum':['low','middle','high',None]},baseline_status=S,material_harm_status=S,expressive_enhancement_status=S,overall_condition_ids=arr(S),decisive_checkpoint_ids=arr(S),decisive_event_ids=arr(S),reason=S,adjacent_grade_explanation=S,uncertainties=arr(S)))
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def call(work,prompt,schema,images,out):
 work.mkdir(parents=True,exist_ok=True);save(work/'schema.json',schema);(work/'prompt.txt').write_text(prompt)
 from PIL import Image
 manifest=[{'id':p.name,'path':str(p),'sha256':sha(p),'dimensions':list(Image.open(p).size)} for p in images];save(work/'input-images.json',manifest)
 cmd=[CLI,'exec','--ignore-user-config','--ephemeral','--sandbox','read-only','--skip-git-repo-check','-C',str(work),'--model','gpt-6.1-sol','--output-schema',str(work/'schema.json'),'--json','-o',str(out)]
 for p in images:cmd+=['-i',str(p)]
 cmd+=['-'];start=time.time()
 with (work/'events.jsonl').open('w') as f:
  proc=subprocess.run(cmd,input=prompt,text=True,stdout=f,stderr=subprocess.STDOUT,timeout=1800)
 save(work/'execution.json',{'requested_model':'gpt-6.1-sol','transport':'Codex CLI, local authenticated session','actual_model':'see raw events; not independently certified','start_epoch':start,'elapsed_seconds':time.time()-start,'returncode':proc.returncode,'human_answers_used':False,'command':cmd})
 if proc.returncode:raise RuntimeError(str(work/'events.jsonl'))
 for line in (work/'events.jsonl').read_text().splitlines():
  try:ev=json.loads(line)
  except ValueError:continue
  if ev.get('item',{}).get('type') in ['command_execution','mcp_tool_call','web_search','file_change']:raise RuntimeError('Unexpected tool use: isolation violation')
 return json.loads(out.read_text())
def validate(r,rule,frames,measured):
 points={p['id']:p for f in rule['factors'] for g in f['scoring_guidance'].values() for p in g['checks']};stages={s['stage_id'] for s in r['stages']};events={e['event_id'] for e in r['events']};ids=set(frames)|set(measured);seen=set()
 def times(ranges):
  for rg in ranges:
   assert len(rg)==2 and 0<=rg[0]<=rg[1]<=20,('invalid time',rg)
 for c in r['checks']:
  assert c['checkpoint_id'] in points
  assert c['indicator_id']==points[c['checkpoint_id']]['indicator_id']
  assert c['stage_id'] in stages
  key=(c['stage_id'],c['checkpoint_id']);assert key not in seen;seen.add(key)
  assert set(c['input_evidence_ids'])<=ids,('unknown evidence',c['input_evidence_ids'])
  assert set(c['event_ids'])<=events;times(c['time_ranges'])
  if c['state']=='met':assert c['input_evidence_ids'] and c['observation']
 for st in stages:assert {p for s,p in seen if s==st}==set(points),('incomplete checks',st)
 for e in r['events']:assert set(e['checkpoint_ids'])<=set(points);times(e['time_ranges'])
 o=r['overall'];assert (o['status']=='scored')==(o['grade'] in ['low','middle','high'])
 assert set(o['decisive_checkpoint_ids'])<=set(points);assert set(o['decisive_event_ids'])<=events
 assert {(q['frame_index'],q['object_id']) for q in r['segmentation_review']}==set(measured.values()),'Missing mask QA'
 for st in r['stages']:
  times([st['time_range']]);assert set(st['input_evidence_ids'])<=ids
 for q in r['segmentation_review']:assert (q['frame_index'],q['object_id']) in measured.values()
 core=[c for c in r['checks'] if c['checkpoint_id'][0] in 'PCS']
 low_met=[c for c in core if '-L-' in c['checkpoint_id'] and c['state']=='met']
 base_failed=[c for c in core if '-B-' in c['checkpoint_id'] and c['state']=='not_met']
 if low_met or base_failed:assert o['grade']=='low','Confirmed baseline failure must route to low'
 if o['grade'] in ['middle','high']:
  assert all(c['state'] in ['met','not_applicable'] for c in core if '-B-' in c['checkpoint_id']),'Unresolved baseline cannot support middle/high'
 if o['grade']=='low':assert low_met or base_failed,'Low lacks confirmed baseline failure'
 if o['grade']=='high':assert any('-H-' in c['checkpoint_id'] and c['state']=='met' for c in r['checks']) and o['decisive_event_ids'],'High lacks enhancement/event evidence'
 return {'passed':True,'checks':len(r['checks']),'stages':len(stages),'note':'Structural/reference validation only; independent human review pending.'}
def lean_row(row):
 # Preserve numerical values without rounding. Omit repetitive model metadata and
 # auxiliary histograms; full unabridged measurements remain saved separately.
 packed={'frame_index':row['frame_index'],'time':row['time'],'dimensions':row['dimensions'],'primary_ids':row['primary_ids'],'objects':[],'overlap_pairs':row['overlap_pairs']}
 for o in row['objects']:
  v={k:o[k] for k in ['object_id','kind','valid','reason','mask_source','mask_bbox_seed_iou','position','area','occlusion','headroom','look_room','action_crop','motion_front'] if k in o}
  sep=o.get('background_separation',{});v['background_separation']={k:sep[k] for k in ['valid','reason','color_JS_distance','boundary_Lstar'] if k in sep}
  pose=o.get('pose',{});v['pose']=pose
  dep=o.get('depth',{});v['depth']={k:dep[k] for k in ['valid','values','reason'] if k in dep}
  # Per-contour sample coordinates and sensitivity sweeps are engineering diagnostics,
  # not necessary for qualitative VLM decisions; keep pair-level minimum/ratio.
  packed['objects'].append(v)
 packed['overlap_pairs']=[{'objects':v['objects'],'valid':v.get('valid'), 'geometry':{k:{f:x for f,x in g.items() if f in ['min_distance_normalized','near_contour_ratio']} for k,g in v.get('geometry',{}).items()}} for v in row['overlap_pairs']]
 return packed

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run-dir',type=Path,required=True);ap.add_argument('--lean',action='store_true');ap.add_argument('--temporal',action='store_true');ap.add_argument('--ids',default='T01,T02,T03');ap.add_argument('--phase',choices=['identify','measure','judge'],required=True);a=ap.parse_args();d=a.run_dir.resolve();rule=load_rubric(ROOT/'rubrics/composition_rubric.json')
 existing=d/'rubric'/'active-expanded.json'
 if existing.exists():assert json.loads(existing.read_text())==rule,'Rubric changed during trial; start a new run directory'
 save(d/'rubric'/'active-expanded.json',rule);save(d/'rubric'/'active-lock.json',json.loads((ROOT/'rubrics/composition_rubric.lock.json').read_text()))
 if a.phase=='measure':
  env=os.environ.copy();env['GAME_EVAL_RUN_DIR']=str(d)
  subprocess.run([env.get('GAME_EVAL_PYTHON',sys.executable),str(ROOT/'src/cv_measure.py')],env=env,check=True);return
 for sid in a.ids.split(','):
  inp=d/'inputs'/sid;work=d/'model-calls'/sid/a.phase;out=work/'result.json'
  if out.exists():
   if a.phase=='identify' and not (d/'assignments'/(sid+'.json')).exists():raise RuntimeError('Output exists without converted assignment; inspect before resume')
   if a.phase=='judge' and not (work/'validation.json').exists():raise RuntimeError('Unvalidated output exists; inspect before resume')
   print('REUSE',sid,a.phase,flush=True);continue
  images=[inp/'input-1.jpg',inp/'input-2.jpg'];frame_rows=json.loads((inp/'frames.json').read_text());frameids={f"rgb-{x['frame_index']:04d}":x for x in frame_rows}
  if a.phase=='identify':
   prompt='不要使用工具或读取额外文件，仅使用本次附图与文本。你只做画面内容识别与定位，不判美学档位。两张序列图共80帧，4FPS，帧号0..79，时间0..19.75秒。坐标使用原图1280x720。识别主体、陪体、环境前景背景，按实际呈现内容变化划分必要阶段，并记录必要信息和证据帧。主体可以多人、物体或景物，不默认最大最亮为主体；没有完整剧情也可评价。不猜测人物心理。为主要主体及少量重要陪体/环境提供可见范围框，每个对象至少在其存在阶段的起止及变化处给稀疏anchors；不要跨主体切换线性追踪。框只是分割提示，不是像素mask。场景区域kind=scene_region；人物humanoid。疑似界面叠加或异常需保留不确定性。角色可在segments注明变化。仅返回schema JSON。样本编号：'+sid
   r=call(work,prompt,ASSIGN,images,out)
   for k,seg in enumerate(r['segments']):
    seg['reported_range']=list(seg['range']);seg['range']=[seg['range'][0],r['segments'][k+1]['range'][0] if k+1<len(r['segments']) else 20]
   r['range_convention']='Half-open ranges, end at next start, final end=20; reported_range retained.'
   for o in r['objects']:
    o['anchors']={str(v['frame_index']):v['box'] for v in o['anchors']}
    if o['role']=='subject':
     o['active_frame_ranges']=[[min(f['frame_index'] for f in frame_rows if seg['range'][0]<=f['time']<seg['range'][1]),max(f['frame_index'] for f in frame_rows if seg['range'][0]<=f['time']<seg['range'][1])] for seg in r['segments'] if o['id'] in seg['primary']]
   save(d/'assignments'/(sid+'.json'),r)
  else:
   from PIL import Image,ImageDraw
   rows=json.loads((d/sid/'measurements.json').read_text());chosen=[x for x in rows if (d/sid/f"overlay-{x['frame_index']:04d}.jpg").exists()]
   canvas=Image.new('RGB',(1280,384* ((len(chosen)+1)//2)), '#101820');draw=ImageDraw.Draw(canvas)
   for k,row in enumerate(chosen):
    p=d/sid/f"overlay-{row['frame_index']:04d}.jpg";im=Image.open(p);im.thumbnail((640,360));x=(k%2)*640;y=(k//2)*384;canvas.paste(im,(x,y));draw.text((x,y+360),f"measurement {row['frame_index']:04d} {row['time']:.2f}s",fill='white')
   qa=work/'segmentation-contact-sheet.jpg';qa.parent.mkdir(parents=True,exist_ok=True);canvas.save(qa,quality=92);images.append(qa)
   # Only selected overlay frames' measurements are sent; all raw rows remain in the run.
   subset=[x for x in rows if x['frame_index'] in [v['frame_index'] for v in chosen]];mids={f"measure-{x['frame_index']:04d}-{o['object_id']}":(x['frame_index'],o['object_id']) for x in subset for o in x['objects']}
   evidence={'RGB_ids':list(frameids),'measurement_ids':list(mids),'measurement_rows':[lean_row(row) for row in subset] if a.lean else subset,'assignment':json.loads((d/'assignments'/(sid+'.json')).read_text())};save(work/'evidence.json',evidence)
   prompt='不要使用工具或读取额外文件，仅使用本次附图与文本。你是构图VLM评审。仅依据以下冻结Rubric和实际附图、测量。人工答案与历史预测未提供。先核对主体/陪体/环境和关键阶段；第一、二张为80帧RGB序列，第三张为分割覆盖图。原始图1280x720，4FPS，时间0..19.75秒。mask只是估计，必须逐项审查所给覆盖图中每个对象，记入segmentation_review；不可靠mask及其面积、位置、颜色/深度统计不得作为依据。bbox不是mask；无amodal不算遮挡率；单目深度不是米。画面可直接支持质性观察，不编造数值或心理。数值仅为证据，不是美学阈值。每一阶段必须输出完整42个原子检查点，各自一个indicator_id。基础中档是最低功能，高档继承基础且有实质表达，不平均不计数。已确认关键失败判低；缺失不等于失败。未证明增强而基础成立判中。手法未识别不扣档。引用rgb-0000等画面ID或measure-0000-对象ID，只能引用下面清单。简洁、可核查理由，不写隐含思维推演。样本：'+sid+'\nRubric:\n'+json.dumps(rule,ensure_ascii=False)+'\nEvidence:\n'+json.dumps(evidence,ensure_ascii=False)
   schema=json.loads(json.dumps(RESULT))
   if a.temporal:
    schema['properties']['temporal_analysis']=arr(obj(before_stage_id=S,after_stage_id=S,before_evidence_ids=arr(S),after_evidence_ids=arr(S),visible_change=S,spatial_or_attention_effect=S,expressive_effect=S,checkpoint_ids=arr(S),uncertainty=S))
    schema['required'].append('temporal_analysis')
    prompt+='\n时序分析为必填：每个相邻阶段给前后阶段ID、前后实际帧ID、可见安排变化、空间／注意效果及表达效果。若整段无阶段变化，前后可为同一阶段，比较开始／中段／结束并说明维持了什么。不要把A→B的主体切换当作同一主体的位置或面积变化；常规正反打建立空间关系，不自动等于情感增强。无需强行编造变化或情感；缺少时序证据应写不确定性。给出简洁可核查理由。'
   if a.lean:prompt+='\n测量说明：位置/边距均按画宽高归一，可见占比为mask像素/(W×H)，遮挡率无amodal时无效。Lab直方图JS距离为0..1；轮廓L*差为0..100。深度为单目相对逆深度，非米。除已提供覆盖图对应对象外，其他原始测量未作为本次输入。重复模型元数据、九宫格分布和敏感性诊断已省略，不从省略内容作判断。'
   r=call(work,prompt,schema,images,out);report=validate(r,rule,frameids,mids);
   if a.temporal:
    stage_ids={v['stage_id'] for v in r['stages']};assert r['temporal_analysis'],'Missing temporal analysis'
    point_ids={v['checkpoint_id'] for v in r['checks']}
    for t in r['temporal_analysis']:
     assert t['before_stage_id'] in stage_ids and t['after_stage_id'] in stage_ids
     assert t['before_evidence_ids'] and t['after_evidence_ids']
     assert set(t['before_evidence_ids']+t['after_evidence_ids'])<=set(frameids)|set(mids)
     assert set(t['checkpoint_ids'])<=point_ids
    report['temporal_analysis_records']=len(r['temporal_analysis'])
   save(work/'validation.json',report);save(d/sid/'prediction.json',r)
  print('DONE',sid,a.phase,flush=True)
if __name__=='__main__':main()
