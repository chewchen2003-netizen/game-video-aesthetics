"""2 FPS base samples with bounded, explicitly logged 4 FPS local supplementation."""
from pathlib import Path
import json,shutil,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont

def render(run,sid,rows):
 d=run/'inputs'/sid;rows=sorted(rows,key=lambda x:x['time']);(d/'frames.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
 n=len(rows);cols=8;tilew=160;tileh=116;gridheight=math.ceil(n/cols)*tileh
 canvas=Image.new('RGB',(1280,gridheight+400),'#111');draw=ImageDraw.Draw(canvas);font=ImageFont.load_default(size=15)
 for k,e in enumerate(rows):
  im=Image.open(run/'inputs'/e['image']);im.thumbnail((160,90));x=k%cols*160;y=k//cols*tileh;canvas.paste(im,(x,y));draw.text((x+2,y+92),f"#{e['frame_index']} {e['time']:.2f}s",fill='white',font=font)
 for k,t in enumerate([5,15]):
  e=min(rows,key=lambda x:abs(x['time']-t));im=Image.open(run/'inputs'/e['image']);im.thumbnail((640,360));canvas.paste(im,(k*640,gridheight+25));draw.text((k*640+4,gridheight+385),f"REFERENCE #{e['frame_index']} {e['time']:.2f}s",fill='white',font=font)
 canvas.save(d/'input-sequence.jpg',quality=94)
 (d/'input-manifest.json').write_text(json.dumps({'images':['input-sequence.jpg'],'base_fps':2,'supplemental_fps':4,'frame_index_convention':'original 4FPS grid index; sparse, use explicit timestamps','actual_frame_count':n},indent=2))

def prepare(source,run,sid,computer_budget=8):
 dest=run/'inputs'/sid;(dest/'frames').mkdir(parents=True,exist_ok=True);original=json.loads((source/'frames.json').read_text());assert len(original)==80
 base=[e for e in original if e['frame_index']%2==0];scores=[]
 def small(e):return np.asarray(Image.open(source.parent/e['image']).convert('RGB').resize((64,36)),dtype=float)
 for a,b in zip(base,base[1:]):
  score=float(np.mean(np.abs(small(a)-small(b)))/255)
  if score>=.12:scores.append((score,a['frame_index']+1))
 selected={e['frame_index'] for e in base};extras=[i for _,i in sorted(scores,reverse=True)[:computer_budget]];selected.update(extras)
 rows=[]
 for e in original:
  if e['frame_index'] not in selected:continue
  x=dict(e);x['sampling_reason']='base_2fps' if x['frame_index']%2==0 else 'rapid_change_candidate_4fps';x['adaptive']=x['frame_index']%2==1
  shutil.copyfile(source.parent/e['image'],run/'inputs'/e['image']);rows.append(x)
 render(run,sid,rows)
 (dest/'sampling-plan.json').write_text(json.dumps({'base_fps':2,'base_count':40,'computer_extra_indices':extras,'computer_extra_budget':computer_budget,'change_threshold':.12,'threshold_status':'engineering trigger only, not an aesthetic grade threshold','model_extra_budget':8,'source_cache':str(source),'candidate_count':len(scores),'not_all_candidate_changes_are_exhaustively_sampled':len(scores)>computer_budget},ensure_ascii=False,indent=2))
 return rows

def supplement(source,run,sid,requests,budget=8):
 dest=run/'inputs'/sid;rows=json.loads((dest/'frames.json').read_text());have={e['frame_index'] for e in rows};original=json.loads((source/'frames.json').read_text());added=[]
 for req in requests:
  lo,hi=req['time_range'];assert 0<=lo<=hi<=20
  for e in original:
   if len(added)>=budget:break
   if e['frame_index'] not in have and lo<=e['time']<=hi:
    x=dict(e);x.update(sampling_reason='model_requested_4fps',adaptive=True);shutil.copyfile(source.parent/e['image'],run/'inputs'/e['image']);rows.append(x);have.add(e['frame_index']);added.append(e['frame_index'])
 render(run,sid,rows);plan=json.loads((dest/'sampling-plan.json').read_text());plan.update(model_requests=requests,model_extra_indices=added,actual_count=len(rows),model_supplement_limit_reached=len(added)>=budget);(dest/'sampling-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2))
 return rows
