"""
Formal Legal Entity and Argument Types.
"""
from enum import Enum

class LegalType(str, Enum):
    PERSON = "Person"
    ACT = "Act"
    PROPERTY = "Property"
    STATE_OF_MIND = "StateOfMind"
    BODILY_INJURY = "BodilyInjury"
    PENALTY = "Penalty"
    GROUND = "DiscriminatoryGround"
    ANY = "Any"
