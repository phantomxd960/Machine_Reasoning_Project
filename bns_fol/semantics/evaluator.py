"""
Open-World Legal Reasoning and Verification Evaluator.
Evaluates statutory rules under 3-valued semantics and produces auditable explanations.
"""
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field
from bns_fol.semantics.truth_values import TruthValue
from bns_fol.semantics.model import ScenarioFactModel
from bns_fol.rules.schema import StatutoryRule

class RuleEvaluationResult(BaseModel):
    rule_id: str
    rule_name: str
    rule_type: str
    variable_binding: Dict[str, str]
    overall_value: TruthValue
    satisfied_premises: List[str]
    contradicted_premises: List[str]
    missing_premises: List[str]
    ground_conclusion: str
    is_concluded: bool

class OffenceVerificationResult(BaseModel):
    section_number: int
    offence_name: str
    accused: str
    victim: Optional[str] = None
    status: str = Field(description="SUPPORTED, CONTRADICTED, INSUFFICIENT_INFORMATION, MITIGATED_DEFENCE_APPLIED")
    primary_rule_applied: Optional[str] = None
    exceptions_applied: List[str] = Field(default_factory=list)
    exceptions_open: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    explanation: str

class OpenWorldLegalEvaluator:
    @staticmethod
    def evaluate_rule(
        rule: StatutoryRule,
        model: ScenarioFactModel,
        binding: Dict[str, str]
    ) -> RuleEvaluationResult:
        satisfied = []
        contradicted = []
        missing = []
        overall = TruthValue.TRUE

        for p in rule.premises:
            val = model.evaluate_literal(p, binding)
            ground_str = model.get_ground_atom(p, binding)
            display_lit = f"~{ground_str}" if (p.startswith("~") or p.startswith("¬")) else ground_str

            if val == TruthValue.TRUE:
                satisfied.append(display_lit)
            elif val == TruthValue.FALSE:
                contradicted.append(display_lit)
            else:
                missing.append(display_lit)

            overall = overall & val

        ground_conc = model.get_ground_atom(rule.conclusion, binding)
        is_conc = (overall == TruthValue.TRUE)

        return RuleEvaluationResult(
            rule_id=rule.rule_id,
            rule_name=rule.rule_name,
            rule_type=rule.rule_type,
            variable_binding=binding,
            overall_value=overall,
            satisfied_premises=satisfied,
            contradicted_premises=contradicted,
            missing_premises=missing,
            ground_conclusion=ground_conc,
            is_concluded=is_conc
        )

    @classmethod
    def verify_section_101_murder(
        cls,
        model: ScenarioFactModel,
        rules: List[StatutoryRule],
        accused: str = "A",
        victim: str = "B"
    ) -> OffenceVerificationResult:
        binding = {"x": accused, "y": victim}

        # 1. Evaluate all prima facie branches (Clauses a, b, c, d)
        prima_facie_rules = [r for r in rules if r.section_number == 101 and r.rule_type == "OFFENCE_ELEMENT"]
        prima_facie_satisfied = []
        all_missing_pf = []

        for r in prima_facie_rules:
            res = cls.evaluate_rule(r, model, binding)
            if res.overall_value == TruthValue.TRUE:
                prima_facie_satisfied.append(res)
            elif res.overall_value == TruthValue.UNKNOWN:
                all_missing_pf.extend(res.missing_premises)

        # If no prima facie branch is satisfied:
        if not prima_facie_satisfied:
            # Check if any missing
            if all_missing_pf:
                return OffenceVerificationResult(
                    section_number=101,
                    offence_name="Murder",
                    accused=accused,
                    victim=victim,
                    status="INSUFFICIENT_INFORMATION",
                    missing_information=list(set(all_missing_pf)),
                    explanation=f"Cannot establish prima facie murder: missing factual evidence for statutory elements ({', '.join(set(all_missing_pf))})."
                )
            else:
                return OffenceVerificationResult(
                    section_number=101,
                    offence_name="Murder",
                    accused=accused,
                    victim=victim,
                    status="CONTRADICTED",
                    explanation="Culpable homicide / murder actus reus or mens rea is negated by facts."
                )

        selected_pf = prima_facie_satisfied[0]

        # 2. Evaluate all 5 statutory exceptions
        exception_rules = [r for r in rules if r.section_number == 101 and r.rule_type == "EXCEPTION_DEFENCE"]
        exceptions_applied = []
        exceptions_open = []

        raised_unresolved = []
        raised_missing = []
        for r in exception_rules:
            res = cls.evaluate_rule(r, model, binding)
            if res.overall_value == TruthValue.TRUE:
                exceptions_applied.append(r.rule_name)
            elif res.overall_value == TruthValue.UNKNOWN:
                exceptions_open.append(r.rule_name)
                triggers = r.trigger_premises or [r.premises[0]]
                if all(model.evaluate_literal(t, binding) == TruthValue.TRUE for t in triggers):
                    # The defence has been raised but cannot be resolved either way.
                    raised_unresolved.append(r.rule_name)
                    raised_missing.extend(res.missing_premises)

        # If an exception applies, offence is mitigated!
        if exceptions_applied:
            return OffenceVerificationResult(
                section_number=101,
                offence_name="Murder",
                accused=accused,
                victim=victim,
                status="MITIGATED_DEFENCE_APPLIED",
                primary_rule_applied=selected_pf.rule_id,
                exceptions_applied=exceptions_applied,
                explanation=(
                    f"Prima facie murder established under {selected_pf.rule_name}, "
                    f"BUT statutory defence applied: {', '.join(exceptions_applied)}. "
                    f"Offence is mitigated to Culpable Homicide Not Amounting to Murder."
                )
            )

        # A raised defence whose conditions or provisos are UNKNOWN leaves ¬ExceptedFromMurder UNKNOWN.
        if raised_unresolved:
            return OffenceVerificationResult(
                section_number=101,
                offence_name="Murder",
                accused=accused,
                victim=victim,
                status="INSUFFICIENT_INFORMATION",
                primary_rule_applied=selected_pf.rule_id,
                exceptions_open=raised_unresolved,
                missing_information=list(dict.fromkeys(raised_missing)),
                explanation=(
                    f"Prima facie murder established under {selected_pf.rule_name}, but raised defence(s) "
                    f"{', '.join(raised_unresolved)} cannot be resolved: missing {', '.join(dict.fromkeys(raised_missing))}."
                )
            )

        # If no exception applies:
        return OffenceVerificationResult(
            section_number=101,
            offence_name="Murder",
            accused=accused,
            victim=victim,
            status="SUPPORTED",
            primary_rule_applied=selected_pf.rule_id,
            exceptions_applied=[],
            exceptions_open=exceptions_open,
            explanation=(
                f"Murder fully supported under Section 101 ({selected_pf.rule_name}). "
                f"Satisfied premises: {', '.join(selected_pf.satisfied_premises)}. "
                f"No statutory exceptions apply."
            )
        )
