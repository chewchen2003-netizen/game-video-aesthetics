"""Render color knowledge inside its evaluation factors and indicators."""
from pathlib import Path
import json,html,shutil
ROOT=Path(__file__).resolve().parents[1];r=json.loads((ROOT/'rubrics/vocal_rubric.json').read_text());out=ROOT/'docs/rubrics';out.mkdir(exist_ok=True)
e=lambda x:html.escape(str(x))
ul=lambda xs:'<ul>'+''.join('<li>'+e(x)+'</li>' for x in xs)+'</ul>'
b='<nav><a href="../game-tag-tree.html">返回评价标准</a> · <a href="vocal_rubric.json">规则JSON</a></nav><h1>人声 Rubric · 方法草案</h1><p class="notice">尚未执行或验证。观察经验直接服务光照逻辑、体积塑造与人声手法；光型不与情绪或档位固定对应。</p><h2>模型输入</h2>'+ul(r['input'].values())+'<h2 id="observation-knowledge">评价因素与指标</h2><nav class="factors">'+''.join('<a href="#'+e(f['id'])+'">'+e(f['name'])+'</a>' for f in r['factors'])+'</nav>'
for f in r['factors']:
 knowledge={x['id']:x for x in f['observation_knowledge']};b+='<section class="factor" id="'+e(f['id'])+'"><h2>'+e(f['name'])+'</h2>'+ul(f['questions'])
 for i in f['indicators']:
  b+='<section class="indicator" id="'+e(i['id'])+'"><h3>'+e(i['name'])+'</h3><p><b>观察：</b>'+e(i['observation'])+'</p><p><b>判断：</b>'+e(i['judgement'])+'</p><p class="boundary"><b>作用与边界：</b>'+e(i['effect_and_boundary'])+'</p>'
  if i['knowledge_refs']:
   b+='<details><summary>这些经验如何帮助观察：'+e('、'.join(knowledge[k]['name'] for k in i['knowledge_refs']))+'</summary>'
   for key in i['knowledge_refs']:
    x=knowledge[key];b+='<div class="knowledge"><h4>'+e(x['name'])+'</h4><p>'+e(x['observable_cues'])+'</p><p><b>可能作用：</b>'+e(x['possible_effect'])+'</p><p><b>边界：</b>'+e(x['boundaries'])+'</p></div>'
   b+='</details>'
  b+='</section>'
 b+='</section>'
b+='<h2>整体判档思路</h2>'
for k,label in [('low','低'),('middle','中'),('high','高'),('uncertain','无法判断'),('not_applicable','不适用')]:b+='<p><b>'+label+'：</b>'+e(r['overall_scoring_guidance'][k])+'</p>'
b+='<h2>通用边界与证据</h2>'+ul(r['rules'])+ul(r['evidence_requirements'])+'<h2>验证方案</h2><p>'+e(r['validation_plan'])+'</p>'
style='*{box-sizing:border-box}body{max-width:1100px;margin:30px auto;padding:0 25px;background:#f7fafb;color:#233e4d;font:16px/1.85 system-ui}h1{font-size:28px}h2{margin-top:36px;padding-top:12px}h3{font-size:18px;color:#24566d;margin:0 0 10px}h4{margin:0;font-size:16px}.factor{margin:35px 0;border-top:2px solid #7897a7}.indicator{background:white;border:1px solid #dde6ea;border-radius:9px;padding:18px 22px;margin:16px 0}.notice{background:#fff4d7;padding:14px 20px;border-left:3px solid #bd8d28}.boundary{background:#f3f6f8;padding:10px 14px}summary{font-weight:550;cursor:pointer;background:#edf3f6;padding:10px 14px;border-radius:7px}details{margin:16px 0}.knowledge{padding:14px 18px;border-left:2px solid #c3d5de;margin-top:12px}.knowledge p{margin:5px 0}a{color:#1a6d87}.factors{display:flex;gap:25px;flex-wrap:wrap}'
(out/'vocal_rubric.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>人声Rubric·评价因素与观察依据</title><style>'+style+'</style>'+b+'</html>');shutil.copyfile(ROOT/'rubrics/vocal_rubric.json',out/'vocal_rubric.json');print('Rendered integrated color factors and indicators')
