"""
Predicate Ontology: Signatures, Arity, and Statutory Semantics.
"""
from typing import Dict, List, Any
from pydantic import BaseModel, Field
from bns_fol.ontology.types import LegalType

class PredicateSignature(BaseModel):
    name: str = Field(description="Formal predicate identifier (e.g. CausesDeath)")
    arity: int = Field(description="Number of arguments")
    arg_types: List[LegalType] = Field(description="Types of arguments")
    category: str = Field(description="ACTUS_REUS, MENS_REA, EXCEPTION, PROVISO, PUNISHMENT, STATUS")
    description: str = Field(description="Formal legal meaning under BNS 2023")
    arg_names: List[str] = Field(default_factory=list, description="Role of each argument, e.g. ['provoker', 'accused']")

PREDICATE_REGISTRY: Dict[str, PredicateSignature] = {
    # General / Entity
    "Person": PredicateSignature(
        name="Person", arity=1, arg_types=[LegalType.PERSON],
        category="STATUS", description="Entity x is a legal person under BNS Sec 2(26)"
    ),
    "GroupOfPersons": PredicateSignature(
        name="GroupOfPersons", arity=1, arg_types=[LegalType.ANY],
        category="STATUS", description="Entity g is a group of persons"
    ),
    "MemberOfGroup": PredicateSignature(
        name="MemberOfGroup", arity=2, arg_types=[LegalType.PERSON, LegalType.ANY],
        category="STATUS", description="Person x is a member of group g"
    ),

    # Section 101: Murder & Culpable Homicide (Actus Reus & Mens Rea)
    "CausesDeath": PredicateSignature(
        name="CausesDeath", arity=2, arg_types=[LegalType.PERSON, LegalType.PERSON],
        category="ACTUS_REUS", description="Person x causes the death of person y"
    ),
    "IntentionToCauseDeath": PredicateSignature(
        name="IntentionToCauseDeath", arity=2, arg_types=[LegalType.PERSON, LegalType.PERSON],
        category="MENS_REA", description="Person x acts with intention of causing death of y (Sec 101 cl a)"
    ),
    "IntentionToCauseBodilyInjury": PredicateSignature(
        name="IntentionToCauseBodilyInjury", arity=2, arg_types=[LegalType.PERSON, LegalType.PERSON],
        category="MENS_REA", description="Person x acts with intention of causing bodily injury to y"
    ),
    "KnowsInjuryLikelyToCauseDeath": PredicateSignature(
        name="KnowsInjuryLikelyToCauseDeath", arity=2, arg_types=[LegalType.PERSON, LegalType.PERSON],
        category="MENS_REA", description="Offender knows injury is likely to cause death of person harmed (Sec 101 cl b)"
    ),
    "BodilyInjurySufficientInOrdinaryCourse": PredicateSignature(
        name="BodilyInjurySufficientInOrdinaryCourse", arity=2, arg_types=[LegalType.PERSON, LegalType.PERSON],
        category="ACTUS_REUS", description="Injury intended to be inflicted is sufficient in ordinary course of nature to cause death (Sec 101 cl c)"
    ),
    "ImminentlyDangerousAct": PredicateSignature(
        name="ImminentlyDangerousAct", arity=1, arg_types=[LegalType.PERSON],
        category="ACTUS_REUS", description="Person x commits an act that is so imminently dangerous that it must in all probability cause death (Sec 101 cl d)"
    ),
    "KnowledgeOfProbabilityOfDeath": PredicateSignature(
        name="KnowledgeOfProbabilityOfDeath", arity=1, arg_types=[LegalType.PERSON],
        category="MENS_REA", description="Person x knows act must in all probability cause death (Sec 101 cl d)"
    ),
    "WithoutLawfulExcuse": PredicateSignature(
        name="WithoutLawfulExcuse", arity=1, arg_types=[LegalType.PERSON],
        category="ACTUS_REUS", description="Person x acts without any lawful excuse for incurring the risk of death (Sec 101 cl d)"
    ),

    # Section 101: Exceptions & Defences
    "GraveAndSuddenProvocation": PredicateSignature(
        name="GraveAndSuddenProvocation", arity=2, arg_types=[LegalType.PERSON, LegalType.PERSON],
        category="EXCEPTION", description="Person y gives grave and sudden provocation to person x (Sec 101 Exc 1)"
    ),
    "DeprivedOfSelfControl": PredicateSignature(
        name="DeprivedOfSelfControl", arity=1, arg_types=[LegalType.PERSON],
        category="EXCEPTION", description="Offender x is deprived of the power of self-control by provocation (Sec 101 Exc 1)"
    ),
    "ProvocationVoluntarilySought": PredicateSignature(
        name="ProvocationVoluntarilySought", arity=1, arg_types=[LegalType.PERSON],
        category="PROVISO", description="Provocation was sought or voluntarily provoked by offender as an excuse (Sec 101 Exc 1 Prov a)"
    ),
    "ProvocationByLawfulPublicServant": PredicateSignature(
        name="ProvocationByLawfulPublicServant", arity=1, arg_types=[LegalType.PERSON],
        category="PROVISO", description="Provocation was given in obedience to law or by a public servant in lawful exercise of power (Sec 101 Exc 1 Prov b)"
    ),
    "ProvocationByLawfulPrivateDefence": PredicateSignature(
        name="ProvocationByLawfulPrivateDefence", arity=1, arg_types=[LegalType.PERSON],
        category="PROVISO", description="Provocation was given by anything done in lawful exercise of right of private defence (Sec 101 Exc 1 Prov c)"
    ),
    "ExceedsPrivateDefenceInGoodFaith": PredicateSignature(
        name="ExceedsPrivateDefenceInGoodFaith", arity=1, arg_types=[LegalType.PERSON],
        category="EXCEPTION", description="Offender x in good faith exercise of private defence exceeds lawful power (Sec 101 Exc 2)"
    ),
    "WithoutPremeditation": PredicateSignature(
        name="WithoutPremeditation", arity=1, arg_types=[LegalType.PERSON],
        category="EXCEPTION", description="Offender x acts without premeditation (Sec 101 Exc 2, 4)"
    ),
    "WithoutIntentionOfMoreHarmThanNecessary": PredicateSignature(
        name="WithoutIntentionOfMoreHarmThanNecessary", arity=1, arg_types=[LegalType.PERSON],
        category="EXCEPTION", description="Offender x has no intention of doing more harm than is necessary for defence (Sec 101 Exc 2)"
    ),
    "PublicServantAdvancingJustice": PredicateSignature(
        name="PublicServantAdvancingJustice", arity=1, arg_types=[LegalType.PERSON],
        category="EXCEPTION", description="Public servant or person aiding public servant acting in good faith belief of lawful duty (Sec 101 Exc 3)"
    ),
    "SuddenFightUponSuddenQuarrel": PredicateSignature(
        name="SuddenFightUponSuddenQuarrel", arity=2, arg_types=[LegalType.PERSON, LegalType.PERSON],
        category="EXCEPTION", description="Offence committed in sudden fight in heat of passion upon sudden quarrel (Sec 101 Exc 4)"
    ),
    "TookUndueAdvantageOrActedCruelly": PredicateSignature(
        name="TookUndueAdvantageOrActedCruelly", arity=1, arg_types=[LegalType.PERSON],
        category="PROVISO", description="Offender x took undue advantage or acted in a cruel or unusual manner (Sec 101 Exc 4)"
    ),
    "VictimAboveAge18": PredicateSignature(
        name="VictimAboveAge18", arity=1, arg_types=[LegalType.PERSON],
        category="EXCEPTION", description="Victim y is above eighteen years of age (Sec 101 Exc 5)"
    ),
    "VictimConsentsToRiskOfDeath": PredicateSignature(
        name="VictimConsentsToRiskOfDeath", arity=1, arg_types=[LegalType.PERSON],
        category="EXCEPTION", description="Victim y suffers death or takes the risk of death with own consent (Sec 101 Exc 5)"
    ),

    # Higher-Order Offence Classifications
    "PrimaFacieMurder": PredicateSignature(
        name="PrimaFacieMurder", arity=2, arg_types=[LegalType.PERSON, LegalType.PERSON],
        category="STATUS", description="Actus reus and mens rea of murder are prima facie satisfied"
    ),
    "ExceptedFromMurder": PredicateSignature(
        name="ExceptedFromMurder", arity=2, arg_types=[LegalType.PERSON, LegalType.PERSON],
        category="STATUS", description="A statutory exception to murder applies under Section 101"
    ),
    "Murder": PredicateSignature(
        name="Murder", arity=2, arg_types=[LegalType.PERSON, LegalType.PERSON],
        category="STATUS", description="Person x is legally liable for the offence of murder of y under Section 101"
    ),
    "CulpableHomicideNotAmountingToMurder": PredicateSignature(
        name="CulpableHomicideNotAmountingToMurder", arity=2, arg_types=[LegalType.PERSON, LegalType.PERSON],
        category="STATUS", description="Act constitutes culpable homicide not amounting to murder"
    ),

    # Section 103: Punishment for Murder & Mob Lynching
    "ActingInConcertOnDiscriminatoryGround": PredicateSignature(
        name="ActingInConcertOnDiscriminatoryGround", arity=3, arg_types=[LegalType.ANY, LegalType.PERSON, LegalType.GROUND],
        category="ACTUS_REUS", description="Group g of 5 or more commits murder of y on discriminatory ground (Sec 103 ss 2)"
    ),
    "LiableToPunishment": PredicateSignature(
        name="LiableToPunishment", arity=2, arg_types=[LegalType.PERSON, LegalType.PENALTY],
        category="PUNISHMENT", description="Person x is liable to statutory penal sanction"
    ),

    # Section 318: Cheating
    "Deceives": PredicateSignature(
        name="Deceives", arity=2, arg_types=[LegalType.PERSON, LegalType.PERSON],
        category="ACTUS_REUS", description="Person x deceives person y (Sec 318 ss 1)"
    ),
    "DishonestlyConcealsFact": PredicateSignature(
        name="DishonestlyConcealsFact", arity=3, arg_types=[LegalType.PERSON, LegalType.PERSON, LegalType.ANY],
        category="ACTUS_REUS", description="Person x dishonestly conceals fact f from person y (Sec 318 Expl)"
    ),
    "FraudulentlyOrDishonestlyInducesDelivery": PredicateSignature(
        name="FraudulentlyOrDishonestlyInducesDelivery", arity=3, arg_types=[LegalType.PERSON, LegalType.PERSON, LegalType.PROPERTY],
        category="ACTUS_REUS", description="Person x fraudulently or dishonestly induces y to deliver property p (Sec 318 ss 1)"
    ),
    "IntentionallyInducesHarmfulActOrOmission": PredicateSignature(
        name="IntentionallyInducesHarmfulActOrOmission", arity=2, arg_types=[LegalType.PERSON, LegalType.PERSON],
        category="ACTUS_REUS", description="Person x intentionally induces y to do/omit act causing harm in body, mind, reputation or property (Sec 318 ss 1)"
    ),
    "Cheats": PredicateSignature(
        name="Cheats", arity=2, arg_types=[LegalType.PERSON, LegalType.PERSON],
        category="STATUS", description="Person x commits the offence of cheating against person y under Section 318"
    ),
    "BoundByLawOrContractToProtectInterest": PredicateSignature(
        name="BoundByLawOrContractToProtectInterest", arity=2, arg_types=[LegalType.PERSON, LegalType.PERSON],
        category="STATUS", description="Offender x was bound by law or contract to protect interest of person y (Sec 318 ss 3)"
    ),
    "KnowsLikelyToCauseWrongfulLossToProtectedPerson": PredicateSignature(
        name="KnowsLikelyToCauseWrongfulLossToProtectedPerson", arity=2, arg_types=[LegalType.PERSON, LegalType.PERSON],
        category="MENS_REA", description="Offender knows act is likely to cause wrongful loss to protected person (Sec 318 ss 3)"
    ),
    "BreachOfContract": PredicateSignature(
        name="BreachOfContract", arity=2, arg_types=[LegalType.PERSON, LegalType.PERSON],
        category="STATUS", description="Person x failed to perform a contractual promise owed to y (a civil wrong; relevant to Sec 318 Illus. g)"
    ),
    "InducesDeliveryOfPropertyOrValuableSecurity": PredicateSignature(
        name="InducesDeliveryOfPropertyOrValuableSecurity", arity=3, arg_types=[LegalType.PERSON, LegalType.PERSON, LegalType.PROPERTY],
        category="ACTUS_REUS", description="Offender dishonestly induces delivery of property or valuable security (Sec 318 ss 4)"
    )
}


