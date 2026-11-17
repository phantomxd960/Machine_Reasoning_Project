"""
First-Order Logic Predicates, Atoms, and Literals.
"""
from dataclasses import dataclass
from typing import List, Tuple
from bns_fol.syntax.terms import Term

@dataclass(frozen=True)
class Atom:
    predicate: str
    args: Tuple[Term, ...]

    def __init__(self, predicate: str, *args: Term):
        object.__setattr__(self, "predicate", predicate)
        object.__setattr__(self, "args", tuple(args))

    def __str__(self) -> str:
        args_str = ", ".join(str(a) for a in self.args)
        return f"{self.predicate}({args_str})"

    def to_latex(self) -> str:
        args_str = ", ".join(a.to_latex() for a in self.args)
        return f"\\text{{{self.predicate}}}({args_str})"

@dataclass(frozen=True)
class Literal:
    atom: Atom
    is_negated: bool = False

    def __str__(self) -> str:
        if self.is_negated:
            return f"¬{self.atom}"
        return str(self.atom)

    def to_ascii(self) -> str:
        if self.is_negated:
            return f"~{self.atom}"
        return str(self.atom)

    def to_latex(self) -> str:
        if self.is_negated:
            return f"\\neg {self.atom.to_latex()}"
        return self.atom.to_latex()

    def negate(self) -> "Literal":
        return Literal(atom=self.atom, is_negated=not self.is_negated)
