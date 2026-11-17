"""
Scenario Fact Valuation Model under Open-World Assumption (OWA).
"""
import re
from typing import Dict, List, Optional, Tuple
from bns_fol.semantics.truth_values import TruthValue

_ATOM_RE = re.compile(r"^([A-Za-z0-9_]+)\((.*)\)$")


def parse_literal(literal_str: str) -> Tuple[bool, str, List[str]]:
    """
    Splits a literal such as '~CausesDeath(A,  B)' into (is_negated, predicate, [args]).
    Atoms without an argument list are returned with an empty argument list.
    """
    clean = literal_str.strip()
    is_negated = clean.startswith("~") or clean.startswith("¬")
    atom = clean.lstrip("~¬").strip()
    m = _ATOM_RE.match(atom)
    if not m:
        return is_negated, atom, []
    args = [a.strip() for a in m.group(2).split(",") if a.strip()]
    return is_negated, m.group(1), args


def format_atom(predicate: str, args: List[str]) -> str:
    """Canonical atom string: 'Pred(a, b)' with exactly one space after each comma."""
    return f"{predicate}({', '.join(args)})" if args else predicate


def canonical_atom(atom_str: str) -> str:
    """Normalises spacing so 'CausesDeath(A,B)' and 'CausesDeath( A , B )' are the same atom."""
    _, pred, args = parse_literal(atom_str)
    return format_atom(pred, args)


class ScenarioFactModel:
    """
    Stores ground facts for a specific legal scenario.
    Undeclared facts evaluate strictly to UNKNOWN (Open-World Assumption).
    """
    def __init__(self, name: str = "Scenario"):
        self.name = name
        self._facts: Dict[str, TruthValue] = {}
        self._provenance: Dict[str, str] = {}

    def add_fact(self, literal_str: str, value: TruthValue = TruthValue.TRUE, source: str = "Stated in Scenario"):
        """
        Registers a ground literal (e.g. 'CausesDeath(A, B)' or '~ProvocationVoluntarilySought(A)').
        A negated literal stored as TRUE means its atom is FALSE.
        """
        is_negated, pred, args = parse_literal(literal_str)
        atom = format_atom(pred, args)
        self._facts[atom] = ~value if is_negated else value
        self._provenance[atom] = source

    def ground(self, literal_str: str, variable_binding: Optional[Dict[str, str]] = None) -> Tuple[bool, str]:
        """Returns (is_negated, ground_atom) after substituting bound variables."""
        binding = variable_binding or {}
        is_negated, pred, args = parse_literal(literal_str)
        return is_negated, format_atom(pred, [binding.get(a, a) for a in args])

    def evaluate_literal(self, literal_str: str, variable_binding: Optional[Dict[str, str]] = None) -> TruthValue:
        """
        Evaluates a literal under the scenario fact base and variable binding.
        """
        is_negated, ground_atom = self.ground(literal_str, variable_binding)
        atom_val = self._facts.get(ground_atom, TruthValue.UNKNOWN)
        return ~atom_val if is_negated else atom_val

    def get_ground_atom(self, literal_str: str, variable_binding: Optional[Dict[str, str]] = None) -> str:
        return self.ground(literal_str, variable_binding)[1]

    def facts_for(self, predicate: str) -> List[Tuple[List[str], TruthValue]]:
        """All known (non-UNKNOWN) ground atoms of a predicate, as (args, value) pairs."""
        out = []
        for atom, val in self._facts.items():
            _, pred, args = parse_literal(atom)
            if pred == predicate:
                out.append((args, val))
        return out

    def known_atoms(self) -> Dict[str, TruthValue]:
        return dict(self._facts)

    def provenance(self, atom_str: str) -> Optional[str]:
        return self._provenance.get(canonical_atom(atom_str))
