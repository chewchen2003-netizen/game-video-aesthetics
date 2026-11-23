"""Render paired calibration outputs; no rewriting predictions or assigning human labels."""
from pathlib import Path
import json,html
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'runs/composition-five-calibration'
e=lambda x:html.escape(str(x))
def render(run=D):
 def load(p):return json.loads(p.read_text()) if p.exists() and p.stat().st_size else None
 rows=[];details=[]
 for sid in ['R01','R05','R11','R12','R49']:
  rs={arm:load(run/'model-calls'/sid/arm/'result.json') if (run/'model-calls'/sid/arm/'validation.json').exists() else None for arm in ['baseline','candidate']};cells=[];cards=[]
  for arm in ['baseline','candidate']:
   r=rs[arm];w=run/'model-calls'/sid/arm
   if r is None:cells+=['<td>处理中</td><td>—</td>'];cards.append('<article><h3>'+e(arm)+'</h3><p>处理中</p></article>');continue
   o=r['overall'];grade={'low':'低','middle':'中','high':'高'}.get(o['grade'],{'uncertain':'无法判断','not_applicable':'不适用'}.get(o['status'],o['status']));x=load(w/'execution.json');secs=round(x['elapsed_seconds']);usage={}
   for line in (w/'events.jsonl').read_text().splitlines():
    try:v=json.loads(line)
    except ValueError:continue
    if v.get('type')=='turn.completed':usage=v.get('usage',{})
   cells+=['<td><b>'+e(grade)+'</b></td>','<td>'+str(secs)+'秒</td>']
   points=''.join('<tr>'+''.join('<td>'+e(i[k])+'</td>' for k in ['indicator_id','baseline','enhancement','condition_ids','event_ids','uncertainty'])+'</tr>' for i in r['indicators'])
   events=''.join('<li><b>'+e(ev['event_id'])+' '+e(ev['time_ranges'])+'</b> '+e(ev['observation'])+'<br>作用：'+e(ev['effect'])+'<br>证据：'+e(ev['input_evidence_ids'])+'</li>' for ev in r['events'])
   cards.append('<article><h3>'+('原规则 v2.2.0' if arm=='baseline' else '候选规则 v2.3.0')+' · '+e(grade)+'</h3><p>'+e(o['reason'])+'</p><p>相邻档：'+e(o['adjacent_grade_explanation'])+'</p><small>输入 '+e(usage.get('input_tokens','未知'))+' token · 输出 '+e(usage.get('output_tokens','未知'))+' token · '+str(secs)+'秒</small><details><summary>14项判断</summary><div class="scroll"><table><tr><th>指标</th><th>基础</th><th>增强</th><th>条件</th><th>事件</th><th>不确定性</th></tr>'+points+'</table></div></details><details><summary>事件证据</summary><ul>'+events+'</ul></details></article>')
  rows.append('<tr><td><a href="#'+sid+'">'+sid+'</a></td>'+''.join(cells)+'</tr>');details.append('<section id="'+sid+'"><h2>'+sid+'</h2><div class="pair">'+''.join(cards)+'</div></section>')
 b='<h1>5条精简版 · 双规则对照</h1><p>同一输入、同一14项输出；每条分别按原规则与候选规则判断。候选版不要求高档必须传达情感，允许有证据的有效观看引导与空间组织；低档覆盖明确、持续的组织不足，不要求完全看不懂。</p><p>原始CV测量使用缓存，时间只比较本次模型调用；高／低参照参与校准，不能把这5条当独立盲评测试。没有向模型提供人工档位或旧机标。</p><p><a href="/">返回进度</a> · 页面每20秒刷新</p><table><tr><th>样本</th><th>原规则</th><th>模型耗时</th><th>候选规则</th><th>模型耗时</th></tr>'+''.join(rows)+'</table>'+''.join(details)
 style='body{max-width:1250px;margin:30px auto;padding:0 24px;font:15px/1.75 system-ui;background:#f4f7f9;color:#243d4c}h1{font-size:26px}h2{margin-top:35px}h3{font-size:17px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px}article{padding:20px;background:white;border:1px solid #d9e4ea;border-radius:10px;min-width:0}table{border-collapse:collapse;width:100%;background:white}td,th{padding:12px;border:1px solid #dbe5eb;text-align:left;vertical-align:top}.scroll{overflow:auto}.scroll table{min-width:850px}details{margin-top:18px}summary{cursor:pointer;font-weight:600}small{color:#748693}a{color:#176c89}@media(max-width:700px){.pair{grid-template-columns:1fr}}'
 return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="20"><title>五条校准对照</title><style>'+style+'</style>'+b+'</html>'
if __name__=='__main__':(D/'comparison.html').write_text(render())
