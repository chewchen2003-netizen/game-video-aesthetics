"""Render a human-readable page from the verified canonical JSON, without inference."""
from pathlib import Path
import html,json,shutil
from check_composition_rubric import check,ROOT

rubric,lock=check()
out=ROOT/'docs/rubrics';out.mkdir(parents=True,exist_ok=True)
def e(value):return html.escape(str(value))
def lst(values):return '<ul>'+''.join('<li>'+e(v)+'</li>' for v in values)+'</ul>'
body='<h1>构图 Rubric · v'+e(rubric['version'])+'</h1>'
body+='<p class="notice">已冻结用于验证，尚未完成验证。此页是新规则，不是原50条结果的判档依据；本次没有重新推理。</p>'
body+='<p><a href="composition_rubric.json">构图规则 JSON</a> · <a href="composition_rubric.lock.json">版本与校验记录</a></p>'
body+='<h2>角色与评价范围</h2><p>'+e(rubric['role'])+'</p><p>由 GPT-6.1 Sol 承担VLM判档；不设置数值美学分数或因素权重。实际调用模型信息须随运行单独保存。</p>'
body+='<h2>共同定义</h2><dl>'
names={'expression':'表达','basic_presentation':'基本呈现','expressive_enhancement':'进一步表情达意','subject':'主体','supporting_element':'陪体','material_comprehension_harm':'关键理解损害','applicability':'适用性','evidence_insufficiency':'证据不足'}
for key,value in rubric['definitions'].items():
    if key=='environment':
        body+='<dt>环境</dt><dd>'+e(value['definition'])+lst([k+'：'+v for k,v in value['subtypes'].items()])+'</dd>'
    else:body+='<dt>'+e(names.get(key,key))+'</dt><dd>'+e(value)+'</dd>'
body+='</dl><h2>通用规则</h2>'+lst(rubric['rules'])
body+='<h2>评价前提</h2>'+lst(rubric['preconditions']['required'])+'<p>'+e(rubric['preconditions']['role_uncertainty'])+'</p>'
labels={'low':'低：妨碍理解','middle':'中：基本呈现成立','high':'高：进一步表情达意'}
for factor in rubric['factors']:
    imap={x['id']:x for x in factor['indicators']}
    body+='<h2 id="'+e(factor['id'])+'">'+e(factor['name'])+'</h2><p>'+e(factor['criteria'])+'</p>'
    if factor['effect_only']:body+='<p>先确认手法是否存在；未识别到明确手法不扣档、不强制定为中。效果证据关联到整体，不独立加分。</p>'
    for grade,title in labels.items():
        guidance=factor['scoring_guidance'][grade]
        logic={'low':'任一问题确认且造成关键理解损害。','middle':'无确认的关键理解损害，全部适用基础点成立。','high':'继承中档全部适用条件，再证明至少一种实质表达效果；不按命中数量加分。'}[grade]
        body+='<h3>'+e(title)+'</h3><p>'+e(logic)+'</p><div class="table"><table><thead><tr><th>检查点</th><th>唯一关联指标</th><th>判断条件</th></tr></thead><tbody>'
        for point in guidance['checks']:body+='<tr><td>'+e(point['id'])+'</td><td>'+e(point['letter']+'．'+imap[point['indicator_id']]['name'])+'</td><td>'+e(point['condition'])+'</td></tr>'
        body+='</tbody></table></div>'
    body+='<details><summary>指标定义与合理例外</summary><dl>'
    for indicator in factor['indicators']:body+='<dt>'+e(indicator['letter']+'．'+indicator['name'])+'</dt><dd>'+e(indicator['definition'])+lst(indicator['exceptions'])+'</dd>'
    body+='</dl></details>'
body+='<h2>构图整体判档</h2>'
for grade,title in labels.items():
    guidance=rubric['overall_scoring_guidance'][grade]
    logic={'low':'以下任一成立，并引用下层问题、实际损害和例外检查。','middle':'以下全部适用条件成立，允许不影响基本呈现的不足。','high':'满足全部中档条件，并至少有以下一种表达得到充分证明。'}[grade]
    body+='<h3>'+e(title)+'</h3><p>'+e(logic)+'</p>'+lst([p['id']+'：'+p['condition'] for p in guidance['checks']])
    if grade=='high':body+='<p>每个增强效果还必须全部满足：</p>'+lst(guidance['all_required_for_each_effect'])+'<p>'+e(guidance['technical_mechanism'])+'</p>'
for key in ['uncertain','not_applicable','unresolved_case']:body+='<p><strong>'+e({'uncertain':'无法判断','not_applicable':'不适用','unresolved_case':'矛盾或未解决情形'}[key])+'：</strong>'+e(rubric['overall_scoring_guidance'][key])+'</p>'
body+='<h2>输出与运行证据</h2><p>逐点记录：检查点、唯一指标、阶段、状态、时间码、实际输入证据ID、观察、影响、上下文、例外、事件ID及不确定性。</p><p>整体记录：状态、档位、基础呈现、关键损害、进一步表达、整体条件编号、决定性检查点与事件、简洁理由、相邻档排除理由。</p>'+lst(rubric['run_record_requirements'])
body+='<h2>验证状态与边界</h2>'+lst(rubric['known_limits'])+'<p class="hash">SHA256：'+e(lock['sha256'])+'</p>'
style='*{box-sizing:border-box}body{max-width:1100px;margin:32px auto;padding:0 24px;font:16px/1.9 system-ui;color:#243746;background:#fbfcfd}h1{font-size:30px}h2{margin-top:48px;border-top:2px solid #365f72;padding-top:18px}h3{margin-top:26px;color:#244d61}a{color:#086b87}table{border-collapse:collapse;width:100%}td,th{border:1px solid #d5e0e6;padding:12px;text-align:left;vertical-align:top}th{background:#edf3f6}td:first-child{white-space:nowrap}.table{overflow-x:auto}.notice{padding:16px;background:#fff2ce;border-left:4px solid #b98223}dt{font-weight:650;margin-top:15px}dd{margin-left:0}.hash{overflow-wrap:anywhere;font-size:13px}summary{cursor:pointer;margin-top:18px}@media(max-width:650px){body{padding:0 16px}h1{font-size:24px}table{min-width:600px}}'
(out/'composition_rubric_v2.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>构图Rubric</title><style>'+style+'</style><nav><a href="../index.html">项目首页</a> · <a href="../report.html">原交付说明</a></nav>'+body+'</html>')
for name in ['composition_rubric.json','composition_rubric.lock.json']:shutil.copyfile(ROOT/'rubrics'/name,out/name)
print('Rendered:',out/'composition_rubric_v2.html')
