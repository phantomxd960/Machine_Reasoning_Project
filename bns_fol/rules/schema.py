"""
Schema for Formal Statutory First-Order Logic Rules.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class StatutoryRule(BaseModel):
    rule_id: str = Field(description="Unique deterministic identifier, e.g. RULE-BNS-101-CL-A")
    section_number: int = Field(description="BNS 2023 section number")
    source_component_id: str = Field(description="Knowledge base source component ID")
    rule_name: str = Field(description="Descriptive name of the legal rule")
    rule_type: str = Field(description="OFFENCE_ELEMENT, EXCEPTION_DEFENCE, EXCEPTION_OVERRIDE, DEFINITIONAL_EXPANSION, PUNISHMENT_MAPPING")
    variables: List[str] = Field(description="Quantified variable names, e.g. ['x', 'y']")
    premises: List[str] = Field(description="List of premise literals (e.g. ['CausesDeath(x, y)', 'IntentionToCauseDeath(x, y)'])")
    conclusion: str = Field(description="Conclusion literal (e.g. 'PrimaFacieMurder(x, y)')")
    formula_unicode: str = Field(description="Unicode mathematical representation: ∀x, y. P1 ∧ P2 → C")
    formula_latex: str = Field(description="LaTeX representation for paper and reports")
    formula_ascii: str = Field(description="Machine-parsable ASCII representation: ALL x, y. (P1 & P2 -> C)")
    description: str = Field(description="Human-readable legal explanation of the formalization")
    formalization_level: str = Field(
        default="SCHEMATIC",
        description=(
            "GOLD = hand-formalised over typed ontology predicates and executable by the verification engine; "
            "SCHEMATIC = auto-generated skeleton with placeholder predicates (traceable to the KB, not executed)."
        )
    )
    trigger_premises: List[str] = Field(
        default_factory=list,
        description=(
            "EXCEPTION_DEFENCE rules only: the premise(s) whose truth means the defence has been raised. "
            "Defaults to the first premise when empty."
        )
    )
    premise_notes: Dict[str, str] = Field(
        default_factory=dict,
        description="Optional legal note per premise, shown in the explanation when that premise is contradicted."
    )
