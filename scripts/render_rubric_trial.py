"""Publish only the isolated trial's evidence and frozen predictions, never human answers."""
import argparse,json,shutil,subprocess,html
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def e(x):return html.escape(str(x))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run-dir',type=Path,required=True);a=ap.parse_args();d=a.run_dir.resolve();out=ROOT/'docs/results/rubric-trial3';out.mkdir(parents=True,exist_ok=True)
 sel=json.loads((d/'selection.json').read_text());parts=[];summary=[]
 for source in sel:
  sid=source['trial_id'];dest=out/sid;dest.mkdir(exist_ok=True);r=json.loads((d/sid/'prediction.json').read_text());grade=r['overall']['grade'];summary.append({'id':sid,'original_sample':source['original_sample_number'],'grade':grade,'status':r['overall']['status'],'reason':r['overall']['reason']})
  for file in ['prediction.json','measurements.json','assignment-used.json']:shutil.copyfile(d/sid/file,dest/file)
  shutil.copyfile(d/'inputs'/sid/'frames.json',dest/'frames.json')
  for name in ['input-1.jpg','input-2.jpg','overview.jpg']:shutil.copyfile(d/'inputs'/sid/name,dest/name)
  for p in (d/sid).glob('overlay-*.jpg'):shutil.copyfile(p,dest/p.name)
  if (d/sid/'masks').exists():shutil.copytree(d/sid/'masks',dest/'masks',dirs_exist_ok=True)
  original=Path('/Users/minimax/game-video-review')/source['url']
  if original.exists():shutil.copyfile(original,dest/'original.mp4')
  if not (dest/'original.mp4').exists():raise FileNotFoundError('Provide original source clip before rendering')
  video=dest/'video.mp4'
  if not video.exists():subprocess.run(['ffmpeg','-v','error','-i',str(dest/'original.mp4'),'-vf','scale=960:-2','-c:v','libx264','-crf','27','-preset','fast','-an','-movflags','+faststart',str(video)],check=True)
  for phase in ['identify','judge']:
   call=d/'model-calls'/sid/phase;target=dest/'calls'/phase;target.mkdir(parents=True,exist_ok=True)
   for name in ['prompt.txt','schema.json','result.json']:
    shutil.copyfile(call/name,target/name)
   manifest=json.loads((call/'input-images.json').read_text())
   for item in manifest:item['path']=Path(item['path']).name
   (target/'input-images.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
   if phase=='judge':
    shutil.copyfile(call/'segmentation-contact-sheet.jpg',target/'segmentation-contact-sheet.jpg')
    shutil.copyfile(call/'validation.json',target/'validation.json')
   for img in ['input-1.jpg','input-2.jpg']:shutil.copyfile(dest/img,target/img)
   ex=json.loads((call/'execution.json').read_text());ex.pop('command',None)
   for line in (call/'events.jsonl').read_text().splitlines():
    try:ev=json.loads(line)
    except ValueError:continue
    if ev.get('type')=='turn.completed':ex['usage']=ev.get('usage')
   (target/'execution.json').write_text(json.dumps(ex,ensure_ascii=False,indent=2))
  timings={phase:json.loads((d/'model-calls'/sid/phase/'execution.json').read_text())['elapsed_seconds'] for phase in ['identify','judge']}
  qa={ (q['frame_index'],q['object_id']):q for q in r['segmentation_review']};rows=json.loads((d/sid/'measurements.json').read_text());measure=[]
  for row in rows:
   for ob in row['objects']:
    review=qa.get((row['frame_index'],ob['object_id']))
    if review:
     pos=ob.get('position',{});measure.append('<tr>'+''.join('<td>'+e(v)+'</td>' for v in [f"{row['time']:.2f}s",ob['object_id'],'采用' if review['mask_accepted'] else '拒绝',pos.get('center'),ob.get('area',{}).get('visible_ratio'),ob.get('background_separation',{}).get('color_JS_distance'),review['reason']])+'</tr>')
  checks=''.join('<tr>'+''.join('<td>'+e(c[k])+'</td>' for k in ['stage_id','checkpoint_id','indicator_id','state','time_ranges','input_evidence_ids','observation','impact','context_support','exceptions_checked'])+'</tr>' for c in r['checks'])
  stages=''.join('<li><b>'+e(s['stage_id'])+' '+e(s['time_range'])+'</b>：'+e(s['necessary_information'])+'<br>主体 '+e(s['subject_ids'])+'；陪体 '+e(s['supporting_element_ids'])+'；前景 '+e(s['foreground_ids'])+'；背景 '+e(s['background_ids'])+'<br>关键依据：'+e(s['key_stage_reason'])+'</li>' for s in r['stages'])
  overlays=''.join('<figure><img loading="lazy" src="'+sid+'/'+p.name+'"><figcaption>'+e(p.stem)+'</figcaption></figure>' for p in sorted((dest).glob('overlay-*.jpg')))
  parts.append(f'''<section id="{sid}"><h2>{sid} · 原样本 {source['original_sample_number']} · {e(source['game'])}</h2><video controls preload="metadata" src="{sid}/video.mp4"></video><p>原会话起点 {source['clip_start']:.2f}s；片内时间0–20s；4FPS、80帧。内容识别 {timings['identify']:.1f}s；判档 {timings['judge']:.1f}s。均为本次墙钟实测，不代表固定API延迟。</p><h3>1. 内容提取与阶段</h3><ul>{stages}</ul><details><summary>实际输入的完整序列图</summary><img loading="lazy" src="{sid}/input-1.jpg"><img loading="lazy" src="{sid}/input-2.jpg"></details><h3>2. 分割与测量</h3><p>中心=(x1+x2)/(2W), (y1+y2)/(2H)；可见占比=mask像素数/(W×H)。JS为主体与局部背景Lab直方图距离。它们是证据，不是低中高阈值；拒绝分割对应的数值不采用。无完整主体mask，不输出遮挡率。</p><details><summary>模型审查的覆盖图</summary><div class="gallery">{overlays}</div></details><details><summary>测量值与逐项分割采用／拒绝记录</summary><div class="scroll"><table><tr><th>时间</th><th>对象</th><th>QA</th><th>中心</th><th>可见占比</th><th>颜色JS</th><th>原因</th></tr>{''.join(measure)}</table></div></details><h3>3. VLM判档</h3><p class="grade">{e({'low':'低','middle':'中','high':'高'}.get(grade,r['overall']['status']))}</p><p>{e(r['overall']['reason'])}</p><p>相邻档排除：{e(r['overall']['adjacent_grade_explanation'])}</p><p>决定性检查点：{e(r['overall']['decisive_checkpoint_ids'])}；事件：{e(r['overall']['decisive_event_ids'])}</p><details><summary>完整逐点证据链（{len(r['checks'])}条）</summary><div class="scroll"><table><tr>{''.join('<th>'+x+'</th>' for x in ['阶段','检查点','指标','状态','时间','证据ID','观察','影响','上下文','例外'])}</tr>{checks}</table></div></details><p><a href="{sid}/prediction.json">完整机标JSON</a> · <a href="{sid}/original.mp4">原始片段</a> · <a href="{sid}/measurements.json">逐帧测量JSON</a> · <a href="{sid}/assignment-used.json">对象与定位</a></p><h3>个人批注</h3><textarea data-key="{sid}" placeholder="批注仅保存在当前浏览器，不修改机标结果"></textarea></section>''')
 (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
 for name in ['selection.json','selection-policy.json','config.json','isolation-audit.json','runtime.json','timing.jsonl']:shutil.copyfile(d/name,out/name)
 shutil.copyfile(d/'rubric'/'active-expanded.json',out/'rubric-used.json');shutil.copyfile(d/'rubric'/'active-lock.json',out/'rubric-lock.json')
 header='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>构图 Rubric · 三条试跑</title><style>body{max-width:1120px;margin:30px auto;padding:0 20px;font:16px/1.7 system-ui;color:#203746;background:#f4f7f9}section{background:white;padding:24px;margin:30px 0;border-radius:14px}h2,h3{color:#164e63}video{width:100%;max-height:600px;background:#111}img{max-width:100%}table{border-collapse:collapse;min-width:1000px;font-size:14px}td,th{border:1px solid #ccd8df;padding:9px;vertical-align:top;min-width:100px}.scroll{overflow:auto;max-height:650px}.gallery{display:grid;grid-template-columns:repeat(2,1fr)}figure{margin:8px}textarea{box-sizing:border-box;width:100%;min-height:100px;padding:12px;font:inherit}.grade{font-size:30px;font-weight:bold}summary{cursor:pointer;padding:12px;background:#eaf2f5;margin:12px 0}nav{display:flex;gap:20px;flex-wrap:wrap}</style><h1>构图 Rubric v2.1.1 · 三条试跑</h1><p>非原50条样本。按冻结Rubric由GPT-6.1 Sol判档，保留内容识别→定位分割→测量→逐点证据→整体判档。模型实际看到两张序列图：80张160×90缩略帧，以及第20、60帧的较大参考图；分割覆盖图按640×360排列。原始720p帧保留，但不能声称模型逐帧看到了720p细节。调用途径为本机Codex CLI；实际后端型号无法独立认证。没有使用人工答案或旧机标；独立人工一致率尚未取得。三条随机样本不保证覆盖高中低，不替代全量复跑及验证。</p><nav><a href="../../index.html">项目首页</a><a href="../../rubrics/composition_rubric_v2.html">完整Rubric</a><a href="#T01">T01</a><a href="#T02">T02</a><a href="#T03">T03</a><button onclick="exportNotes()">导出批注</button></nav>'''
 js='''<script>for(const el of document.querySelectorAll('textarea')){const k='rubric-v211-trial3-'+el.dataset.key;el.value=localStorage.getItem(k)||'';el.oninput=()=>localStorage.setItem(k,el.value)}function exportNotes(){const d={};document.querySelectorAll('textarea').forEach(x=>d[x.dataset.key]=x.value);const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(d,null,2)],{type:'application/json'}));a.download='trial3-notes.json';a.click();URL.revokeObjectURL(a.href)}</script></html>'''
 (out/'index.html').write_text(header+''.join(parts)+js);print(out/'index.html')
if __name__=='__main__':main()
