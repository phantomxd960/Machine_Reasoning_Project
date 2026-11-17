"""
First-Order Logic (FOL) Formalization Package for Bharatiya Nyaya Sanhita (BNS) 2023.
"""
from bns_fol.rules.generator import BNSFOLGenerator
from bns_fol.rules.registry import RuleRegistry
from bns_fol.rules.pilot_rules import get_pilot_rules
from bns_fol.semantics.truth_values import TruthValue
from bns_fol.semantics.model import ScenarioFactModel
from bns_fol.semantics.evaluator import OpenWorldLegalEvaluator

__version__ = "1.0.0"
__all__ = [
    "BNSFOLGenerator",
    "RuleRegistry",
    "get_pilot_rules",
    "TruthValue",
    "ScenarioFactModel",
    "OpenWorldLegalEvaluator",
]
