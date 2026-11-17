import unittest
import tempfile
import shutil
from pathlib import Path
from bns_fol.rules.generator import BNSFOLGenerator
from bns_fol.rules.registry import RuleRegistry
from bns_fol.config import PILOT_SECTIONS

class TestFOLFullConversion(unittest.TestCase):
    def setUp(self):
        self.generator = BNSFOLGenerator()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_full_rule_generation(self):
        rules = self.generator.generate_all_rules()
        self.assertGreater(len(rules), 1000)
        
        # Verify pilot rules are present
        pilot_r_ids = {r.rule_id for r in rules if r.section_number in PILOT_SECTIONS}
        self.assertIn("RULE-BNS-101-CL-A", pilot_r_ids)
        self.assertIn("RULE-BNS-101-EXC-1", pilot_r_ids)
        self.assertIn("RULE-BNS-103-SS-1", pilot_r_ids)
        self.assertIn("RULE-BNS-318-EXPL", pilot_r_ids)

        # Verify export to test directory
        reg = RuleRegistry(rules)
        out_jsonl = Path(self.test_dir) / "test_rules.jsonl"
        out_csv = Path(self.test_dir) / "test_rules.csv"
        out_ont = Path(self.test_dir) / "test_ontology.json"

        summary = reg.export(jsonl_path=out_jsonl, csv_path=out_csv, ontology_json_path=out_ont)
        self.assertEqual(summary["total_rules"], len(rules))
        self.assertTrue(out_jsonl.exists())
        self.assertTrue(out_csv.exists())
        self.assertTrue(out_ont.exists())

if __name__ == "__main__":
    unittest.main()
