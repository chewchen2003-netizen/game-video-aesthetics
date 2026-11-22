"""Additional input-gated formulas; no semantic or aesthetic defaults."""
import numpy as np

def occlusion(visible,full=None):
 if full is None:return {'valid':False,'ratio':None,'reason':'no reliable complete/amodal mask'}
 if visible.shape!=full.shape:return {'valid':False,'ratio':None,'reason':'shape mismatch'}
 full=full.astype(bool);visible=visible.astype(bool);den=int(full.sum())
 if den==0:return {'valid':False,'ratio':None,'reason':'empty complete mask'}
 if np.any(visible&~full):return {'valid':False,'ratio':None,'reason':'visible pixels outside complete mask; inputs inconsistent'}
 return {'valid':True,'ratio':float(np.sum(full&~visible)/den),'complete_in_frame_pixels':den,'hidden_in_frame_pixels':int(np.sum(full&~visible))}

def look_room(face_box,direction,W,source=None):
 if face_box is None or direction not in ['left','right']:return {'valid':False,'front':None,'back':None,'ratio':None,'reason':'no reliable horizontal head/gaze direction and face box; camera direction not substituted'}
 l,_,r,_=face_box;f=(W-r)/W if direction=='right' else l/W;b=l/W if direction=='right' else (W-r)/W;den=f+b
 if f<0 or b<0 or den<=0:return {'valid':False,'front':None,'back':None,'ratio':None,'reason':'invalid face bounds or denominator'}
 return {'valid':True,'front':f,'back':b,'ratio':f/den,'direction':direction,'source':source,'note':'No requirement that ratio exceed 0.5.'}

def action_candidates(rows,object_id,W=1280,H=720,edge_fraction=.02):
 """Compute near-edge part tracks and return candidates, never infer exit from disappearance alone."""
 tracks={};diag=float(np.hypot(W,H))
 for row in rows:
  obj=next((o for o in row['objects'] if o['object_id']==object_id and o.get('valid')),None)
  if not obj:continue
  for name,j in (obj.get('pose',{}).get('joints') or {}).items():
   if name not in ['left_wrist','right_wrist','left_ankle','right_ankle'] or not j.get('valid'):continue
   x,y=j['xy'];distances=[x,W-x,y,H-y];near=int(np.argmin(distances));tracks.setdefault(name,[]).append({'time':row['time'],'frame_index':row['frame_index'],'xy':[x,y],'nearest_boundary':['left','right','top','bottom'][near],'distance_pixels':float(min(distances)),'distance_over_diagonal':float(min(distances)/diag)})
 candidates=[]
 for part,track in tracks.items():
  for i,e in enumerate(track):
   if e['distance_over_diagonal']>=edge_fraction:continue
   after=track[i+1] if i+1<len(track) else None;before=track[i-1] if i else None
   candidates.append({'part':part,'frame_index':e['frame_index'],'time':e['time'],'boundary':e['nearest_boundary'],'distance_pixels':e['distance_pixels'],'distance_over_diagonal':e['distance_over_diagonal'],'previous':before,'next':after,'visibility_gap_after':float(after['time']-e['time']) if after else None,'confirmation':'unknown','reason':'Near-edge/gap candidate only; RGB part trajectory and exit/re-entry evidence still required.'})
 return {'part_track_samples':sum(len(t) for t in tracks.values()),'tracks':tracks,'candidates':candidates,'confirmed_events':[],'candidate_threshold':edge_fraction,'threshold_status':'engineering screening only, not aesthetic boundary'}
