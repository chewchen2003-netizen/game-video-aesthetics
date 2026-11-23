"""The compact reading format must preserve the frozen evaluation contract."""
from pathlib import Path
import json,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from rubric_format import compact_rubric,expand_rubric,dumps_readable

class RubricFormatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.original=json.loads((ROOT/'rubrics/composition_rubric.json').read_text())
    def test_serialized_round_trip_preserves_entire_contract(self):
        compact=compact_rubric(self.original)
        self.assertEqual(expand_rubric(json.loads(dumps_readable(compact))),self.original)
    def test_explicit_evidence_override_is_not_lost(self):
        original=json.loads(json.dumps(self.original))
        original['factors'][0]['scoring_guidance']['low']['checks'][1]['required_evidence']=['custom evidence']
        self.assertEqual(expand_rubric(compact_rubric(original)),original)
    def test_invalid_storage_format_is_rejected(self):
        compact=compact_rubric(self.original);compact['_storage']['format']='unknown'
        with self.assertRaises(ValueError):expand_rubric(compact)
    def test_transform_does_not_mutate_canonical_input(self):
        before=json.dumps(self.original,sort_keys=True)
        expand_rubric(compact_rubric(self.original))
        self.assertEqual(before,json.dumps(self.original,sort_keys=True))

if __name__=='__main__':unittest.main()
