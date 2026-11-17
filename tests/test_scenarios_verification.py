import unittest
from bns_scenarios.benchmark_suite import get_benchmark_scenarios
from bns_verifier.benchmark_runner import VerificationBenchmarkRunner
from bns_verifier.engine import LegalVerificationEngine
from bns_scenarios.schema import LegalVerdict

class TestScenariosVerification(unittest.TestCase):
    def setUp(self):
        self.runner = VerificationBenchmarkRunner()
        self.engine = LegalVerificationEngine()
        self.scenarios = get_benchmark_scenarios()
        self.scen_map = {s.scenario_id: s for s in self.scenarios}

    def test_full_benchmark_100_percent_alignment(self):
        """
        Verifies that the LegalVerificationEngine achieves 100% agreement with
        the legal ground truth across all 20 complex scenarios.
        """
        summary = self.runner.run_benchmark(self.scenarios, export_traces=False)
        self.assertEqual(summary["total_scenarios_evaluated"], 20)
        self.assertEqual(summary["ground_truth_matches"], 20)
        self.assertEqual(summary["verification_accuracy_pct"], 100.0)
        self.assertEqual(len(summary["failed_scenarios"]), 0)

    def test_straightforward_murder_scenarios(self):
        s1 = self.scen_map["SCEN-BNS-001"]
        trace = self.engine.verify_scenario(s1)
        self.assertEqual(trace.computed_verdict, LegalVerdict.SUPPORTED)
        self.assertTrue(trace.verdict_matches_ground_truth)
        self.assertIn("RULE-BNS-101-CL-A", trace.applicable_rules)

    def test_statutory_exception_mitigations(self):
        # Provocation exception
        s4 = self.scen_map["SCEN-BNS-004"]
        trace4 = self.engine.verify_scenario(s4)
        self.assertEqual(trace4.computed_verdict, LegalVerdict.MITIGATED_DEFENCE_APPLIED)
        self.assertIn("Exception 1: Grave and Sudden Provocation", trace4.applied_exceptions[0])

        # Private defence exception
        s5 = self.scen_map["SCEN-BNS-005"]
        trace5 = self.engine.verify_scenario(s5)
        self.assertEqual(trace5.computed_verdict, LegalVerdict.MITIGATED_DEFENCE_APPLIED)

    def test_proviso_overrides(self):
        # Provocation voluntarily sought
        s8 = self.scen_map["SCEN-BNS-008"]
        trace8 = self.engine.verify_scenario(s8)
        self.assertEqual(trace8.computed_verdict, LegalVerdict.SUPPORTED)
        self.assertTrue(any("Proviso a" in d for d in trace8.defeated_exceptions))

        # Lawful public servant
        s9 = self.scen_map["SCEN-BNS-009"]
        trace9 = self.engine.verify_scenario(s9)
        self.assertEqual(trace9.computed_verdict, LegalVerdict.SUPPORTED)
        self.assertTrue(any("Proviso b" in d for d in trace9.defeated_exceptions))

    def test_missing_facts_open_world(self):
        # Missing mens rea
        s12 = self.scen_map["SCEN-BNS-012"]
        trace12 = self.engine.verify_scenario(s12)
        self.assertEqual(trace12.computed_verdict, LegalVerdict.INSUFFICIENT_INFORMATION)
        self.assertTrue(len(trace12.missing_facts) > 0)

    def test_evidentiary_conflict(self):
        s15 = self.scen_map["SCEN-BNS-015"]
        trace15 = self.engine.verify_scenario(s15)
        self.assertEqual(trace15.computed_verdict, LegalVerdict.CONFLICTING)
        self.assertTrue(len(trace15.conflicting_facts) > 0)

    def test_civil_breach_vs_cheating(self):
        s20 = self.scen_map["SCEN-BNS-020"]
        trace20 = self.engine.verify_scenario(s20)
        self.assertEqual(trace20.computed_verdict, LegalVerdict.CONTRADICTED)
        self.assertIn("breach of contract", trace20.final_legal_explanation.lower())

if __name__ == "__main__":
    unittest.main()
