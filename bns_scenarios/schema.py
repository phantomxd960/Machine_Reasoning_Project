"""
Schemas for Complex Legal Scenarios in Bharatiya Nyaya Sanhita (BNS) Reasoning.
"""
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class ScenarioCategory(str, Enum):
    STRAIGHTFORWARD = "STRAIGHTFORWARD"                         # Direct rule applicability
    STATUTORY_EXCEPTION = "STATUTORY_EXCEPTION"                 # Valid statutory exception mitigates offence
    PROVISO_OVERRIDE = "PROVISO_OVERRIDE"                       # Proviso defeats exception; offence stands
    MISSING_FACTS = "MISSING_FACTS"                             # Incomplete facts under Open-World Assumption
    CONTRADICTORY_FACTS = "CONTRADICTORY_FACTS"                 # Conflicting evidentiary premises
    MULTI_PROVISION = "MULTI_PROVISION"                         # Interplay between definitions, offences, penalties
    UNSUPPORTED_CONCLUSION = "UNSUPPORTED_CONCLUSION"           # False plausibility / civil dispute disguised as crime

class LegalVerdict(str, Enum):
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"
    MITIGATED_DEFENCE_APPLIED = "MITIGATED_DEFENCE_APPLIED"
    CONFLICTING = "CONFLICTING"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"          # No executable (GOLD) rule concludes the proposed predicate

class LegalScenario(BaseModel):
    scenario_id: str = Field(description="Unique identifier, e.g. SCEN-BNS-001")
    title: str = Field(description="Descriptive title of the legal scenario")
    category: ScenarioCategory = Field(description="Scenario complexity category")
    narrative: str = Field(description="Natural-language description of facts")
    actors: List[str] = Field(description="List of legal entities involved, e.g. ['A', 'B']")
    facts: List[str] = Field(description="Formally grounded FOL literals")
    target_sections: List[int] = Field(description="Relevant BNS statutory sections")
    proposed_conclusion: str = Field(description="Proposed legal charge/conclusion to verify")
    ground_truth_verdict: LegalVerdict = Field(description="Expected legal ground truth verdict")
    ground_truth_explanation: str = Field(description="Detailed legal reasoning justifying the verdict")
    expected_mitigated_offence: Optional[str] = Field(default=None, description="Mitigated offence if defence applies")
    expected_punishment: Optional[str] = Field(default=None, description="Prescribed statutory sanction if liable")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context or benchmark tags")
