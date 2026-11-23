"""Execute the user's composition measurement definitions on isolated RGB inputs.
CV models only; assistant supplies subject/region identities and sparse localization hints.
No human grades, notes, former predictions, cloud inference or VLM calls.
"""
from pathlib import Path
import json,time,hashlib,sys,os
os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY','1');os.environ.setdefault('DO_NOT_TRACK','1')
import numpy as np,cv2,torch
from PIL import Image
from scipy.spatial.distance import jensenshannon
from ultralytics import YOLO,SAM
from transformers import AutoImageProcessor,AutoModelForDepthEstimation
P=Path(__file__).resolve().parent;ROOT=P.parent;D=Path(os.environ.get('GAME_EVAL_RUN_DIR',ROOT/'runs/reproduction')).resolve();IN=D/'inputs';CFG=json.loads((D/'config.json' if (D/'config.json').exists() else ROOT/'data/measurement-config.json').read_text());SEEDS={};HEAD={};DIRECTIONS={};DEVICE='cuda' if torch.cuda.is_available() else ('mps' if torch.backends.mps.is_available() else 'cpu')
NAMES=['nose','left_eye','right_eye','left_ear','right_ear','left_shoulder','right_shoulder','left_elbow','right_elbow','left_wrist','right_wrist','left_hip','right_hip','left_knee','right_knee','left_ankle','right_ankle']
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False,default=lambda v:v.item() if isinstance(v,np.generic) else v.tolist() if isinstance(v,np.ndarray) else str(v)))
def event(stage,**kw):
 with (D/'timing.jsonl').open('a') as f:f.write(json.dumps({'stage':stage,'epoch_seconds':time.time(),'monotonic':time.monotonic(),**kw})+'\n')
def bbox(mask):
 y,x=np.where(mask);return [int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)] if len(x) else None
