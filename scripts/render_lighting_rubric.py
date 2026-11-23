"""Render the concise lighting design draft and its observation knowledge."""
from pathlib import Path
import json,html,shutil
ROOT=Path(__file__).resolve().parents[1];r=json.loads((ROOT/'rubrics/lighting_rubric.json').read_text());out=ROOT/'docs/rubrics';out.mkdir(exist_ok=True)
e=lambda x:html.escape(str(x))
names={'lighting-logic-1':'光源与受光方向','lighting-logic-2':'阴影关系','lighting-logic-3':'光照随运动变化','lighting-volume-1':'明暗面区分','lighting-volume-2':'形体转折表现','lighting-volume-3':'局部结构呈现','light-tech-0':'轮廓光','light-tech-1':'逆光','light-tech-2':'丁达尔光','light-tech-3':'伦勃朗光','light-tech-4':'蝴蝶光','light-tech-5':'霓虹光','light-tech-7':'聚光灯追踪'}
ul=lambda xs:'<ul>'+''.join('<li>'+e(x)+'</li>' for x in xs)+'</ul>'
b='<nav><a href="../game-tag-tree.html">返回评价标准</a> · <a href="lighting_rubric.json">规则JSON</a></nav><h1>光影 Rubric · 方法草案</h1><p class="notice">尚未执行或验证。沿用标签树的光照逻辑、体积塑造与光影手法；以下经验辅助观察，不是光型、情绪与档位的固定对应。</p><h2>模型输入</h2>'+ul(r['input'].values())+'<h2>评价因素与观察问题</h2>'
for f in r['factors']:b+='<section id="'+e(f['id'])+'"><h3>'+e(f['name'])+'</h3><p>指标：'+e('、'.join(names[x] for x in f['indicator_ids']))+'</p>'+ul(f['questions'])+'</section>'
b+='<h2>整体判档思路</h2>'
for k,label in [('low','低'),('middle','中'),('high','高'),('uncertain','无法判断'),('not_applicable','不适用')]:b+='<p><b>'+label+'：</b>'+e(r['overall_scoring_guidance'][k])+'</p>'
b+='<h2 id="observation-knowledge">观察知识</h2><p>性质、方向、来源、功能相互独立。同一光线可同时具有多个属性；先看实际画面，再说明作用。</p>'
for group,label in [('light_quality','一、性质：硬光与软光'),('light_direction','二、方向：以机位与主体朝向为参照'),('light_source','三、光线来源'),('light_function','四、功能：主光、辅光与其他分工')]:
 b+='<details open><summary>'+label+'</summary>'
 for x in r['observation_knowledge'][group]:
  b+='<section id="'+e(x['id'])+'"><h3>'+e(x['name'])+'</h3><p><b>如何观察：</b>'+e(x['observable_cues'])+'</p><p><b>可能的作用：</b>'+e(x['possible_effect'])+'</p><p class="boundary"><b>判断边界：</b>'+e(x['boundaries'])+'</p><p class="refs">关联指标：'+e('、'.join(names[i] for i in x['indicator_ids']))+'</p></section>'
 b+='</details>'
b+='<h2>通用边界与证据</h2>'+ul(r['rules'])+ul(r['evidence_requirements'])+'<h2>验证方案</h2><p>'+e(r['validation_plan'])+'</p>'
style='*{box-sizing:border-box}body{max-width:1100px;margin:30px auto;padding:0 25px;background:#f7fafb;color:#233e4d;font:16px/1.85 system-ui}h1{font-size:28px}h2{margin-top:36px;border-top:1px solid #ccdae1;padding-top:20px}h3{font-size:18px;color:#24566d;margin:0 0 10px}section{background:white;border:1px solid #dde6ea;border-radius:9px;padding:18px 22px;margin:16px 0}.notice{background:#fff4d7;padding:14px 20px;border-left:3px solid #bd8d28}.boundary{background:#f3f6f8;padding:10px 14px}.refs{color:#758692;font-size:13px}summary{font-weight:650;cursor:pointer;background:#e9f1f5;padding:12px 16px;border-radius:8px}details{margin:20px 0}a{color:#1a6d87}'
(out/'lighting_rubric.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>光影Rubric·观察知识</title><style>'+style+'</style>'+b+'</html>');shutil.copyfile(ROOT/'rubrics/lighting_rubric.json',out/'lighting_rubric.json');print('Rendered lighting rubric observation knowledge')
