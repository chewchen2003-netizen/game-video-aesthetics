import json,html
from pathlib import Path
root=Path(__file__).resolve().parents[1]; base=root/'docs/results/composition-v23-review'
data={x['id']:x for x in json.loads((base/'data.json').read_text())}; rubric=json.loads((base/'model-rubric-input.json').read_text());rules={}
def walk(x):
 if isinstance(x,dict):
  if 'id' in x and 'condition' in x:rules[x['id']]=x['condition']
  for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
walk(rubric)
comments={
'R49':'构图评分 高，主体突出、景别合理、空间关系明确。画面中存在持续的构图引导线 p1 3.50s，两侧的低矮石墙形成纵深的引导线，且前中后景清晰，有层次。p2 12s，天空位于上三分之一，上中下分明，画左还有石墙，画右有木屋，构图平衡，但是中景有条边缘线横穿主体脖子，这个不太好。构图整体不错。p3 14.50s，随着主体跳下画面左下方的石阶，镜头自然转向俯视，带出画面上方的村落，自然带出更多的空间信息',
'R01':'构图评分 中，主体清晰；景别裁切合理，持续中景，在背后跟随主体；空间清晰可辨位于草地森林，树叶短暂遮挡视线，但不影响辨别主体位置，无特殊构图手法。构图整体无功无过。p1 0s，p2 1.75s，p3 3s，p4 8s，p5 16s。这个是中的典型case。',
'R13':'构图评分 低，前18s可通过全景建立第三视角观看主体骑马的关系，18s景别突然变小，接近马的近景又到特写，给人从第三视角突然切换到第一视角的突兀感，截图分别是18.00s，18.50s，19.25s，19.50s。后三张图的构图紧、歪斜、丑，且时间轴上来看，这样会让观众对空间产生困惑。这个是低的典型case。'}
times={'R49':[3.5,12,14.5,16],'R01':[0,1.75,3,8,16],'R13':[18,18.5,19.25,19.5]}
notes={'R49':'你强调引导线、三分、平衡与俯视揭示。机器升高的决定性依据是 e2→e3→e4 的连续空间揭示；不是识别出引导线或三分就自动高。你指出的12秒横线穿颈未被机器单独记录，不能写成机器已经检查过；应保留为人工补充的局部瑕疵。机器没有以“跳下石阶”作为已确认动作，后段写的是水渠、木桥与对岸道路。', 'R01':'双方都认为基础观看成立、没有充分增强。你的“无特殊构图手法”可保留；机器实际上识别了近叶、人物、空地、林带的层次，但认为作用止于基本空间可读。中档不等于没有任何构图组织。', 'R13':'双方都把问题定位在末段。机器的低档依据是主体尺度和裁切造成骑手、动作及方向参照损失；没有把“丑”或“歪斜”作为独立低档规则。近似第一人称是你的观看感受，不能认定游戏真实切换了第一人称模式。'}
e=html.escape
parts=['''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>本轮更新：高、中、低典型案例</title><style>body{max-width:1100px;margin:auto;padding:28px;background:#f5f7fa;color:#203646;font:16px/1.75 system-ui}section,article{background:white;padding:24px;border-radius:12px;margin:22px 0}table{border-collapse:collapse;width:100%;font-size:13px}td,th{border:1px solid #cad6df;padding:9px;text-align:left}figure{display:inline-block;width:30%;margin:1%;vertical-align:top}img{width:100%}video{width:100%;max-height:480px}blockquote{border-left:4px solid #459d91;padding:12px;background:#eef8f5}pre{white-space:pre-wrap;overflow-wrap:anywhere}a{color:#126b87}</style><h1>本轮更新：高、中、低典型案例</h1><p>2026-11-24 · 用户选例：R49／R01／R13 · 冻结机标：Rubric 2.3.0。人工评论取自原聊天，属于看过机标后的复核，不是盲评标答。本页引用已有机标，未重新推理。</p><nav><a href="#R49">高 R49</a> · <a href="#R01">中 R01</a> · <a href="#R13">低 R13</a> · <a href="../report.html">报告</a></nav><section><h2>机器按什么规则分档</h2><p>先确定当前需要看懂的主体、动作和空间，再检查适用基础条件，最后检查增强。14项指标不平均、不投票，不按手法数量加分。</p><ul><li>低：至少一个适用最低必要条件被证据明确证明失败，并排除合理特写、正常遮挡、第一人称常规裁切等例外。</li><li>中：适用基础条件成立，但未证明超出基本辨认的增强效果。</li><li>高：继承中档基础，同时有可核查的有效注意引导、空间揭示或关系强化。需要“可见安排→具体联系→增强效果”的证据桥梁。</li></ul><p>关键事实缺失且可能改变最终档位时才无法判断。基础明确成立而增强未证明，应判中。</p><h3>计算公式与判档的关系</h3><p>可见面积占比 = 可见掩码像素数 / (W×H)；测量表 center 是可见区域边界框中心 ((x₁+x₂)/(2W), (y₁+y₂)/(2H))，不是掩码质心；边距为 x₁/W、(W−x₂)/W、y₁/H、(H−y₂)/H。它们描述几何事实，没有面积或位置的美学分档阈值。</p><p>下面仅展示模型实际输入中的测量及其采用范围；accepted=true不代表所有字段都获采用。没有可靠完整主体掩码，遮挡比例不可得；单目深度不是米，不作为这三例增强的数值证明。</p></section>''']
sel=root/'data/reviews/composition-v23-selected-cases/selection.json'
try: selection=json.loads(sel.read_text().rstrip('\\n\n'))
except Exception: selection={'rubric_version':'2.3.0','cases':{}}
for id in ['R49','R01','R13']:
 c=data[id];p=c['prediction']; grade={'high':'高','middle':'中','low':'低'}[p['overall']['grade']]; frames={f['frame_index']:f for f in c['frames']}
 def gallery(indices):
  out=''
  for ix in dict.fromkeys(indices):
   if ix not in frames:continue
   f=frames[ix];url="composition-v23-review/"+f["url"]
   out+=f'<figure><a href="{url}"><img loading="lazy" src="{url}"></a><figcaption>{f["time"]:.2f}s · rgb-{ix:04d}</figcaption></figure>'
  return out
 parts+=[f'<section id="{id}"><h2>{grade}档 · {id} · {e(c["game"])}</h2><p><a href="composition-v23-review/index.html#{id}">原审核页</a> · <a href="composition-v23-review/{id}/prediction.json">冻结机标JSON</a> · <a href="composition-v23-review/{id}/call/prompt.txt">实际提示词</a></p><h3>机器过程 ① 主体、陪体与环境提取</h3><p>依据有序RGB采样，先确认当前主要呈现对象及其与环境的关系，再按观看任务变化切分阶段。以下为冻结机标保存的识别结果。</p><table><tr><th>对象／角色</th><th>时间（秒）</th><th>提取依据及不确定性</th></tr>']
 for role in p['roles']:
  parts+=[f'<tr><td>{e(role["object_id"])} / {e(role["role"])}</td><td>{e(str(role["time_range"]))}</td><td>{e(role["description"])} {e(role.get("uncertainty",""))}</td></tr>']
 parts+=['</table><h4>阶段与最低必要信息</h4>']
 for stage in p['stages']:
  parts+=[f'<p><b>{e(stage["stage_id"])} · {e(str(stage["time_range"]))}秒：</b>{e(stage["necessary_information"])}</p>']
 parts+=[f'<h3>机器过程 ② 分割与掩码核验</h3><p>本轮复用既有CV分割与测量缓存，没有重跑分割。模型对照RGB、掩码QA和测量记录逐项接受或拒绝；原始分割不等于正确答案，漏分与混分的派生值不能进入判档。</p><a href="composition-v23-review/{id}/mask-qa.jpg"><img loading="lazy" src="composition-v23-review/{id}/mask-qa.jpg" alt="{id} 分割掩码核验图"></a><p>具体接受／拒绝理由见下表最后一列；有限采用只指记录中明确允许的用途。</p>']
 measurement_start=len(parts)
 parts+=['<h3>机器过程 ④ 事件证据：画面安排 → 观看影响</h3>']
 for event in p['events']:
  if event['event_id'] not in p['overall']['decisive_event_ids']:continue
  ids=[int(x.split('-')[1]) for x in event['input_evidence_ids'] if x.startswith('rgb-')]
  parts+=[f'<article><h4>{e(event["event_id"])} · {e(str(event["time_ranges"]))} 秒</h4><p>观察：{e(event["observation"])}</p><p>作用：{e(event["effect"])}</p><p>排除例外：{e(event["exceptions_checked"])}</p>'+gallery(ids[:1]+ids[-2:])+'</article>']
 judgment_start=len(parts)
 parts+=[f'<h3>机器过程 ⑤ 规则核对 → 最终判档</h3><p>{e(p["overall"]["reason"])}</p><p>{e(p["overall"]["adjacent_grade_explanation"])}</p><table><tr><th>规则</th><th>实际Rubric原文</th></tr>']
 for rule in p['overall']['condition_ids']:parts+=[f'<tr><td>{rule}</td><td>{e(rules.get(rule,"见完整Rubric"))}</td></tr>']
 parts+=['</table>']
 judgment_end=len(parts)
 parts+=['<h3>机器过程 ③ 实际测量与采用情况</h3><table><tr><th>测量／时间</th><th>可见面积占比</th><th>框中心</th><th>模型核验与用途</th></tr>']
 measurements={m['id']:m for m in json.loads((base/id/'model-evidence.json').read_text())['measurements']}
 for review in p['segmentation_review']:
  m=measurements.get(review['measurement_id'],{}); ratio=m.get('visible_ratio');center=m.get('center')
  parts+=[f'<tr><td>{e(review["measurement_id"])}<br>{m.get("time","—")}s</td><td>{f"{ratio*100:.3f}%" if ratio is not None else "—"}</td><td>{e(str([round(v,4) for v in center])) if center else "—"}</td><td>{"有限采用" if review["accepted"] else "拒绝，不能参与判档"}：{e(review["reason"])}</td></tr>']
 parts+=['</table><p>表中拒绝行仅为审计展示，数值不能用于证明档位。所有公式均为观测计算，最终按上述语义规则判档。</p><details><summary>14项指标的完整判定与证据引用</summary><pre>'+e(json.dumps(p['indicators'],ensure_ascii=False,indent=2))+'</pre></details><p>限制：'+e('；'.join(p['overall']['uncertainties']))+'</p>']
 measurement_parts=parts[judgment_end:]
 del parts[judgment_end:]
 judgment_parts=parts[judgment_start:]
 del parts[judgment_start:]
 parts[measurement_start:measurement_start]=measurement_parts
 parts+=judgment_parts
 parts+=[f'<h3>人工复核：你的 comments（原文）</h3><blockquote>{e(comments[id])}</blockquote><h4>你指定的时间截图</h4>'+gallery([round(t*4) for t in times[id]])+f'<p>{e(notes[id])}</p></section>']
 record=selection['cases'].setdefault(id,{})
 record.update(selected_grade=p['overall']['grade'],machine_grade=p['overall']['grade'],original_comment=comments[id],comment_times=times[id],review_type='post_machine_result_review_not_blind',source='original_chat_user_comments',machine_evidence_source=f'docs/results/composition-v23-review/{id}/prediction.json')
parts+=['<footer>来源：本轮 data.json、prediction.json、model-evidence.json、实际 model-rubric-input.json；截图引用实际模型输入帧。人工补充与机器已记录事实分别标明。</footer></html>']
out=root/'docs/results/composition-v23-selected-cases.html';out.write_text(''.join(parts));sel.write_text(json.dumps(selection,ensure_ascii=False,indent=2)+'\n')
r=root/'REPORT.md';text=r.read_text();line='|[本轮更新：用户选定的高、中、低典型案例](docs/results/composition-v23-selected-cases.html)|R49高、R01中、R13低：人工comments、实际输入截图、机器证据链、公式与测量采用记录、规则和相邻档解释|'
if line not in text:text=text.replace('## 一、分类标准与算子表',line+'\n\n## 一、分类标准与算子表')
r.write_text(text)
r=root/'docs/report.html';s=r.read_text();link='<p><a href="results/composition-v23-selected-cases.html">本轮更新：R49高／R01中／R13低，人工评论与机器判档证据</a></p>'
if link not in s:s=s.replace('</main>',link+'</main>')
r.write_text(s)
print(out)
