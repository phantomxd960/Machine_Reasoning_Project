"""
First-Order Logic Formulas (Conjunction, Disjunction, Implication, Negation, ForAll).
"""
from dataclasses import dataclass
from typing import List, Tuple
from bns_fol.syntax.terms import Variable
from bns_fol.syntax.predicates import Literal

class Formula:
    pass

@dataclass(frozen=True)
class AndFormula(Formula):
    operands: Tuple[Literal, ...]

    def __init__(self, *operands: Literal):
        object.__setattr__(self, "operands", tuple(operands))

    def __str__(self) -> str:
        return " ∧ ".join(str(op) for op in self.operands)

    def to_ascii(self) -> str:
        return " & ".join(op.to_ascii() for op in self.operands)

    def to_latex(self) -> str:
        return " \\land ".join(op.to_latex() for op in self.operands)

@dataclass(frozen=True)
class OrFormula(Formula):
    operands: Tuple[Literal, ...]

    def __init__(self, *operands: Literal):
        object.__setattr__(self, "operands", tuple(operands))

    def __str__(self) -> str:
        return " ∨ ".join(str(op) for op in self.operands)

    def to_ascii(self) -> str:
        return " | ".join(op.to_ascii() for op in self.operands)

    def to_latex(self) -> str:
        return " \\lor ".join(op.to_latex() for op in self.operands)

@dataclass(frozen=True)
class ImpliesFormula(Formula):
    antecedent: Formula
    consequent: Formula

    def __str__(self) -> str:
        return f"{self.antecedent} → {self.consequent}"

    def to_ascii(self) -> str:
        return f"({self.antecedent.to_ascii()} -> {self.consequent.to_ascii()})"

    def to_latex(self) -> str:
        return f"{self.antecedent.to_latex()} \\to {self.consequent.to_latex()}"

@dataclass(frozen=True)
class ForAll(Formula):
    variables: Tuple[Variable, ...]
    formula: Formula

    def __init__(self, variables: List[Variable], formula: Formula):
        object.__setattr__(self, "variables", tuple(variables))
        object.__setattr__(self, "formula", formula)

    def __str__(self) -> str:
        vars_str = ", ".join(str(v) for v in self.variables)
        return f"∀{vars_str}. ({self.formula})"

    def to_ascii(self) -> str:
        vars_str = ", ".join(v.name for v in self.variables)
        return f"ALL {vars_str}. ({self.formula.to_ascii()})"

    def to_latex(self) -> str:
        vars_str = ", ".join(v.to_latex() for v in self.variables)
        return f"\\forall {vars_str} \\ \\left( {self.formula.to_latex()} \\right)"
