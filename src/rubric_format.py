"""Lossless compact representation of a frozen rubric; no grading logic changes."""
from copy import deepcopy
import json

FORMAT='composition_rubric_compact_v1'

def load_rubric(path):
    """Load the sole stored rubric and materialize shared evidence in memory."""
    from pathlib import Path
    value=json.loads(Path(path).read_text())
    return expand_rubric(value) if '_storage' in value else value

def compact_rubric(rubric):
    compact=deepcopy(rubric)
    if '_storage' in compact or '_checkpoint_evidence_defaults' in compact:
        raise ValueError('Reserved compact format keys already present')
    defaults={}
    for grade in ['low','middle','high']:
        lists=[f['scoring_guidance'][grade]['checks'][0]['required_evidence'] for f in rubric['factors']]
        if not all(value==lists[0] for value in lists):
            raise ValueError('Cannot infer a common evidence default for '+grade)
        defaults[grade]=deepcopy(lists[0])
    compact['_storage']={'format':FORMAT,'meaning':'Only repeated evidence lists are inherited by grade; expand before model input. No assessment text or conditions changed.'}
    compact['_checkpoint_evidence_defaults']=defaults
    for factor in compact['factors']:
        for grade,guidance in factor['scoring_guidance'].items():
            for point in guidance['checks']:
                if point['required_evidence']==defaults[grade]:del point['required_evidence']
    return compact

def expand_rubric(compact):
    expanded=deepcopy(compact)
    if expanded.pop('_storage')['format']!=FORMAT:raise ValueError('Unsupported compact rubric format')
    defaults=expanded.pop('_checkpoint_evidence_defaults')
    for factor in expanded['factors']:
        for grade,guidance in factor['scoring_guidance'].items():
            for point in guidance['checks']:
                if 'required_evidence' not in point:point['required_evidence']=deepcopy(defaults[grade])
    return expanded

def dumps_readable(value):
    """One check/indicator per line; keep top-level sections easy to scan."""
    def inline(x):return json.dumps(x,ensure_ascii=False,separators=(', ',': '))
    def render(x,path=(),depth=0):
        pad='  '*depth
        if path and path[0] not in ['factors','rules','overall_scoring_guidance','_checkpoint_evidence_defaults']:
            return inline(x)
        if path and path[0]=='overall_scoring_guidance' and depth>=2:return inline(x)
        if path and path[0]=='_checkpoint_evidence_defaults' and depth>=2:return inline(x)
        if path and path[-1] in ['low','middle','high'] and path[0]=='_checkpoint_evidence_defaults':return inline(x)
        if isinstance(x,list):
            if not x:return '[]'
            return '[\n'+',\n'.join('  '*(depth+1)+render(y,path+('*',),depth+1) for y in x)+'\n'+pad+']'
        if isinstance(x,dict):
            if path and path[-1]=='*' and ('condition' in x or 'definition' in x):return inline(x)
            if not x:return '{}'
            return '{\n'+',\n'.join('  '*(depth+1)+inline(k)+': '+render(v,path+(k,),depth+1) for k,v in x.items())+'\n'+pad+'}'
        return inline(x)
    return render(value)+'\n'
