import unittest
from bns_fol.rules.pilot_rules import get_pilot_rules
from bns_fol.semantics.truth_values import TruthValue
from bns_fol.semantics.model import ScenarioFactModel
from bns_fol.semantics.evaluator import OpenWorldLegalEvaluator

class TestFOLPilotReasoning(unittest.TestCase):
    def setUp(self):
        self.rules = get_pilot_rules()

    def test_case_1_standard_murder_supported(self):
        """
        Scenario: A shoots B with intention to cause death. B dies.
        Result: Murder(A, B) is SUPPORTED. No exceptions apply.
        """
        model = ScenarioFactModel("Standard Murder Case")
        model.add_fact("CausesDeath(A, B)")
        model.add_fact("IntentionToCauseDeath(A, B)")

        result = OpenWorldLegalEvaluator.verify_section_101_murder(model, self.rules, accused="A", victim="B")
        self.assertEqual(result.status, "SUPPORTED")
        self.assertEqual(result.primary_rule_applied, "RULE-BNS-101-CL-A")
        self.assertEqual(len(result.exceptions_applied), 0)

    def test_case_2_murder_mitigated_by_exception_1(self):
        """
        Scenario: Y gives grave and sudden provocation to X. X loses self-control and kills Y.
        The provocation was not voluntarily sought, not from a public servant, not in private defence.
        Result: Murder is defeated; mitigated to Culpable Homicide Not Amounting to Murder!
        """
        model = ScenarioFactModel("Grave and Sudden Provocation Case")
        model.add_fact("CausesDeath(X, Y)")
        model.add_fact("IntentionToCauseDeath(X, Y)")
        model.add_fact("GraveAndSuddenProvocation(Y, X)")
        model.add_fact("DeprivedOfSelfControl(X)")
        # Provisos absent:
        model.add_fact("~ProvocationVoluntarilySought(X)")
        model.add_fact("~ProvocationByLawfulPublicServant(Y)")
        model.add_fact("~ProvocationByLawfulPrivateDefence(Y)")

        result = OpenWorldLegalEvaluator.verify_section_101_murder(model, self.rules, accused="X", victim="Y")
        self.assertEqual(result.status, "MITIGATED_DEFENCE_APPLIED")
        self.assertIn("Exception 1: Grave and Sudden Provocation", result.exceptions_applied[0])
        self.assertIn("mitigated to Culpable Homicide", result.explanation)

    def test_case_3_exception_defeated_by_proviso(self):
        """
        Scenario: X wanted an excuse to kill Y, so X voluntarily provoked Y.
        When Y reacted, X killed Y claiming provocation.
        Result: Proviso (a) holds (ProvocationVoluntarilySought is True),
        so Exception 1 fails, and Murder stands SUPPORTED!
        """
        model = ScenarioFactModel("Provocation Voluntarily Provoked")
        model.add_fact("CausesDeath(X, Y)")
        model.add_fact("IntentionToCauseDeath(X, Y)")
        model.add_fact("GraveAndSuddenProvocation(Y, X)")
        model.add_fact("DeprivedOfSelfControl(X)")
        # Accused voluntarily sought provocation:
        model.add_fact("ProvocationVoluntarilySought(X)")

        result = OpenWorldLegalEvaluator.verify_section_101_murder(model, self.rules, accused="X", victim="Y")
        self.assertEqual(result.status, "SUPPORTED")
        self.assertEqual(len(result.exceptions_applied), 0)

    def test_case_4_insufficient_information_open_world(self):
        """
        Scenario: A struck B. B died. There is no information about whether A intended to kill B,
        nor what weapon was used.
        Result: Evaluator must return INSUFFICIENT_INFORMATION (never falsely assume False!).
        """
        model = ScenarioFactModel("Incomplete Facts Case")
        model.add_fact("CausesDeath(A, B)")
        # Notice: IntentionToCauseDeath is not provided (UNKNOWN)!

        result = OpenWorldLegalEvaluator.verify_section_101_murder(model, self.rules, accused="A", victim="B")
        self.assertEqual(result.status, "INSUFFICIENT_INFORMATION")
        self.assertTrue(len(result.missing_information) > 0)
        self.assertTrue(any("IntentionToCauseDeath" in m for m in result.missing_information))

    def test_case_5_cheating_definitional_expansion(self):
        """
        Scenario: A dishonestly conceals facts from B and thereby fraudulently induces B
        to deliver property.
        Result: Explanation rule expands concealment -> Deception, deriving Cheating!
        """
        model = ScenarioFactModel("Cheating by Concealment")
        model.add_fact("DishonestlyConcealsFact(A, B, DefectInCar)")
        model.add_fact("FraudulentlyOrDishonestlyInducesDelivery(A, B, Money)")

        # 1. Evaluate explanation rule
        expl_rule = [r for r in self.rules if r.rule_id == "RULE-BNS-318-EXPL"][0]
        res_expl = OpenWorldLegalEvaluator.evaluate_rule(expl_rule, model, {"x": "A", "y": "B", "f": "DefectInCar"})
        self.assertEqual(res_expl.overall_value, TruthValue.TRUE)
        self.assertTrue(res_expl.is_concluded)

        # Register the derived fact into model
        model.add_fact("Deceives(A, B)", source="Derived from RULE-BNS-318-EXPL")

        # 2. Evaluate cheating delivery rule
        cheat_rule = [r for r in self.rules if r.rule_id == "RULE-BNS-318-SS-1-DELIVERY"][0]
        res_cheat = OpenWorldLegalEvaluator.evaluate_rule(cheat_rule, model, {"x": "A", "y": "B", "p": "Money"})
        self.assertEqual(res_cheat.overall_value, TruthValue.TRUE)
        self.assertTrue(res_cheat.is_concluded)

    def test_case_6_punishment_mapping(self):
        """
        Scenario: A commits murder of B.
        Result: RULE-BNS-103-SS-1 maps Murder(A, B) -> LiableToPunishment(A, DeathOrImprisonmentForLifeAndFine).
        """
        model = ScenarioFactModel("Murder Penalty Case")
        model.add_fact("Murder(A, B)")

        punish_rule = [r for r in self.rules if r.rule_id == "RULE-BNS-103-SS-1"][0]
        res = OpenWorldLegalEvaluator.evaluate_rule(punish_rule, model, {"x": "A", "y": "B"})
        self.assertEqual(res.overall_value, TruthValue.TRUE)
        self.assertTrue(res.is_concluded)
        self.assertEqual(res.ground_conclusion, "LiableToPunishment(A, DeathOrImprisonmentForLifeAndFine)")

if __name__ == "__main__":
    unittest.main()
