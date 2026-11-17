import unittest
import tempfile
import shutil
from pathlib import Path
from bns_kb.pipeline import BNSKnowledgeBasePipeline

class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.pipeline = BNSKnowledgeBasePipeline(
            output_dir=Path(self.test_dir),
            use_checkpoint=False
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_pilot_execution(self):
        summary = self.pipeline.run(pilot_only=True)
        self.assertEqual(summary["total_sections_processed"], 3)
        self.assertEqual(summary["syntactically_validated_sections"], 3)
        self.assertGreaterEqual(summary["mean_coverage_ratio_pct"], 99.0)
        self.assertGreaterEqual(summary["total_components"], 40)
        self.assertGreaterEqual(summary["total_relationships"], 40)

        # Check that component distribution contains diverse types
        dist = summary["component_distribution"]
        self.assertIn("MAIN_PROVISION", dist)
        self.assertIn("EXCEPTION", dist)
        self.assertIn("EXPLANATION", dist)
        self.assertIn("ILLUSTRATION", dist)

if __name__ == "__main__":
    unittest.main()
