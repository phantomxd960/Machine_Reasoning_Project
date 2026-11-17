"""
First-Order Logic Terms: Variables, Constants, and Functions.
"""
from dataclasses import dataclass
from typing import Any

class Term:
    pass

@dataclass(frozen=True)
class Variable(Term):
    name: str

    def __str__(self) -> str:
        return self.name

    def to_latex(self) -> str:
        return self.name

@dataclass(frozen=True)
class Constant(Term):
    name: str

    def __str__(self) -> str:
        return self.name

    def to_latex(self) -> str:
        return f"\\text{{{self.name}}}"
