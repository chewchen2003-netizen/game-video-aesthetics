"""Build a compact, structured, isolated vision task for Codex CLI."""
from pathlib import Path
import json,os
P=Path(__file__).resolve().parent;ROOT=P.parent;D=Path(os.environ.get('GAME_EVAL_RUN_DIR',ROOT/'runs/reproduction')).resolve();D.mkdir(parents=True,exist_ok=True)
def obj(p):return {'type':'object','properties':p,'required':list(p),'additionalProperties':False}
def string(enum=None):return {'type':'string',**({'enum':enum} if enum else {})}
def arr(t):return {'type':'array','items':t}
nullable_grade={'type':['string','null'],'enum':['high','middle','low',None]};times=arr({'type':'number'});ids=arr(string())
SCHEMA=obj({'blind_id':string(),'status':string(['scored','uncertain','not_applicable']),'grade':nullable_grade,'summary':string(),'factor_diagnostics':arr(obj({'factor_id':string(['composition-prominence','composition-shot-size','composition-spatial-layering']),'subject_id':{'type':['string','null']},'time_range':times,'status':string(['scored','uncertain','not_applicable']),'grade':nullable_grade,'summary':string(),'event_ids':ids})), 'indicator_assessments':arr(obj({'indicator_id':string(['subject-position','subject-area','subject-occlusion','subject-separation','shot-crop-joint','shot-crop-headroom','shot-crop-look-room','shot-crop-lead-room','shot-crop-action-crop','spatial-depth','spatial-vertical','spatial-overlap']),'applicability':string(['applicable','not_applicable','uncertain']),'effect':string(['支持','削弱','中性','证据不足']),'evidence':string()})), 'technique_evidence':arr(obj({'technique':string(['对称','纵深构图','镜面构图','框架构图','留白','三分法','分屏','画中画']),'recognition':string(['存在','不存在','无法判断']),'effect':{'type':['string','null'],'enum':['有效','普通','造成问题','无法判断',None]},'effect_reason':string(),'evidence_segments':arr(obj({'time_range':times,'elements':ids,'relationship':string(),'event_id':{'type':['string','null']}})),'related_factors':ids})), 'unique_events':arr(obj({'event_id':string(),'kind':string(['positive_effect','problem','basic_organization','unconfirmed_risk']),'time_range':times,'object_ids':ids,'relationship':string(),'observation':string(),'impact':string(),'evidence_frame_indices':arr({'type':'integer'})})), 'measurement_qa':obj({'summary':string(),'rejections':arr(obj({'object_id':string(),'frame_indices':arr({'type':'integer'}),'scope':string(['mask','pose','depth']),'reason':string()}))}), 'evidence':arr(obj({'frame_index':{'type':'integer'},'observation':string(),'impact':string()})), 'uncertainties':ids})
(D/'terminal-output-schema.json').write_text(json.dumps(SCHEMA,ensure_ascii=False))
def task(bid):
 nodes=json.loads((ROOT/'data/standards/composition-frozen-contracts.json').read_text());defs=[]
 for n in nodes:
  if n['id']=='composition':defs.append({'id':n['id'],'overallScoring':n['overallScoring']})
  elif n['id'] in ['composition-prominence','composition-shot-size','composition-spatial-layering','composition-techniques']:
   io={k:v for k,v in n.get('integratedOperator',{}).items() if k not in ['example','references','source']};defs.append({'id':n['id'],'description':n.get('description'),'grading':n.get('grading'),'operator':io,'techniqueDefinitions':n.get('techniqueDefinitions')})
 d=D/bid;rows=json.loads((d/'measurements.json').read_text());ass=json.loads((D/'assignments'/(bid+'.json')).read_text());summary=json.loads((d/'summary.json').read_text());chosen={0,16,32,48,64,79}
 summary['overlap_pairs']={k:[{'time':x['time'],'geometry':{direction:{key:value for key,value in data.items() if key!='near_locations_xy'} for direction,data in x.get('geometry',{}).items()}} for x in vals if int(round(x['time']*4)) in chosen] for k,vals in summary.get('overlap_pairs',{}).items()}
 summary['depth_orders']=summary.get('depth_orders',[])[::max(1,len(summary.get('depth_orders',[]))//5)]
 for o in summary['objects'].values():
  for j in o.get('joint_distance_summary',[]):j.pop('nearest_observations',None)
 snaps=[]
 for row in rows:
  if row['frame_index'] not in chosen:continue
  rr={k:v for k,v in row.items() if k!='overlap_pairs'}
  rr['objects']=[{k:v for k,v in o.items() if k not in ['mask_file','localization_seed','motion_front','semantic_validity','occlusion','look_room','action_crop']} for o in row['objects']]
  snaps.append(rr)
 prompt='''你是独立的游戏视频构图算子综合判断环节。只使用所附原画面序列图、测量QA图、实际测量和原始评价定义。不读取其他文件、浏览器、人工答案或既有预测。不要调用工具，不写代码，只返回符合schema的JSON。\n原视频20秒，4FPS采样80帧；每张序列图上面40帧，左到右上到下，底部重复清晰参考帧；上传图片数量不是视频帧数。网格和文字不是游戏画面。只评价构图，不评动作丰富性。\n严格执行输入/测量有效性检查→按主体和阶段评价三因素→八项手法逐项识别及效果→按事件ID去重→综合输出。缺失为null/证据不足，不按有效值数量、均值、权重或手法数量评分。高档必须给具体对象关系、实际效果和多个证据帧；清楚/完整本身不足判高。\n核对掩码和姿态是否属于指定对象；如果SAM误选武器或墙、倒置姿态解剖对应错误，列出rejections。frame_indices为空数组代表该对象所有时刻都拒绝。没有可靠主要阶段输入时返回uncertain，不能把无法判断当成低或不适用。\n人体、草丛遮挡、第一人称武器、交互正常离框等按例外处理，不仅凭框触边或关键点消失扣分。屏幕位移不等于世界运动；单目深度是同帧相对逆深度，不是米。天空、火、透明粒子、二维地图不作可靠三维几何。身体尺度被裁切时关节距离/S无效；人物框顶部不能冒充头顶。\n总体和因素status非scored时grade=null；最终只输出低/中/高；无法判断与不适用单列；不输出数值分数。indicator_assessments必须覆盖12项；technique_evidence必须覆盖全部八项。每项手法识别与效果分开，无手法不扣分。\n输出中文简洁可核查理由。evidence最多3条，frame_index0..79。不得猜测创作意图，不输出冗长推演。\n'''
 payload={'blind_id':bid,'indicator_definitions':[{'id':n['id'],'name':n['name'],'definition':n['evaluationSpec']} for n in nodes if n.get('evaluationSpec')],'original_contracts':defs,'subject_assignment':ass,'measured_summary':summary,'actual_measurement_snapshots':snaps,'raw_measurement_count':len(rows),'human_answers_available':False,'note':'QA图仅显示16个均匀抽取时刻；测量仍需语义检查，未检查到的问题不等于不存在。'}
 (d/'terminal-task.txt').write_text(prompt+json.dumps(payload,ensure_ascii=False));return d/'terminal-task.txt'
if __name__=='__main__':
 import sys
 print(task(sys.argv[1]))
