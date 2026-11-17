"""
Three-Valued Logic (Kleene / Open-World Logic): TRUE, FALSE, UNKNOWN.
"""
from enum import Enum

class TruthValue(str, Enum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    UNKNOWN = "UNKNOWN"

    def __invert__(self) -> "TruthValue":
        if self == TruthValue.TRUE:
            return TruthValue.FALSE
        if self == TruthValue.FALSE:
            return TruthValue.TRUE
        return TruthValue.UNKNOWN

    def __and__(self, other: "TruthValue") -> "TruthValue":
        if self == TruthValue.FALSE or other == TruthValue.FALSE:
            return TruthValue.FALSE
        if self == TruthValue.TRUE and other == TruthValue.TRUE:
            return TruthValue.TRUE
        return TruthValue.UNKNOWN

    def __or__(self, other: "TruthValue") -> "TruthValue":
        if self == TruthValue.TRUE or other == TruthValue.TRUE:
            return TruthValue.TRUE
        if self == TruthValue.FALSE and other == TruthValue.FALSE:
            return TruthValue.FALSE
        return TruthValue.UNKNOWN