def iou(a,b):
 x=max(a[0],b[0]);y=max(a[1],b[1]);xx=min(a[2],b[2]);yy=min(a[3],b[3]);inter=max(0,xx-x)*max(0,yy-y);return inter/max(1,(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-inter)
def hint(o,idx):
 if o.get('active_frame_ranges') and not any(lo<=idx<=hi for lo,hi in o['active_frame_ranges']):return None
 a=sorted((int(k),np.array(v,dtype=float)) for k,v in o['anchors'].items())
 if not a[0][0]<=idx<=a[-1][0]:return None
 if len(a)==1:return a[0][1].tolist()
 for (k,v),(kk,vv) in zip(a,a[1:]):
  if k<=idx<=kk:return (v+(vv-v)*(idx-k)/max(1,kk-k)).tolist()
def pos(b,W,H):return {'bbox_xyxy':b,'bbox_kind':'visible_mask_bbox','center':[float((b[0]+b[2])/(2*W)),float((b[1]+b[3])/(2*H))],'edge_distances':{'left':b[0]/W,'right':(W-b[2])/W,'top':b[1]/H,'bottom':(H-b[3])/H},'crop_status':'unknown; touching border alone is not proof of cropping'}
def grid(m):
 H,W=m.shape;yc,xc=np.where(m);cy=float(yc.mean()/H);cx=float(xc.mean()/W);edgesx=np.linspace(0,W,4,dtype=int);edgesy=np.linspace(0,H,4,dtype=int);a=[];b=[];total=int(m.sum())
 for i in range(3):
  aa=[];bb=[]
  for j in range(3):
   q=m[edgesy[i]:edgesy[i+1],edgesx[j]:edgesx[j+1]];aa.append(float(q.mean()));bb.append(float(q.sum()/total))
  a.append(aa);b.append(bb)
 return {'coverage_per_cell':a,'allocation_per_cell':b,'horizontal_allocation':np.sum(b,axis=0).tolist(),'vertical_allocation':np.sum(b,axis=1).tolist(),'center_kind':'visible_mask_centroid','center':[cx,cy],'cell_row_col':[min(2,int(cy*3)),min(2,int(cx*3))],'distance_to_vertical_thirds':min(abs(cx-1/3),abs(cx-2/3)),'distance_to_horizontal_thirds':min(abs(cy-1/3),abs(cy-2/3)),'distance_to_nearest_thirds_intersection':min(float(np.hypot(cx-x,cy-y)) for x in [1/3,2/3] for y in [1/3,2/3])}
def contour(m):
 cs,_=cv2.findContours(m.astype('uint8'),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE);return max(cs,key=cv2.contourArea).reshape(-1,2) if cs else np.empty((0,2),int)
def separation(rgb,m,others,b):
 H,W=m.shape;ring=max(2,round((b[3]-b[1])*CFG['parameters']['mask_background_ring_fraction_of_bbox_height']));kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(ring*2+1,ring*2+1));bg=cv2.dilate(m.astype('uint8'),kernel).astype(bool)&~m&~others
 if bg.sum()<30:return {'valid':False,'reason':'insufficient local background pixels','color_JS_distance':None,'boundary_Lstar':None}
 lab=cv2.cvtColor(rgb.astype('float32')/255,cv2.COLOR_RGB2LAB);bins=CFG['parameters']['lab_histogram_bins'];ranges=[[0,100],[-128,128],[-128,128]];a=np.histogramdd(lab[m],bins=bins,range=ranges)[0].ravel();bq=np.histogramdd(lab[bg],bins=bins,range=ranges)[0].ravel();js=float(jensenshannon(a/a.sum(),bq/bq.sum(),base=2));cs=contour(m);samples=[];r=CFG['parameters']['contour_neighborhood_pixels']
 for x,y in cs[::max(1,len(cs)//256)]:
  # Exclude image-boundary contours: their outside neighborhood is not observed.
  if x<r or y<r or x>=W-r or y>=H-r:continue
  sl=np.s_[y-r:y+r+1,x-r:x+r+1];v=lab[:,:,0][sl];inside=m[sl];outside=bg[sl]
  if inside.sum()>=3 and outside.sum()>=3:samples.append(float(abs(np.median(v[inside])-np.median(v[outside]))))
 return {'valid':True,'color_space':'OpenCV float Lab D65','histogram_bins':bins,'ring_radius_pixels':ring,'background_pixels':int(bg.sum()),'color_JS_distance':js,'JS_log_base':2,'boundary_Lstar':{'median':float(np.median(samples)) if samples else None,'q10':float(np.quantile(samples,.1)) if samples else None,'q90':float(np.quantile(samples,.9)) if samples else None,'sample_count':len(samples),'unit':'L* 0..100'},'low_color_candidate':js<CFG['parameters']['low_color_JS_distance_candidate'],'low_luminance_candidate':bool(samples and np.median(samples)<CFG['parameters']['low_contour_Lstar_candidate'])}
def overlapping(ma,mb):
 H,W=ma.shape;ca=contour(ma);cb=contour(mb);diag=float(np.hypot(W,H));out={};
 if not len(ca) or not len(cb):return {'valid':False}
 # Distances are computed on contour pixels, not on foreground areas or mask IoU.
 for name,c,target in [('a_to_b',ca,cb),('b_to_a',cb,ca)]:
  canvas=np.ones((H,W),np.uint8);canvas[target[:,1],target[:,0]]=0;dt=cv2.distanceTransform(canvas,cv2.DIST_L2,cv2.DIST_MASK_PRECISE);dist=dt[c[:,1],c[:,0]];out[name]={'min_distance_normalized':float(dist.min()/diag),'near_contour_ratio':float(np.mean(dist<CFG['parameters']['contour_proximity_fraction_of_diagonal']*diag)),'near_ratio_sensitivity':{str(e):float(np.mean(dist<e*diag)) for e in [.0025,.005,.01]},'near_locations_xy':c[dist<CFG['parameters']['contour_proximity_fraction_of_diagonal']*diag][::max(1,int(np.sum(dist<CFG['parameters']['contour_proximity_fraction_of_diagonal']*diag))//10)].tolist()}
 return {'valid':True,'normalization':'frame diagonal','epsilon':CFG['parameters']['contour_proximity_fraction_of_diagonal'],'geometry':out,'interpretation':'candidate geometric contact only; not occlusion ratio or automatic shape-misreading verdict'}
def pose_measure(result,seed,S,W,H):
 if result.keypoints is None or not len(result.boxes):return {'valid':False,'reason':'pose detector returned no person','joints':None}
 boxes=result.boxes.xyxy.cpu().numpy();best=max(range(len(boxes)),key=lambda i:iou(boxes[i],seed));match=iou(boxes[best],seed)
 if match<.1:return {'valid':False,'reason':'no pose associated with selected subject','association_iou':match,'joints':None}
 xy=result.keypoints.xy[best].cpu().numpy();conf=result.keypoints.conf[best].cpu().numpy();j={}
 for name,(x,y),c in zip(NAMES,xy,conf):
  valid=bool(c>=CFG['parameters']['pose_confidence'] and 0<x<W and 0<y<H and S>0);j[name]={'valid':valid,'confidence':float(c),'xy':[float(x),float(y)] if valid else None,'edge_distance_over_subject_height':float(min(x,W-x,y,H-y)/S) if valid else None}
 return {'valid':True,'association_iou':float(match),'source':'YOLO11n-pose COCO17','scale_S':'visible mask bbox height; may be unstable when cropped/occluded','joints':j,'neck':{'valid':False,'xy':None,'reason':'COCO17 has no neck; shoulder midpoint is not a neck keypoint. No validated head/neck estimator.'}}
def forward_from_screen(prev,b,t,W,H):
 if prev is None:return {'valid':False,'reason':'no previous valid same-subject box'}
 pb,pt=prev;dt=t-pt
 if dt<=0 or dt>1.2/CFG.get('measurement_fps',4):return {'valid':False,'reason':'trajectory gap'}
 c=np.array([(b[0]+b[2])/2,(b[1]+b[3])/2]);pc=np.array([(pb[0]+pb[2])/2,(pb[1]+pb[3])/2]);v=(c-pc)/dt;speed=float(np.linalg.norm(v));r={'screen_velocity_px_s':v.tolist(),'screen_speed_px_s':speed,'actual_direction_valid':False,'front_distance':None,'reason':'screen displacement alone is not confirmed motion direction; camera compensation unavailable'}
 if speed<CFG['parameters']['screen_velocity_floor_pixels_per_second']:r['reason']='low screen displacement; does not imply no action or no world movement';return r
 u=v/speed;half=np.array([(b[2]-b[0])/2,(b[3]-b[1])/2]);support=c+np.sign(u)*half;ds=[]
 for k,extent in enumerate([W,H]):
  if abs(u[k])>1e-6:ds.append(((extent if u[k]>0 else 0)-support[k])/u[k])
 d=min(x for x in ds if x>=0) if any(x>=0 for x in ds) else 0;r['screen_only_candidate']={'direction':u.tolist(),'distance_over_diagonal':float(d/np.hypot(W,H)),'valid_for_aesthetic_scoring':False};return r

def run():
 event('start');print('DEVICE',DEVICE,flush=True);models=Path(os.environ.get('GAME_EVAL_MODELS_DIR',D/'models'));models.mkdir(exist_ok=True);os.chdir(models);sam=SAM('mobile_sam.pt');pose=YOLO('yolo11n-pose.pt');personseg=YOLO('yolo11n-seg.pt');processor=AutoImageProcessor.from_pretrained('depth-anything/Depth-Anything-V2-Small-hf');depthmodel=AutoModelForDepthEstimation.from_pretrained('depth-anything/Depth-Anything-V2-Small-hf').to(DEVICE).eval();save(D/'runtime.json',{'device':DEVICE,'torch':torch.__version__,'config':CFG,'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'model_files':{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in models.glob('*.pt')},'depth_config':depthmodel.config.to_dict()});event('models_loaded')
 for bid in os.environ.get('GAME_EVAL_SAMPLE_IDS',','.join(CFG['samples'])).split(','):
  assignment=D/'assignments'/(bid+'.json')
  if not assignment.exists():raise FileNotFoundError('Missing RGB subject assignment: '+str(assignment))
  ass=json.loads(assignment.read_text());SEEDS[bid]=ass;HEAD[bid]=ass.get('head_hints',{});DIRECTIONS[bid]=ass.get('direction_evidence',[]);save(D/bid/'assignment-used.json',ass)
  out=D/bid;out.mkdir(exist_ok=True);frames=json.loads((IN/bid/'frames.json').read_text());rows=[];previous={};event('sample_start',blind_id=bid)
  for entry in frames:
   idx=entry['frame_index'];dest=out/'frames'/f'{idx:04d}.json'
   if dest.exists():
    row=json.loads(dest.read_text());rows.append(row)
    for o in row['objects']:
     if o.get('valid'):previous[o['object_id']]=(o['position']['bbox_xyxy'],row['time'])
    continue
   rgb=np.array(Image.open(IN/entry['image']).convert('RGB'));H,W=rgb.shape[:2];objects=[];boxes=[]
   for o in SEEDS[bid]['objects']:
    b=hint(o,idx)
    if b is not None:objects.append(o);boxes.append([max(0,b[0]),max(0,b[1]),min(W-1,b[2]),min(H-1,b[3])])
   masks=[]
   if boxes:
    sr=sam.predict(source=rgb[:,:,::-1].copy(),bboxes=boxes,device=DEVICE,verbose=False)[0]
    for m in sr.masks.data.cpu().numpy() if sr.masks is not None else []:masks.append(cv2.resize(m,(W,H),interpolation=cv2.INTER_NEAREST)>0.5)
   pr=pose.predict(source=rgb[:,:,::-1].copy(),device=DEVICE,verbose=False,conf=.15,imgsz=640)[0] if any(o['kind']=='humanoid' for o in objects) else None
   personseg_used=set()
   if any(o['kind'] in ['humanoid','vehicle'] or o.get('class_hint') for o in objects):
    ps=personseg.predict(source=rgb[:,:,::-1].copy(),device=DEVICE,verbose=False,conf=.15,imgsz=640)[0]
    if ps.masks is not None:
     pboxes=ps.boxes.xyxy.cpu().numpy();pmasks=ps.masks.data.cpu().numpy()
     detection_used=set();pclasses=ps.boxes.cls.cpu().numpy().astype(int)
     for k,o in enumerate(objects):
      if k>=len(masks):continue
      wanted={0} if o['kind']=='humanoid' else ({i for i,n in personseg.names.items() if n==o.get('class_hint')} if o.get('class_hint') else ({1,2,3,5,7} if o['kind']=='vehicle' else set()))
      matches=[(iou(bb,boxes[k]),j) for j,bb in enumerate(pboxes) if pclasses[j] in wanted and j not in detection_used]
      if matches and max(matches)[0]>.1:
       _,j=max(matches);detection_used.add(j);masks[k]=cv2.resize(pmasks[j],(W,H),interpolation=cv2.INTER_NEAREST)>.5;personseg_used.add(k)

   depth=None
   if idx%4==0:
    ins=processor(images=rgb,return_tensors='pt').to(DEVICE)
    with torch.inference_mode():pred=depthmodel(**ins).predicted_depth;dep=torch.nn.functional.interpolate(pred.unsqueeze(1),size=(H,W),mode='bicubic',align_corners=False).squeeze().cpu().numpy()
    if np.isfinite(dep).all():depth=dep;np.savez_compressed(out/f'depth-{idx:04d}.npz',relative_inverse_depth=dep.astype('float16'))
   records=[];overlay=rgb.copy()
   for k,o in enumerate(objects):
    m=masks[k] if k<len(masks) else None;b=bbox(m) if m is not None else None;valid=b is not None and m.sum()>20 and m.mean()<.85 and (o['kind']=='scene_region' or iou(b,boxes[k])>.15)
    rec={'object_id':o['id'],'kind':o['kind'],'localization_seed':boxes[k],'localization_source':'assistant-selected RGB seed boxes; linear interpolation between anchors','valid':bool(valid),'mask_source':'YOLO11n-seg class-associated instance mask' if k in personseg_used else 'MobileSAM visible mask estimate','semantic_validity':'requires visual QA; model mask is not ground truth','mask_bbox_seed_iou':float(iou(b,boxes[k])) if b else None}
    if not valid:rec['reason']='missing, empty or implausibly whole-frame segmentation';records.append(rec);continue
    maskfile=out/'masks'/f'{idx:04d}-{o["id"]}.png';maskfile.parent.mkdir(exist_ok=True);cv2.imwrite(str(maskfile),m.astype('uint8')*255);others=np.zeros_like(m)
    for kk,mm in enumerate(masks):
     if kk!=k:others|=mm
    rec.update(mask_file=str(maskfile.relative_to(D)),position=pos(b,W,H),area={'visible_pixel_count':int(m.sum()),'visible_ratio':float(m.mean()),'bbox_width_px':b[2]-b[0],'bbox_height_px':b[3]-b[1],'amodal_ratio':None},occlusion={'valid':False,'ratio':None,'reason':'no reliable complete/amodal object mask; visible mask or bbox cannot substitute'},background_separation=separation(rgb,m,others,b),grid=grid(m),motion_front=forward_from_screen(previous.get(o['id']),b,entry['time'],W,H));previous[o['id']]=(b,entry['time'])
    rec['pose']=pose_measure(pr,boxes[k],b[3]-b[1],W,H) if o['kind']=='humanoid' and pr is not None else {'valid':False,'reason':'not a humanoid selected subject','joints':None}
    head=HEAD.get(bid,{}).get(str(idx),{}).get(o['id']);rec['headroom']={'valid':False,'gap_pixels':None,'reason':'no reliable head-top/head-height at this time; person bbox top is not head top'}
    if head:
     hb=head['box'];hh=hb[3]-hb[1];rec['headroom']={'valid':True,'source':'assistant sparse head localization estimate; requires QA','head_box':hb,'gap_pixels':hb[1],'gap_over_frame_height':hb[1]/H,'gap_over_head_height':hb[1]/hh,'head_top_status':'inside_frame','orientation':head.get('orientation'),'geometric_measurement_not_comfort_score':True}
    cue=next((c for c in DIRECTIONS.get(bid,[]) if c['object_id']==o['id'] and c['time_range'][0]<=entry['time']<=c['time_range'][1]),None)
    if cue:
     u=np.array(cue['direction'],float);u/=np.linalg.norm(u);c=np.array([(b[0]+b[2])/2,(b[1]+b[3])/2]);support=c+np.sign(u)*np.array([(b[2]-b[0])/2,(b[3]-b[1])/2]);ds=[((extent if u[k]>0 else 0)-support[k])/u[k] for k,extent in enumerate([W,H]) if abs(u[k])>1e-6];distance=min(x for x in ds if x>=0);rec['motion_front'].update(actual_direction_valid=True,direction_source=cue,front_distance={'pixels':float(distance),'over_diagonal':float(distance/np.hypot(W,H)),'direction':u.tolist(),'source':'coarse visible-action projection proxy'},reason=None)
    rec['look_room']={'valid':False,'front':None,'back':None,'ratio':None,'reason':'no reliable projected gaze/head direction; camera direction not substituted'}
    rec['action_crop']={'status':'unknown' if o['kind']=='humanoid' else 'not_applicable','events':[],'reason':'needs confirmed active-part trajectory and evidence of border crossing; pose disappearance alone not used'}
    rec['depth']={'valid':depth is not None,'source':'Depth-Anything-V2-Small monocular relative inverse depth' if depth is not None else None,'units':'relative model units; larger generally nearer; not meters','coverage':1.0 if depth is not None else 0.0,'values':{'median':float(np.median(depth[m])),'q10':float(np.quantile(depth[m],.1)),'q90':float(np.quantile(depth[m],.9))} if depth is not None else None,'reason':None if depth is not None else 'not a depth sample; depth inference only 1FPS, no interpolated values'}
    records.append(rec);color=np.array([(60+83*k)%255,(200+47*k)%255,(120+97*k)%255]);overlay[m]=(overlay[m]*.6+color*.4).astype('uint8');cv2.rectangle(overlay,(b[0],b[1]),(b[2],b[3]),(255,130,0),2);cv2.putText(overlay,o['id'],(b[0],max(15,b[1]-6)),cv2.FONT_HERSHEY_SIMPLEX,.6,(255,130,0),2)
    if rec['pose'].get('joints'):
     for j in rec['pose']['joints'].values():
      if j['valid']:cv2.circle(overlay,tuple(round(v) for v in j['xy']),3,(255,0,255),-1)
   pairs=[]
   for k in range(len(records)):
    for j in range(k+1,len(records)):
     if records[k].get('valid') and records[j].get('valid'):pairs.append({'objects':[objects[k]['id'],objects[j]['id']],**overlapping(masks[k],masks[j])})
   row={'blind_id':bid,'frame_index':idx,'time':entry['time'],'dimensions':[W,H],'objects':records,'overlap_pairs':pairs,'primary_ids':next((s['primary'] for s in SEEDS[bid]['segments'] if s['range'][0]<=entry['time']<=s['range'][1]),[])};save(dest,row);rows.append(row)
   if idx%4==0 or entry.get('adaptive') or idx==frames[-1]['frame_index'] or (not CFG.get('adaptive_sampling') and idx in [20,44,52,60,68,73,76,79]):cv2.imwrite(str(out/f'overlay-{idx:04d}.jpg'),cv2.cvtColor(overlay,cv2.COLOR_RGB2BGR))
   if idx%8==0:print(bid,idx,'objects',len(records),'valid',sum(r['valid'] for r in records),'sampled_count',len(rows),'total',len(frames),flush=True)
  save(out/'measurements.json',rows);event('sample_end',blind_id=bid);print('DONE',bid,flush=True)
 event('end');print('ALL MEASUREMENTS COMPLETE',flush=True)
if __name__=='__main__':run()
