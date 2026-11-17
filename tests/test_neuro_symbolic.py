"""
Offline tests for grounded fact extraction, the evidence guards, the engine-guided clarification
loop and agreement triage. A scripted stub replaces the OpenAI client (no network, no API key).
"""
import json
import unittest
from types import SimpleNamespace

from bns_fol.ontology.signatures import PREDICATE_REGISTRY
from bns_scenarios.schema import LegalScenario, LegalVerdict, ScenarioCategory
from bns_verifier.fact_extractor import (FactExtractor, NeuroSymbolicPipeline, evidence_check, is_grounded,
                                         normalise_constant)
from bns_verifier.hybrid import analyse, triage

NARR = ("A deliberately fired a pistol at B with the intention of killing B. B died of the wound. "
        "B's age remains unknown.")


class _ScriptedClient:
    """Returns the scripted JSON payloads in order, one per chat.completions.create call."""
    def __init__(self, *payloads):
        self.payloads, self.calls = list(payloads), 0

        def create(**kw):
            content = json.dumps(self.payloads[min(self.calls, len(self.payloads) - 1)])
            self.calls += 1
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=create))


def scenario(narr=NARR, gt=LegalVerdict.SUPPORTED, actors=("A", "B")):
    return LegalScenario(scenario_id="T", title="t", category=ScenarioCategory.STRAIGHTFORWARD, narrative=narr,
                         actors=list(actors), facts=[], target_sections=[101], proposed_conclusion="Murder(A, B)",
                         ground_truth_verdict=gt, ground_truth_explanation="")


class TestGuards(unittest.TestCase):
    def test_grounding(self):
        self.assertTrue(is_grounded("fired a pistol at B", NARR))
        self.assertTrue(is_grounded("A fired a pistol at B with intention of killing B", NARR))  # light paraphrase
        self.assertFalse(is_grounded("B was over eighteen", NARR))

    def test_uncertainty_and_negation_guards(self):
        self.assertIsNotNone(evidence_check("~VictimAboveAge18(B)", "B's age remains unknown."))
        self.assertIsNotNone(evidence_check("~IntentionToCauseDeath(A, B)", "deprived of self-control"))
        self.assertIsNone(evidence_check("~WithoutPremeditation(A)", "A did not act without premeditation"))
        self.assertIsNone(evidence_check("CausesDeath(A, B)", "B died of the wound"))

    def test_constants_and_roles(self):
        self.assertEqual(normalise_constant("'religious community'"), "ReligiousCommunity")
        self.assertEqual(PREDICATE_REGISTRY["GraveAndSuddenProvocation"].arg_names, ["provoker", "accused"])
        self.assertTrue(all(len(s.arg_names) == s.arity for s in PREDICATE_REGISTRY.values()))


class TestGroundedExtraction(unittest.TestCase):
    def test_ungrounded_uncertain_and_role_labelled_facts(self):
        client = _ScriptedClient({"facts": [
            {"fact": "CausesDeath(accused: A, victim: B)", "evidence": "B died of the wound"},
            {"fact": "~VictimAboveAge18(B)", "evidence": "B's age remains unknown"},
            {"fact": "VictimConsentsToRiskOfDeath(B)", "evidence": "B agreed to the risk"},
            {"fact": "Murder(A, B)", "evidence": "deliberately fired a pistol at B"},
        ]})
        res = FactExtractor(client=client).extract(NARR, ["A", "B"], mode="grounded")
        self.assertIn("CausesDeath(A, B)", res.accepted)
        self.assertIn("Person(A)", res.accepted)
        self.assertNotIn("~VictimAboveAge18(B)", res.accepted)
        self.assertEqual(len(res.rejected), 3)


class TestClarificationLoop(unittest.TestCase):
    def test_engine_guided_question_resolves_missing_intent(self):
        client = _ScriptedClient(
            {"facts": [{"fact": "CausesDeath(A, B)", "evidence": "B died of the wound"}]},
            {"answers": [{"atom": "IntentionToCauseDeath(A, B)", "status": "TRUE",
                          "evidence": "with the intention of killing B"},
                         {"atom": "ImminentlyDangerousAct(A)", "status": "UNKNOWN", "evidence": ""}]},
        )
        pipe = NeuroSymbolicPipeline(FactExtractor(client=client))
        grounded = pipe.run(scenario(), mode="grounded")
        self.assertEqual(grounded["trace"].computed_verdict, LegalVerdict.INSUFFICIENT_INFORMATION)
        client.calls = 0
        out = pipe.run(scenario(), mode="loop")
        self.assertEqual(out["trace"].computed_verdict, LegalVerdict.SUPPORTED)
        self.assertEqual(out["llm_calls"], 2)
        self.assertIn("IntentionToCauseDeath(A, B)", out["clarification_rounds"][0]["questions"])
        self.assertEqual(out["evidence"]["IntentionToCauseDeath(A, B)"], "with the intention of killing B")

    def test_clarification_cannot_flip_known_facts(self):
        client = _ScriptedClient(
            {"facts": [{"fact": "CausesDeath(A, B)", "evidence": "B died of the wound"}]},
            {"answers": [{"atom": "CausesDeath(A, B)", "status": "FALSE", "evidence": "B died of the wound, not"}]},
        )
        out = NeuroSymbolicPipeline(FactExtractor(client=client)).run(scenario(), mode="loop")
        self.assertNotIn("~CausesDeath(A, B)", out["facts"])


class TestTriage(unittest.TestCase):
    def test_agreement_triage(self):
        self.assertEqual(triage("SUPPORTED", "SUPPORTED"), "AUTO_ACCEPT")
        self.assertEqual(triage("SUPPORTED", "MITIGATED_DEFENCE_APPLIED"), "HUMAN_REVIEW")
        ext = {"model": "m", "modes": {"loop": {"records": [
            {"scenario_id": "S1", "ground_truth": "SUPPORTED", "verdict_from_extracted_facts": "SUPPORTED", "end_to_end_correct": True},
            {"scenario_id": "S2", "ground_truth": "CONFLICTING", "verdict_from_extracted_facts": "SUPPORTED", "end_to_end_correct": False},
        ]}}}
        cmp = {"comparison_records": [{"scenario_id": "S1", "llm_verdict": "SUPPORTED"},
                                      {"scenario_id": "S2", "llm_verdict": "CONTRADICTED"}]}
        r = analyse(ext, cmp)
        self.assertEqual((r["auto_accepted"], r["auto_correct"], r["unsafe_routed_to_review"]), (1, 1, 1))
        self.assertEqual(r["human_review"], ["S2"])


if __name__ == "__main__":
    unittest.main()
