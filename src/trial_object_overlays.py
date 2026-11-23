"""Post-hoc object-location SVG overlays. Never masks or new model predictions."""
import html,json
from pathlib import Path

def interpolate(anchors,index):
 values=sorted((int(k),v) for k,v in anchors.items())
 if not values or not values[0][0]<=index<=values[-1][0]:return None
 for (a,x),(b,y) in zip(values,values[1:]):
  if a<=index<=b:return [round(v+(w-v)*(index-a)/(b-a),1) for v,w in zip(x,y)]
 return values[0][1] if len(values)==1 else values[-1][1]

def create_t01_overlays(dest,assignment,frames):
 records={};objects={o['id']:o for o in assignment['objects']}
 for p in sorted((dest/'evidence').glob('rgb-*.jpg')):
  index=int(p.stem.split('-')[1]);f=frames[index]
  stage=next(s for s in assignment['segments'] if s['range'][0]<=f['time']<s['range'][1]);primary=stage['primary'][0]
  specs=[(primary,'主体 A' if primary=='person_a' else '主体 B','#149b87',False,None),('lower_character','陪体候选 · 身份未确认','#d28b16',True,None),('shield','陪体候选 · 盾状物','#d28b16',True,None)]
  # These windows point to visible examples, not the full original broad region boxes.
  specs += [('fence_foliage','背景局部示意 · 栅栏/绿植','#805ad5',True,[960,90,1250,390])] if primary=='person_a' else [('camp_background','背景局部示意 · 营地','#805ad5',True,[28,65,350,380])]
  specs += [('ground','环境 · 下方地面 / 前景归属待确认','#367bc2',True,[840,585,1245,690])]
  entries=[]
  for oid,label,color,dashed,window in specs:
   box=window or interpolate(objects[oid]['anchors'],index)
   if box is None:continue
   entries.append({'object_id':oid,'label':label,'color':color,'dashed':dashed,'box':box,'original_role':objects[oid]['role'],'original_seed_box':interpolate(objects[oid]['anchors'],index),'geometry_source':'posthoc illustrative visible-region window' if window else 'original RGB-only localization seed, interpolated within active stage','is_mask':False})
  record={'frame_index':index,'time':f['time'],'source_time':f['source_time'],'stage_id':stage['id'],'subject_id':primary,'raw_url':f'T01/evidence/{p.name}','annotated_url':f'T01/evidence/objects-{index:04d}.svg','objects':entries};records[str(index)]=record
  svg=['<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 1280 720" width="1280" height="720"><image width="1280" height="720" href="'+p.name+'" xlink:href="'+p.name+'"/>']
  for n in entries:
   x,y,x2,y2=n['box'];color=n['color'];label=html.escape(n['label']);dash='stroke-dasharray="12 8"' if n['dashed'] else ''
   svg.append(f'<rect x="{x}" y="{y}" width="{x2-x}" height="{y2-y}" fill="{color}" fill-opacity="0.035" stroke="{color}" stroke-width="4" {dash}/>')
   label_y=max(28,min(y+30,705));label_width=min(560,max(150,len(n['label'])*23));label_x=max(0,min(x,1280-label_width-4));svg.append(f'<rect x="{label_x}" y="{label_y-27}" width="{label_width}" height="34" rx="4" fill="{color}"/><text x="{label_x+8}" y="{label_y}" font-family="system-ui,sans-serif" font-size="24" fill="white">{label}</text>')
  svg.append('</svg>');(dest/'evidence'/f'objects-{index:04d}.svg').write_text(''.join(svg))
 data={'version':'display-overlay-v1','provenance':'事后展示层：主体／陪体框来自原RGB定位提示；背景及地面仅用另画的可见局部窗口示意。不是像素分割，不修改角色识别原记录，不曾作为本次机标输入。','uncertainty':'下方人物与上方头像的身份对应、陪体角色及地面的前景归属待确认。未强行合并为同一身体。','frames':records}
 (dest/'object-annotations.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');return data
