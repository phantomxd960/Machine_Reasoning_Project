"""
Audit Trace and Verification Step Schemas for Transparent Legal Reasoning.
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from bns_scenarios.schema import LegalVerdict

class ReasoningStep(BaseModel):
    step_number: int
    rule_id: str
    rule_name: str
    rule_type: str
    premises_satisfied: List[str]
    premises_missing: List[str]
    premises_contradicted: List[str]
    deduced_fact: Optional[str] = None
    step_explanation: str

class VerificationAuditTrace(BaseModel):
    scenario_id: str
    scenario_title: str
    target_sections: List[int]
    proposed_conclusion: str
    computed_verdict: LegalVerdict
    ground_truth_verdict: LegalVerdict
    verdict_matches_ground_truth: bool
    applicable_rules: List[str]
    reasoning_steps: List[ReasoningStep]
    applied_exceptions: List[str] = Field(default_factory=list)
    defeated_exceptions: List[str] = Field(default_factory=list)
    missing_facts: List[str] = Field(default_factory=list)
    conflicting_facts: List[str] = Field(default_factory=list)
    unresolved_exceptions: List[str] = Field(
        default_factory=list,
        description="Defences that were raised but whose conditions or provisos are still UNKNOWN"
    )
    applicable_sanctions: List[str] = Field(
        default_factory=list,
        description="LiableToPunishment(...) conclusions derived from GOLD punishment rules (base and aggravated)"
    )
    sanction_matches_expected: Optional[bool] = Field(
        default=None,
        description="True/False when the scenario states an expected punishment; None otherwise"
    )
    fact_warnings: List[str] = Field(
        default_factory=list,
        description="Facts whose predicate is not in the ontology or has the wrong arity"
    )
    final_legal_explanation: str
