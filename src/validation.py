"""Validate categorical results; this does not certify aesthetic correctness."""
IND={'subject-position','subject-area','subject-occlusion','subject-separation','shot-crop-joint','shot-crop-headroom','shot-crop-look-room','shot-crop-lead-room','shot-crop-action-crop','spatial-depth','spatial-vertical','spatial-overlap'}
TECH={'对称','纵深构图','镜面构图','框架构图','留白','三分法','分屏','画中画'}
def validate(r,bid=None):
 errors=[]
 if bid and r.get('blind_id')!=bid:errors.append('blind_id mismatch')
 if r.get('status') not in ['scored','uncertain','not_applicable']:errors.append('invalid status')
 if (r.get('status')=='scored' and r.get('grade') not in ['high','middle','low']) or (r.get('status')!='scored' and r.get('grade') is not None):errors.append('status/grade mismatch')
 if r.get('score') is not None:errors.append('numeric aesthetic score is not allowed')
 if len(r.get('indicator_assessments',[]))!=12 or {v.get('indicator_id') for v in r.get('indicator_assessments',[])}!=IND:errors.append('need exactly 12 indicators')
 if len(r.get('technique_evidence',[]))!=8 or {v.get('technique') for v in r.get('technique_evidence',[])}!=TECH:errors.append('need exactly 8 techniques')
 events=r.get('unique_events',[]);ids=[e.get('event_id') for e in events]
 if len(ids)!=len(set(ids)):errors.append('duplicate event IDs')
 for e in events:
  t=e.get('time_range',[])
  if len(t)!=2 or not 0<=t[0]<=t[1]<=20:errors.append('event time outside clip')
  if any(not isinstance(i,int) or not 0<=i<80 for i in e.get('evidence_frame_indices',[])):errors.append('invalid event frame')
 for f in r.get('factor_diagnostics',[]):
  if (f.get('status')=='scored')!=(f.get('grade') in ['high','middle','low']):errors.append('factor status/grade mismatch')
  if not set(f.get('event_ids',[]))<=set(ids):errors.append('unknown event reference')
 for t in r.get('technique_evidence',[]):
  if t.get('recognition')!='存在' and t.get('effect') is not None:errors.append('effect for unrecognized technique')
  if t.get('recognition')=='存在' and not t.get('evidence_segments'):errors.append('technique lacks evidence')
 if r.get('grade')=='high' and not any(e.get('kind')=='positive_effect' and len(set(e.get('evidence_frame_indices',[])))>=2 for e in events):errors.append('high requires concrete positive effect with multiple frames')
 for e in r.get('evidence',[]):
  if not isinstance(e.get('frame_index'),int) or not 0<=e['frame_index']<80:errors.append('invalid evidence frame')
 return errors
