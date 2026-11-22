"""Extract actual 4 FPS frames and preserve clip-relative and source timecodes."""
from pathlib import Path
import json,subprocess
from PIL import Image,ImageDraw,ImageFont

def extract(video,run,bid,source_start=0):
 d=Path(run)/'inputs'/bid;fr=d/'frames';fr.mkdir(parents=True,exist_ok=True)
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(video),'-an','-vf','fps=4:start_time=0','-frames:v','80','-q:v','2',str(fr/'frame-%04d.jpg')],check=True)
 files=sorted(fr.glob('frame-*.jpg'))
 if len(files)!=80:raise ValueError(f'{bid}: need a 20s clip producing 80 frames, got {len(files)}')
 entries=[{'frame_index':i,'time':i/4,'source_time':source_start+i/4,'image':str(f.relative_to(Path(run)/'inputs'))} for i,f in enumerate(files)]
 (d/'frames.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2));font=ImageFont.load_default(size=15)
 for page in range(2):
  canvas=Image.new('RGB',(1280,1040),'#111');dr=ImageDraw.Draw(canvas)
  for k,e in enumerate(entries[page*40:(page+1)*40]):
   im=Image.open(Path(run)/'inputs'/e['image']);im.thumbnail((160,90));x=k%8*160;y=k//8*116;canvas.paste(im,(x,y));dr.text((x+2,y+92),f"#{e['frame_index']} {e['time']:05.2f}s",font=font,fill='white')
  ix=page*40+20;im=Image.open(files[ix]);im.thumbnail((768,432));canvas.paste(im,(256,600));dr.text((3,582),f'{bid} REFERENCE #{ix} {ix/4:.2f}s',font=font,fill='white');canvas.save(d/f'input-{page+1}.jpg',quality=94)
 canvas=Image.new('RGB',(1280,1152),'#111');dr=ImageDraw.Draw(canvas)
 for k,ix in enumerate([0,16,32,48,64,79]):
  im=Image.open(files[ix]);im.thumbnail((640,360));x=k%2*640;y=k//2*384;canvas.paste(im,(x,y));dr.text((x+4,y+362),f'{bid} #{ix} {ix/4:.2f}s',font=font,fill='white')
 canvas.save(d/'overview.jpg',quality=95)
 return entries