# Argument roles: who plays which part in each predicate. Used to document the ontology and to
# tell an LLM fact extractor the argument order (e.g. the provoker comes first in GraveAndSuddenProvocation).
ARG_ROLES: Dict[str, List[str]] = {
    "Person": ["person"], "GroupOfPersons": ["group"], "MemberOfGroup": ["member", "group"],
    "CausesDeath": ["accused", "victim"], "IntentionToCauseDeath": ["accused", "victim"],
    "IntentionToCauseBodilyInjury": ["accused", "victim"], "KnowsInjuryLikelyToCauseDeath": ["accused", "victim"],
    "BodilyInjurySufficientInOrdinaryCourse": ["accused", "victim"], "ImminentlyDangerousAct": ["accused"],
    "KnowledgeOfProbabilityOfDeath": ["accused"], "WithoutLawfulExcuse": ["accused"],
    "GraveAndSuddenProvocation": ["provoker", "accused"], "DeprivedOfSelfControl": ["accused"],
    "ProvocationVoluntarilySought": ["accused"], "ProvocationByLawfulPublicServant": ["provoker"],
    "ProvocationByLawfulPrivateDefence": ["provoker"], "ExceedsPrivateDefenceInGoodFaith": ["accused"],
    "WithoutPremeditation": ["accused"], "WithoutIntentionOfMoreHarmThanNecessary": ["accused"],
    "PublicServantAdvancingJustice": ["accused"], "SuddenFightUponSuddenQuarrel": ["accused", "victim"],
    "TookUndueAdvantageOrActedCruelly": ["accused"], "VictimAboveAge18": ["victim"],
    "VictimConsentsToRiskOfDeath": ["victim"], "PrimaFacieMurder": ["accused", "victim"],
    "ExceptedFromMurder": ["accused", "victim"], "Murder": ["accused", "victim"],
    "CulpableHomicideNotAmountingToMurder": ["accused", "victim"],
    "ActingInConcertOnDiscriminatoryGround": ["group", "victim", "ground"],
    "LiableToPunishment": ["accused", "penalty"], "Deceives": ["deceiver", "deceived"],
    "DishonestlyConcealsFact": ["accused", "deceived", "concealed_fact"],
    "FraudulentlyOrDishonestlyInducesDelivery": ["accused", "deceived", "property"],
    "IntentionallyInducesHarmfulActOrOmission": ["accused", "deceived"], "Cheats": ["accused", "victim"],
    "BoundByLawOrContractToProtectInterest": ["accused", "protected_person"],
    "KnowsLikelyToCauseWrongfulLossToProtectedPerson": ["accused", "protected_person"],
    "BreachOfContract": ["promisor", "promisee"],
    "InducesDeliveryOfPropertyOrValuableSecurity": ["accused", "deceived", "property"],
}
for _name, _roles in ARG_ROLES.items():
    PREDICATE_REGISTRY[_name].arg_names = _roles
assert all(len(s.arg_names) == s.arity for s in PREDICATE_REGISTRY.values()), "every predicate needs argument roles"
