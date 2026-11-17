"""
Tests for the generic, rule-driven verification engine and the fixes to the
limitations listed in the project guide (Chapter 13).
"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from bns_fol.rules.generator import BNSFOLGenerator
from bns_fol.rules.pilot_rules import get_pilot_rules
from bns_fol.semantics.model import ScenarioFactModel
from bns_fol.semantics.truth_values import TruthValue
from bns_kb.extractors.rule_based_parser import RuleBasedBNSParser
from bns_kb.pipeline import BNSKnowledgeBasePipeline
from bns_scenarios.benchmark_suite import get_benchmark_scenarios
from bns_scenarios.schema import LegalScenario, LegalVerdict, ScenarioCategory
from bns_verifier.engine import LegalVerificationEngine
from bns_verifier.fact_extractor import FactExtractor, compare_facts, validate_facts
from bns_verifier.llm_comparator import LLMComparator


def make(facts, conclusion="Murder(A, B)", expected=LegalVerdict.SUPPORTED, punishment=None):
    return LegalScenario(
        scenario_id="TEST", title="test", category=ScenarioCategory.STRAIGHTFORWARD, narrative="",
        actors=["A", "B"], facts=facts, target_sections=[101], proposed_conclusion=conclusion,
        ground_truth_verdict=expected, ground_truth_explanation="", expected_punishment=punishment,
    )


PF = ["CausesDeath(A, B)", "IntentionToCauseDeath(A, B)"]


class TestGenericEngine(unittest.TestCase):
    def setUp(self):
        self.engine = LegalVerificationEngine()

    def test_exception_3_is_evaluated(self):
        t = self.engine.verify_scenario(make(PF + ["PublicServantAdvancingJustice(A)", "WithoutPremeditation(A)"]))
        self.assertEqual(t.computed_verdict, LegalVerdict.MITIGATED_DEFENCE_APPLIED)
        self.assertIn("RULE-BNS-101-EXC-3", t.applicable_rules)
        self.assertIn("RULE-BNS-101-MITIGATED", t.applicable_rules)

    def test_raised_defence_with_unknown_provisos_is_insufficient(self):
        t = self.engine.verify_scenario(make(PF + ["GraveAndSuddenProvocation(B, A)", "DeprivedOfSelfControl(A)"]))
        self.assertEqual(t.computed_verdict, LegalVerdict.INSUFFICIENT_INFORMATION)
        self.assertEqual(t.unresolved_exceptions, ["Exception 1: Grave and Sudden Provocation"])
        self.assertIn("~ProvocationVoluntarilySought(A)", t.missing_facts)

    def test_consent_with_unknown_age_is_insufficient_for_murder(self):
        t = self.engine.verify_scenario(make(PF + ["VictimConsentsToRiskOfDeath(B)"]))
        self.assertEqual(t.computed_verdict, LegalVerdict.INSUFFICIENT_INFORMATION)
        self.assertIn("VictimAboveAge18(B)", t.missing_facts)

    def test_failed_defence_does_not_block_murder(self):
        # Exception 2 raised but premeditation proven -> defence fails -> murder stands
        t = self.engine.verify_scenario(make(PF + ["ExceedsPrivateDefenceInGoodFaith(A)", "~WithoutPremeditation(A)"]))
        self.assertEqual(t.computed_verdict, LegalVerdict.SUPPORTED)

    def test_out_of_scope_conclusion(self):
        t = self.engine.verify_scenario(make(PF, conclusion="Theft(A, B)"))
        self.assertEqual(t.computed_verdict, LegalVerdict.OUT_OF_SCOPE)

    def test_aggravated_sanctions_are_derived(self):
        s = {x.scenario_id: x for x in get_benchmark_scenarios()}
        t17 = self.engine.verify_scenario(s["SCEN-BNS-017"])
        self.assertIn("LiableToPunishment(A, ImprisonmentUpTo7YearsAndFine)", t17.applicable_sanctions)
        self.assertIn("RULE-BNS-318-SS-4", t17.applicable_rules)
        t18 = self.engine.verify_scenario(s["SCEN-BNS-018"])
        self.assertIn("RULE-BNS-103-SS-2", t18.applicable_rules)
        self.assertTrue(t18.sanction_matches_expected)

    def test_mob_lynching_rule_requires_murder(self):
        rule = next(r for r in get_pilot_rules() if r.rule_id == "RULE-BNS-103-SS-2")
        self.assertIn("Murder(x, y)", rule.premises)

    def test_all_expected_punishments_derived(self):
        for sc in get_benchmark_scenarios():
            t = self.engine.verify_scenario(sc)
            if t.sanction_matches_expected is not None:
                self.assertTrue(t.sanction_matches_expected, sc.scenario_id)

    def test_spacing_insensitive_and_ontology_warnings(self):
        t = self.engine.verify_scenario(make(["CausesDeath(A,B)", "IntentionToCauseDeath( A , B )", "CausesDeth(A, B)", "Murder(A)"]))
        self.assertEqual(t.computed_verdict, LegalVerdict.SUPPORTED)
        self.assertEqual(len(t.fact_warnings), 2)

    def test_schematic_rules_are_not_executed(self):
        all_rules = BNSFOLGenerator().generate_all_rules()
        engine = LegalVerificationEngine(all_rules)
        self.assertEqual(len(engine.rules), 24)
        self.assertGreater(engine.ignored_schematic_rules, 1000)
        self.assertTrue(all(r.formalization_level == "GOLD" for r in get_pilot_rules()))

    def test_civil_breach_explanation_comes_from_rule_data(self):
        s20 = next(s for s in get_benchmark_scenarios() if s.scenario_id == "SCEN-BNS-020")
        t = self.engine.verify_scenario(s20)
        self.assertEqual(t.computed_verdict, LegalVerdict.CONTRADICTED)
        self.assertIn("Illustration (g)", t.final_legal_explanation)


class TestFactModel(unittest.TestCase):
    def test_canonical_atoms(self):
        m = ScenarioFactModel()
        m.add_fact("CausesDeath( A ,B )")
        self.assertEqual(m.evaluate_literal("CausesDeath(x, y)", {"x": "A", "y": "B"}), TruthValue.TRUE)
        m.add_fact("~Deceives(A,B)")
        self.assertEqual(m.evaluate_literal("Deceives(A, B)"), TruthValue.FALSE)


class TestParserRomanNumerals(unittest.TestCase):
    def setUp(self):
        self.parser = RuleBasedBNSParser()

    def _types(self, text):
        comps, _ = self.parser.parse(999, "Test", text)
        return [(c.statutory_label, c.component_type.value) for c in comps]

    def test_roman_list_under_clause(self):
        t = self._types("Whoever—\n(a) does an act likely to cause—\n(i) death; or\n(ii) injury; or\n(v) loss,\nshall be punished.")
        self.assertIn(("(i)", "SUBCLAUSE"), t)

    def test_letter_i_after_h_stays_clause(self):
        letters = "abcdefghi"
        text = "Whoever—\n" + "\n".join(f"({c}) item {c};" for c in letters)
        self.assertIn(("(i)", "CLAUSE"), self._types(text))

    def test_roman_list_at_top_level(self):
        t = self._types("(1) A man committing any of the following acts:\n(i) one; or\n(ii) two; or\n(iii) three.")
        self.assertIn(("(i)", "SUBCLAUSE"), t)


class TestCheckpointReuse(unittest.TestCase):
    def test_second_run_reuses_unchanged_sections(self):
        d = tempfile.mkdtemp()
        try:
            first = BNSKnowledgeBasePipeline(output_dir=Path(d), use_checkpoint=True).run(pilot_only=True)
            self.assertEqual(first["sections_extracted"], 3)
            second = BNSKnowledgeBasePipeline(output_dir=Path(d), use_checkpoint=True).run(pilot_only=True)
            self.assertEqual(second["sections_reused_from_checkpoint"], 3)
            self.assertEqual(second["total_components"], first["total_components"])
        finally:
            shutil.rmtree(d, ignore_errors=True)


class _StubClient:
    def __init__(self, facts):
        content = json.dumps({"facts": facts})
        reply = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: reply))


class TestFactExtraction(unittest.TestCase):
    def test_validation_rejects_bad_proposals(self):
        ok, bad = validate_facts(
            ["CausesDeath(A,B)", "Murder(A, B)", "CausesDeath(A)", "Teleports(A)", "CausesDeath(A, Q)", "~ProvocationVoluntarilySought(A)"],
            actors=["A", "B"])
        self.assertEqual(ok, ["CausesDeath(A, B)", "~ProvocationVoluntarilySought(A)"])
        self.assertEqual(len(bad), 4)

    def test_extraction_then_verification_loop(self):
        ex = FactExtractor(client=_StubClient(["CausesDeath(A, B)", "Murder(A, B)"]))
        res = ex.extract("A struck B, who died.", ["A", "B"])
        self.assertEqual(res.accepted, ["CausesDeath(A, B)"])
        t = LegalVerificationEngine().verify_scenario(make(res.accepted))
        self.assertEqual(t.computed_verdict, LegalVerdict.INSUFFICIENT_INFORMATION)
        self.assertEqual(compare_facts(res.accepted, PF)["recall"], 0.5)


class TestLLMComparatorSource(unittest.TestCase):
    def test_offline_source_is_labelled_and_counted(self):
        import os
        if os.getenv("OPENAI_API_KEY"):
            self.skipTest("live key present")
        s = LLMComparator().run_comparison(export=False)
        self.assertEqual(s["llm_response_source"], "offline_recorded")
        self.assertEqual(s["llm_correct"], round(s["llm_accuracy_pct"] * s["total_scenarios"] / 100))


if __name__ == "__main__":
    unittest.main()
