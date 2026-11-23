"""Reject incomplete or fabricated evidence references before accepting a trial output."""
import copy,importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('trial',ROOT/'scripts/run_rubric_trial.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class TrialValidationTests(unittest.TestCase):
 def setUp(self):
  self.rule=m.load_rubric(ROOT/'rubrics/composition_rubric.json')
  checks=[{'checkpoint_id':p['id'],'indicator_id':p['indicator_id'],'stage_id':'s1','state':'not_applicable','time_ranges':[],'input_evidence_ids':[],'observation':'无相关对象','impact':'','context_support':'','exceptions_checked':[],'event_ids':[],'uncertainty':''} for f in self.rule['factors'] for g in f['scoring_guidance'].values() for p in g['checks']]
  self.r={'stages':[{'stage_id':'s1','time_range':[0,20],'input_evidence_ids':['rgb-0000']}],'checks':checks,'events':[],'overall':{'status':'uncertain','grade':None,'decisive_checkpoint_ids':[],'decisive_event_ids':[]},'segmentation_review':[{'frame_index':0,'object_id':'p','mask_accepted':False,'reason':'bad mask'}]};self.frames={'rgb-0000':{}};self.measures={'measure-0000-p':(0,'p')}
 def test_complete_references_pass(self):self.assertTrue(m.validate(self.r,self.rule,self.frames,self.measures)['passed'])
 def test_missing_checkpoint_rejected(self):
  self.r['checks'].pop()
  with self.assertRaises(AssertionError):m.validate(self.r,self.rule,self.frames,self.measures)
 def test_invented_evidence_rejected(self):
  self.r['checks'][0]['input_evidence_ids']=['rgb-9999']
  with self.assertRaises(AssertionError):m.validate(self.r,self.rule,self.frames,self.measures)
 def test_missing_mask_review_rejected(self):
  self.r['segmentation_review']=[]
  with self.assertRaises(AssertionError):m.validate(self.r,self.rule,self.frames,self.measures)
 def test_confirmed_failure_cannot_be_hidden_as_uncertain(self):
  next(c for c in self.r['checks'] if '-B-' in c['checkpoint_id'])['state']='not_met'
  with self.assertRaises(AssertionError):m.validate(self.r,self.rule,self.frames,self.measures)
 def test_grade_status_mismatch_rejected(self):
  self.r['overall']['grade']='high'
  with self.assertRaises(AssertionError):m.validate(self.r,self.rule,self.frames,self.measures)
if __name__=='__main__':unittest.main()
