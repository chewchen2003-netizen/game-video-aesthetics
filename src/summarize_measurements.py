import json,hashlib,statistics,os
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;ROOT=P.parent;D=Path(os.environ.get('GAME_EVAL_RUN_DIR',ROOT/'runs/reproduction')).resolve();CFG=json.loads((D/'config.json').read_text())
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False))
def stats(x):return {'n':len(x),'min':float(np.min(x)),'median':float(np.median(x)),'max':float(np.max(x))} if x else None
def intervals(samples,test):
 runs=[];cur=[]
 for t,v in samples:
  if test(v):
   if cur and t-cur[-1]>.251:runs.append(cur);cur=[]
   cur.append(t)
  elif cur:runs.append(cur);cur=[]
 if cur:runs.append(cur)
 return [{'sample_time_range':[r[0],r[-1]],'sample_count':len(r),'support_seconds':len(r)/4,'interpretation':'4FPS sample-supported duration, not exact continuous event boundaries'} for r in runs]
def main():
 reports=[];font=ImageFont.load_default(size=16)
 import sys
 for bid in ([sys.argv[1]] if len(sys.argv)>1 else CFG['samples']):
  d=D/bid
  if not (d/'measurements.json').exists():continue
  rows=json.loads((d/'measurements.json').read_text());objects={};pairs={};depthorders=[]
  for r in rows:
   for o in r['objects']:objects.setdefault(o['object_id'],[]).append((r['time'],o))
   for pair in r['overlap_pairs']:pairs.setdefault('|'.join(pair['objects']),[]).append({'time':r['time'],**pair})
   valid=[o for o in r['objects'] if o.get('valid') and o['depth']['valid']]
   if len(valid)>1:depthorders.append({'time':r['time'],'source':'monocular_relative_inverse_depth','median_near_to_far':sorted([{'object_id':o['object_id'],'median':o['depth']['values']['median']} for o in valid],key=lambda x:-x['median']),'warning':'same-frame relative relation only; no metric/cross-session depth claim; semantic masks require QA'})
  summary={}
  for oid,values in objects.items():
   good=[(t,o) for t,o in values if o.get('valid')];sep=[o['background_separation'] for t,o in good if o['background_separation'].get('valid')];heads=[{'time':t,**o['headroom']} for t,o in good if o['headroom'].get('valid')];joints=[(t,o['pose']['joints']) for t,o in good if o['pose'].get('valid')];event=[]
   for joint in ['left_elbow','right_elbow','left_wrist','right_wrist','left_knee','right_knee','left_ankle','right_ankle']:
    evidence=[{'time':t,**j[joint]} for t,j in joints if j[joint]['valid'] and j[joint].get('edge_distance_over_subject_height') is not None]
    event.append({'joint':joint,'valid_points':len(evidence),'distance_over_subject_height':stats([x['edge_distance_over_subject_height'] for x in evidence]),'nearest_observations':sorted(evidence,key=lambda x:x['edge_distance_over_subject_height'])[:3],'cut_status':'unknown; nearness alone does not establish limb truncation'})
   summary[oid]={'sample_count_with_seed':len(values),'valid_mask_samples':len(good),'mask_coverage_over_all_80_samples':len(good)/80,'area_ratio':stats([o['area']['visible_ratio'] for t,o in good]),'bbox_center_x':stats([o['position']['center'][0] for t,o in good]),'bbox_center_y':stats([o['position']['center'][1] for t,o in good]),'edge_candidates_sensitivity':{str(th):intervals([(t,min(o['position']['edge_distances'].values())) for t,o in good],lambda x:x<th) for th in [.01,.02,.04]},'color_JS_distance':stats([s['color_JS_distance'] for s in sep]),'boundary_Lstar_median':stats([s['boundary_Lstar']['median'] for s in sep if s['boundary_Lstar']['median'] is not None]),'low_color_candidates':intervals([(t,o['background_separation'].get('color_JS_distance')) for t,o in good if o['background_separation'].get('valid')],lambda x:x<.1),'occlusion_ratio':None,'occlusion_reason':'Reliable complete/amodal masks unavailable; not replaced with bbox/visible-mask IoU.','headroom_sparse':heads,'joint_distance_summary':event,'gaze_room':None,'gaze_reason':'No reliable eye/head direction supplied.','confirmed_motion_front_distance':stats([o['motion_front']['front_distance']['over_diagonal'] for t,o in good if o['motion_front'].get('actual_direction_valid') and o['motion_front'].get('front_distance')]),'motion_reason':'Screen-only displacement saved separately; not promoted without camera/action direction evidence.','confirmed_action_crop_events':[],'action_reason':'No border-crossing event confirmed by pose disappearance alone.','depth_sample_count':sum(o['depth']['valid'] for t,o in good),'depth_units':'monocular relative inverse model output; not meters','grid_mean_object_allocation':np.mean([o['grid']['allocation_per_cell'] for t,o in good],axis=0).tolist() if good else None,'coverage_warning':'Coverage restricted to preselected subject intervals, no inference outside seed intervals. All segmentations still need semantic QA.'}
  report={'blind_id':bid,'sample_count':len(rows),'source_definitions_sha256':hashlib.sha256((ROOT/'data/standards/composition-frozen-contracts.json').read_bytes()).hexdigest(),'objects':summary,'depth_orders':depthorders,'overlap_pairs':pairs,'score':None,'threshold_version':None,'grade_rule':'No averages or weights; structured evidence feeds assistant evaluation after QA.'};save(d/'summary.json',report);reports.append(report)
  pics=sorted(d.glob('overlay-*.jpg'));canvas=Image.new('RGB',(1280,4*208),'#151515');draw=ImageDraw.Draw(canvas)
  # Up to 16 evenly spaced QA overlays, not just aesthetically favorable frames.
  inds=np.linspace(0,len(pics)-1,min(16,len(pics)),dtype=int) if pics else []
  for k,ix in enumerate(inds):
   pic=pics[ix];im=Image.open(pic);im.thumbnail((320,180));x=k%4*320;y=k//4*208;canvas.paste(im,(x,y));idx=int(pic.stem.split('-')[-1]);draw.text((x+4,y+182),f'{bid} #{idx} {idx/4:.2f}s',font=font,fill='white')
  canvas.save(d/'measurement-qa.jpg')
 print('Summarized',len(reports),'samples')
if __name__=='__main__':main()
