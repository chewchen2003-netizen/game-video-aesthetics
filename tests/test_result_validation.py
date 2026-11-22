import unittest,json,sys,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));from validation import validate
class ValidationTests(unittest.TestCase):
 def setUp(self):self.r=json.loads((ROOT/'data/results/results.json').read_text())[0]
 def test_saved_result(self):self.assertEqual(validate(self.r),[])
 def test_no_forced_grade_on_unknown(self):r=copy.deepcopy(self.r);r['status']='uncertain';self.assertIn('status/grade mismatch',validate(r))
 def test_reject_numeric_score(self):r=copy.deepcopy(self.r);r['score']=80;self.assertIn('numeric aesthetic score is not allowed',validate(r))
 def test_reject_missing_evidence(self):r=copy.deepcopy(self.r);r['grade']='high';r['unique_events']=[];self.assertTrue(any('high requires' in x for x in validate(r)))
 def test_reject_duplicate_event(self):r=copy.deepcopy(self.r);r['unique_events'].append(r['unique_events'][0]);self.assertIn('duplicate event IDs',validate(r))
