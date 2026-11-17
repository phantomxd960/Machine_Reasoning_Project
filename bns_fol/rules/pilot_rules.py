"""
Gold-Standard Formal First-Order Logic Rules for Pilot Sections:
- Section 101: Murder (Definitions, 4 mental elements, 5 statutory exceptions, provisos)
- Section 103: Punishment for Murder (Standard & Mob Lynching)
- Section 318: Cheating (Deception, inducement, explanation, 3 penalty tiers)
"""
from typing import List
from bns_fol.rules.schema import StatutoryRule

def get_pilot_rules() -> List[StatutoryRule]:
    rules = []

    # =========================================================================
    # SECTION 101: MURDER
    # =========================================================================

    # Clause (a): Intention of causing death
    rules.append(StatutoryRule(
        rule_id="RULE-BNS-101-CL-A",
        section_number=101,
        source_component_id="BNS-SEC-101-MAIN-CL-A",
        rule_name="Murder by Direct Intention to Cause Death",
        rule_type="OFFENCE_ELEMENT",
        variables=["x", "y"],
        premises=["CausesDeath(x, y)", "IntentionToCauseDeath(x, y)"],
        conclusion="PrimaFacieMurder(x, y)",
        formula_unicode="∀x, y. CausesDeath(x, y) ∧ IntentionToCauseDeath(x, y) → PrimaFacieMurder(x, y)",
        formula_latex=r"\forall x, y \ (\text{CausesDeath}(x, y) \land \text{IntentionToCauseDeath}(x, y) \to \text{PrimaFacieMurder}(x, y))",
        formula_ascii="ALL x, y. (CausesDeath(x, y) & IntentionToCauseDeath(x, y) -> PrimaFacieMurder(x, y))",
        description="Culpable homicide is prima facie murder if the act by which death is caused is done with the intention of causing death."
    ))

    # Clause (b): Intention to cause bodily injury known likely to cause death
    rules.append(StatutoryRule(
        rule_id="RULE-BNS-101-CL-B",
        section_number=101,
        source_component_id="BNS-SEC-101-MAIN-CL-B",
        rule_name="Murder by Injury with Subjective Knowledge of Lethality",
        rule_type="OFFENCE_ELEMENT",
        variables=["x", "y"],
        premises=["CausesDeath(x, y)", "IntentionToCauseBodilyInjury(x, y)", "KnowsInjuryLikelyToCauseDeath(x, y)"],
        conclusion="PrimaFacieMurder(x, y)",
        formula_unicode="∀x, y. CausesDeath(x, y) ∧ IntentionToCauseBodilyInjury(x, y) ∧ KnowsInjuryLikelyToCauseDeath(x, y) → PrimaFacieMurder(x, y)",
        formula_latex=r"\forall x, y \ (\text{CausesDeath}(x, y) \land \text{IntentionToCauseBodilyInjury}(x, y) \land \text{KnowsInjuryLikelyToCauseDeath}(x, y) \to \text{PrimaFacieMurder}(x, y))",
        formula_ascii="ALL x, y. (CausesDeath(x, y) & IntentionToCauseBodilyInjury(x, y) & KnowsInjuryLikelyToCauseDeath(x, y) -> PrimaFacieMurder(x, y))",
        description="Culpable homicide is prima facie murder if done with intention to cause such bodily injury as offender knows likely to cause death."
    ))

    # Clause (c): Intention to cause bodily injury sufficient in ordinary course of nature
    rules.append(StatutoryRule(
        rule_id="RULE-BNS-101-CL-C",
        section_number=101,
        source_component_id="BNS-SEC-101-MAIN-CL-C",
        rule_name="Murder by Objectively Sufficient Bodily Injury",
        rule_type="OFFENCE_ELEMENT",
        variables=["x", "y"],
        premises=["CausesDeath(x, y)", "IntentionToCauseBodilyInjury(x, y)", "BodilyInjurySufficientInOrdinaryCourse(x, y)"],
        conclusion="PrimaFacieMurder(x, y)",
        formula_unicode="∀x, y. CausesDeath(x, y) ∧ IntentionToCauseBodilyInjury(x, y) ∧ BodilyInjurySufficientInOrdinaryCourse(x, y) → PrimaFacieMurder(x, y)",
        formula_latex=r"\forall x, y \ (\text{CausesDeath}(x, y) \land \text{IntentionToCauseBodilyInjury}(x, y) \land \text{BodilyInjurySufficientInOrdinaryCourse}(x, y) \to \text{PrimaFacieMurder}(x, y))",
        formula_ascii="ALL x, y. (CausesDeath(x, y) & IntentionToCauseBodilyInjury(x, y) & BodilyInjurySufficientInOrdinaryCourse(x, y) -> PrimaFacieMurder(x, y))",
        description="Culpable homicide is prima facie murder if bodily injury intended to be inflicted is sufficient in ordinary course of nature to cause death."
    ))

    # Clause (d): Imminently dangerous act without lawful excuse
    rules.append(StatutoryRule(
        rule_id="RULE-BNS-101-CL-D",
        section_number=101,
        source_component_id="BNS-SEC-101-MAIN-CL-D",
        rule_name="Murder by Imminently Dangerous Act",
        rule_type="OFFENCE_ELEMENT",
        variables=["x", "y"],
        premises=["CausesDeath(x, y)", "ImminentlyDangerousAct(x)", "KnowledgeOfProbabilityOfDeath(x)", "WithoutLawfulExcuse(x)"],
        conclusion="PrimaFacieMurder(x, y)",
        formula_unicode="∀x, y. CausesDeath(x, y) ∧ ImminentlyDangerousAct(x) ∧ KnowledgeOfProbabilityOfDeath(x) ∧ WithoutLawfulExcuse(x) → PrimaFacieMurder(x, y)",
        formula_latex=r"\forall x, y \ (\text{CausesDeath}(x, y) \land \text{ImminentlyDangerousAct}(x) \land \text{KnowledgeOfProbabilityOfDeath}(x) \land \text{WithoutLawfulExcuse}(x) \to \text{PrimaFacieMurder}(x, y))",
        formula_ascii="ALL x, y. (CausesDeath(x, y) & ImminentlyDangerousAct(x) & KnowledgeOfProbabilityOfDeath(x) & WithoutLawfulExcuse(x) -> PrimaFacieMurder(x, y))",
        description="Culpable homicide is prima facie murder if act is so imminently dangerous that it must in all probability cause death, without lawful excuse."
    ))

    # Exception 1: Grave and Sudden Provocation
    rules.append(StatutoryRule(
        rule_id="RULE-BNS-101-EXC-1",
        section_number=101,
        source_component_id="BNS-SEC-101-EXC-1",
        rule_name="Exception 1: Grave and Sudden Provocation",
        rule_type="EXCEPTION_DEFENCE",
        variables=["x", "y"],
        premises=[
            "GraveAndSuddenProvocation(y, x)",
            "DeprivedOfSelfControl(x)",
            "~ProvocationVoluntarilySought(x)",
            "~ProvocationByLawfulPublicServant(y)",
            "~ProvocationByLawfulPrivateDefence(y)"
        ],
        conclusion="Exception1GraveSuddenProvocation(x, y)",
        formula_unicode="∀x, y. GraveAndSuddenProvocation(y, x) ∧ DeprivedOfSelfControl(x) ∧ ¬ProvocationVoluntarilySought(x) ∧ ¬ProvocationByLawfulPublicServant(y) ∧ ¬ProvocationByLawfulPrivateDefence(y) → Exception1GraveSuddenProvocation(x, y)",
        formula_latex=r"\forall x, y \ (\text{Provocation}(y, x) \land \text{DeprivedOfSelfControl}(x) \land \neg \text{Sought}(x) \land \neg \text{PublicServant}(y) \land \neg \text{PrivateDefence}(y) \to \text{Exception1}(x, y))",
        formula_ascii="ALL x, y. (GraveAndSuddenProvocation(y, x) & DeprivedOfSelfControl(x) & ~ProvocationVoluntarilySought(x) & ~ProvocationByLawfulPublicServant(y) & ~ProvocationByLawfulPrivateDefence(y) -> Exception1GraveSuddenProvocation(x, y))",
        description="Exception 1 applies if offender was deprived of self-control by grave and sudden provocation, provided provocation was not voluntarily sought, lawful by public servant, or in private defence."
    ))

    # Exception 2: Exceeding Private Defence in Good Faith
    rules.append(StatutoryRule(
        rule_id="RULE-BNS-101-EXC-2",
        section_number=101,
        source_component_id="BNS-SEC-101-EXC-2",
        rule_name="Exception 2: Private Defence Exceeded in Good Faith",
        rule_type="EXCEPTION_DEFENCE",
        variables=["x", "y"],
        premises=["ExceedsPrivateDefenceInGoodFaith(x)", "WithoutPremeditation(x)", "WithoutIntentionOfMoreHarmThanNecessary(x)"],
        conclusion="Exception2PrivateDefence(x, y)",
        formula_unicode="∀x, y. ExceedsPrivateDefenceInGoodFaith(x) ∧ WithoutPremeditation(x) ∧ WithoutIntentionOfMoreHarmThanNecessary(x) → Exception2PrivateDefence(x, y)",
        formula_latex=r"\forall x, y \ (\text{ExceedsPrivateDefence}(x) \land \text{WithoutPremeditation}(x) \land \text{NoExcessHarmIntent}(x) \to \text{Exception2}(x, y))",
        formula_ascii="ALL x, y. (ExceedsPrivateDefenceInGoodFaith(x) & WithoutPremeditation(x) & WithoutIntentionOfMoreHarmThanNecessary(x) -> Exception2PrivateDefence(x, y))",
        description="Exception 2 applies if private defence is exercised in good faith without premeditation and without intention of doing more harm than necessary."
    ))

    # Exception 3: Public Servant Acting in Good Faith
    rules.append(StatutoryRule(
        rule_id="RULE-BNS-101-EXC-3",
        section_number=101,
        source_component_id="BNS-SEC-101-EXC-3",
        rule_name="Exception 3: Public Servant Advancing Justice",
        rule_type="EXCEPTION_DEFENCE",
        variables=["x", "y"],
        premises=["PublicServantAdvancingJustice(x)", "WithoutPremeditation(x)"],
        conclusion="Exception3PublicServant(x, y)",
        formula_unicode="∀x, y. PublicServantAdvancingJustice(x) ∧ WithoutPremeditation(x) → Exception3PublicServant(x, y)",
        formula_latex=r"\forall x, y \ (\text{PublicServantAdvancingJustice}(x) \land \text{WithoutPremeditation}(x) \to \text{Exception3}(x, y))",
        formula_ascii="ALL x, y. (PublicServantAdvancingJustice(x) & WithoutPremeditation(x) -> Exception3PublicServant(x, y))",
        description="Exception 3 applies if public servant acts in good faith believing action lawful and necessary for discharge of duty."
    ))

    # Exception 4: Sudden Fight
    rules.append(StatutoryRule(
        rule_id="RULE-BNS-101-EXC-4",
        section_number=101,
        source_component_id="BNS-SEC-101-EXC-4",
        rule_name="Exception 4: Sudden Fight Upon Sudden Quarrel",
        rule_type="EXCEPTION_DEFENCE",
        variables=["x", "y"],
        premises=["SuddenFightUponSuddenQuarrel(x, y)", "WithoutPremeditation(x)", "~TookUndueAdvantageOrActedCruelly(x)"],
        conclusion="Exception4SuddenFight(x, y)",
        formula_unicode="∀x, y. SuddenFightUponSuddenQuarrel(x, y) ∧ WithoutPremeditation(x) ∧ ¬TookUndueAdvantageOrActedCruelly(x) → Exception4SuddenFight(x, y)",
        formula_latex=r"\forall x, y \ (\text{SuddenFight}(x, y) \land \text{WithoutPremeditation}(x) \land \neg \text{UndueAdvantageOrCruel}(x) \to \text{Exception4}(x, y))",
        formula_ascii="ALL x, y. (SuddenFightUponSuddenQuarrel(x, y) & WithoutPremeditation(x) & ~TookUndueAdvantageOrActedCruelly(x) -> Exception4SuddenFight(x, y))",
        description="Exception 4 applies if committed in sudden fight in heat of passion without premeditation and without taking undue advantage or acting cruelly."
    ))

    # Exception 5: Consent of Victim Above Age 18
    rules.append(StatutoryRule(
        rule_id="RULE-BNS-101-EXC-5",
        section_number=101,
        source_component_id="BNS-SEC-101-EXC-5",
        rule_name="Exception 5: Consent of Adult Victim",
        rule_type="EXCEPTION_DEFENCE",
        variables=["x", "y"],
        premises=["VictimAboveAge18(y)", "VictimConsentsToRiskOfDeath(y)"],
        conclusion="Exception5Consent(x, y)",
        formula_unicode="∀x, y. VictimAboveAge18(y) ∧ VictimConsentsToRiskOfDeath(y) → Exception5Consent(x, y)",
        formula_latex=r"\forall x, y \ (\text{VictimAboveAge18}(y) \land \text{ConsentToDeath}(y) \to \text{Exception5}(x, y))",
        formula_ascii="ALL x, y. (VictimAboveAge18(y) & VictimConsentsToRiskOfDeath(y) -> Exception5Consent(x, y))",
        description="Exception 5 applies when person whose death is caused is above age 18 and suffers death or takes risk of death with own consent."
    ))

    # Exception Aggregators
    for i, exc_pred in enumerate([
        "Exception1GraveSuddenProvocation", "Exception2PrivateDefence",
        "Exception3PublicServant", "Exception4SuddenFight", "Exception5Consent"
    ], 1):
        rules.append(StatutoryRule(
            rule_id=f"RULE-BNS-101-EXC-AGG-{i}",
            section_number=101,
            source_component_id=f"BNS-SEC-101-EXC-{i}",
            rule_name=f"Exception {i} Overrides Murder",
            rule_type="EXCEPTION_OVERRIDE",
            variables=["x", "y"],
            premises=[f"{exc_pred}(x, y)"],
            conclusion="ExceptedFromMurder(x, y)",
            formula_unicode=f"∀x, y. {exc_pred}(x, y) → ExceptedFromMurder(x, y)",
            formula_latex=rf"\forall x, y \ (\text{{{exc_pred}}}(x, y) \to \text{{ExceptedFromMurder}}(x, y))",
            formula_ascii=f"ALL x, y. ({exc_pred}(x, y) -> ExceptedFromMurder(x, y))",
            description=f"If Exception {i} is satisfied, the act is an excepted case under Section 101."
        ))

    # Final Substantive Murder Rule (Actus Reus + Mens Rea AND NOT Excepted)
    rules.append(StatutoryRule(
        rule_id="RULE-BNS-101-FINAL",
        section_number=101,
        source_component_id="BNS-SEC-101-MAIN",
        rule_name="Murder Offence Liability Rule",
        rule_type="OFFENCE_FINAL",
        variables=["x", "y"],
        premises=["PrimaFacieMurder(x, y)", "~ExceptedFromMurder(x, y)"],
        conclusion="Murder(x, y)",
        formula_unicode="∀x, y. PrimaFacieMurder(x, y) ∧ ¬ExceptedFromMurder(x, y) → Murder(x, y)",
        formula_latex=r"\forall x, y \ (\text{PrimaFacieMurder}(x, y) \land \neg \text{ExceptedFromMurder}(x, y) \to \text{Murder}(x, y))",
        formula_ascii="ALL x, y. (PrimaFacieMurder(x, y) & ~ExceptedFromMurder(x, y) -> Murder(x, y))",
        description="Except in the cases hereinafter excepted, culpable homicide is murder."
    ))

    # Mitigated Offence Rule (Culpable Homicide Not Amounting to Murder)
    rules.append(StatutoryRule(
        rule_id="RULE-BNS-101-MITIGATED",
        section_number=101,
        source_component_id="BNS-SEC-101-MAIN",
        rule_name="Mitigation to Culpable Homicide Not Amounting to Murder",
        rule_type="OFFENCE_MITIGATED",
        variables=["x", "y"],
        premises=["PrimaFacieMurder(x, y)", "ExceptedFromMurder(x, y)"],
        conclusion="CulpableHomicideNotAmountingToMurder(x, y)",
        formula_unicode="∀x, y. PrimaFacieMurder(x, y) ∧ ExceptedFromMurder(x, y) → CulpableHomicideNotAmountingToMurder(x, y)",
        formula_latex=r"\forall x, y \ (\text{PrimaFacieMurder}(x, y) \land \text{ExceptedFromMurder}(x, y) \to \text{CulpableHomicideNotAmountingToMurder}(x, y))",
        formula_ascii="ALL x, y. (PrimaFacieMurder(x, y) & ExceptedFromMurder(x, y) -> CulpableHomicideNotAmountingToMurder(x, y))",
        description="If prima facie murder conditions are met but an exception applies, offence is mitigated to culpable homicide not amounting to murder."
    ))

    # =========================================================================
    # SECTION 103: PUNISHMENT FOR MURDER
    # =========================================================================

    # Subsection 1: Whoever commits murder
    rules.append(StatutoryRule(
        rule_id="RULE-BNS-103-SS-1",
        section_number=103,
        source_component_id="BNS-SEC-103-SS-1",
        rule_name="Punishment for Murder",
        rule_type="PUNISHMENT_MAPPING",
        variables=["x", "y"],
        premises=["Murder(x, y)"],
        conclusion="LiableToPunishment(x, DeathOrImprisonmentForLifeAndFine)",
        formula_unicode="∀x, y. Murder(x, y) → LiableToPunishment(x, DeathOrImprisonmentForLifeAndFine)",
        formula_latex=r"\forall x, y \ (\text{Murder}(x, y) \to \text{LiableToPunishment}(x, \text{DeathOrLifeImprisonmentAndFine}))",
        formula_ascii="ALL x, y. (Murder(x, y) -> LiableToPunishment(x, DeathOrImprisonmentForLifeAndFine))",
        description="Whoever commits murder shall be punished with death or imprisonment for life, and shall also be liable to fine."
    ))

    # Subsection 2: Mob Lynching / Murder by group on discriminatory ground
    rules.append(StatutoryRule(
        rule_id="RULE-BNS-103-SS-2",
        section_number=103,
        source_component_id="BNS-SEC-103-SS-2",
        rule_name="Punishment for Mob Lynching / Hate Murder",
        rule_type="PUNISHMENT_MAPPING",
        variables=["g", "x", "y", "ground"],
        # Section 103(2) applies only when the group "commits murder", so Murder(x, y) is a required premise.
        premises=["GroupOfPersons(g)", "MemberOfGroup(x, g)", "ActingInConcertOnDiscriminatoryGround(g, y, ground)", "Murder(x, y)"],
        conclusion="LiableToPunishment(x, DeathOrImprisonmentForLifeAndFine)",
        formula_unicode="∀g, x, y, ground. GroupOfPersons(g) ∧ MemberOfGroup(x, g) ∧ ActingInConcertOnDiscriminatoryGround(g, y, ground) ∧ Murder(x, y) → LiableToPunishment(x, DeathOrImprisonmentForLifeAndFine)",
        formula_latex=r"\forall g, x, y, \text{ground} \ (\text{Group}(g) \land \text{Member}(x, g) \land \text{ConcertDiscriminatory}(g, y, \text{ground}) \land \text{Murder}(x, y) \to \text{LiableToPunishment}(x, \text{DeathOrLifeImprisonmentAndFine}))",
        formula_ascii="ALL g, x, y, ground. (GroupOfPersons(g) & MemberOfGroup(x, g) & ActingInConcertOnDiscriminatoryGround(g, y, ground) & Murder(x, y) -> LiableToPunishment(x, DeathOrImprisonmentForLifeAndFine))",
        description="When group of five or more acting in concert commits murder on discriminatory grounds, each member is punished with death or life imprisonment."
    ))

    # =========================================================================
    # SECTION 318: CHEATING
    # =========================================================================

    # Explanation: Concealment of facts is deception
    rules.append(StatutoryRule(
        rule_id="RULE-BNS-318-EXPL",
        section_number=318,
        source_component_id="BNS-SEC-318-SS-1-EXPL-1",
        rule_name="Dishonest Concealment as Deception",
        rule_type="DEFINITIONAL_EXPANSION",
        variables=["x", "y", "f"],
        premises=["DishonestlyConcealsFact(x, y, f)"],
        conclusion="Deceives(x, y)",
        formula_unicode="∀x, y, f. DishonestlyConcealsFact(x, y, f) → Deceives(x, y)",
        formula_latex=r"\forall x, y, f \ (\text{DishonestlyConcealsFact}(x, y, f) \to \text{Deceives}(x, y))",
        formula_ascii="ALL x, y, f. (DishonestlyConcealsFact(x, y, f) -> Deceives(x, y))",
        description="A dishonest concealment of facts is a deception within the meaning of this section."
    ))

    # Subsection 1 (Branch 1): Deception + Fraudulent inducement of property delivery
    rules.append(StatutoryRule(
        rule_id="RULE-BNS-318-SS-1-DELIVERY",
        section_number=318,
        source_component_id="BNS-SEC-318-SS-1",
        rule_name="Cheating by Inducing Property Delivery",
        rule_type="OFFENCE_ELEMENT",
        variables=["x", "y", "p"],
        premises=["Deceives(x, y)", "FraudulentlyOrDishonestlyInducesDelivery(x, y, p)"],
        conclusion="Cheats(x, y)",
        formula_unicode="∀x, y, p. Deceives(x, y) ∧ FraudulentlyOrDishonestlyInducesDelivery(x, y, p) → Cheats(x, y)",
        formula_latex=r"\forall x, y, p \ (\text{Deceives}(x, y) \land \text{FraudulentlyOrDishonestlyInducesDelivery}(x, y, p) \to \text{Cheats}(x, y))",
        formula_ascii="ALL x, y, p. (Deceives(x, y) & FraudulentlyOrDishonestlyInducesDelivery(x, y, p) -> Cheats(x, y))",
        description="Deceiving any person and fraudulently or dishonestly inducing delivery of property constitutes cheating."
    ))

    # Subsection 1 (Branch 2): Deception + Intentionally inducing harmful act/omission
    rules.append(StatutoryRule(
        rule_id="RULE-BNS-318-SS-1-HARM",
        section_number=318,
        source_component_id="BNS-SEC-318-SS-1",
        rule_name="Cheating by Inducing Harmful Act or Omission",
        rule_type="OFFENCE_ELEMENT",
        variables=["x", "y"],
        premises=["Deceives(x, y)", "IntentionallyInducesHarmfulActOrOmission(x, y)"],
        conclusion="Cheats(x, y)",
        formula_unicode="∀x, y. Deceives(x, y) ∧ IntentionallyInducesHarmfulActOrOmission(x, y) → Cheats(x, y)",
        formula_latex=r"\forall x, y \ (\text{Deceives}(x, y) \land \text{IntentionallyInducesHarmfulActOrOmission}(x, y) \to \text{Cheats}(x, y))",
        formula_ascii="ALL x, y. (Deceives(x, y) & IntentionallyInducesHarmfulActOrOmission(x, y) -> Cheats(x, y))",
        description="Deceiving any person and intentionally inducing act causing harm in body, mind, reputation or property constitutes cheating."
    ))

    # Subsection 2: Basic punishment for cheating
    rules.append(StatutoryRule(
        rule_id="RULE-BNS-318-SS-2",
        section_number=318,
        source_component_id="BNS-SEC-318-SS-2",
        rule_name="Basic Punishment for Cheating",
        rule_type="PUNISHMENT_MAPPING",
        variables=["x", "y"],
        premises=["Cheats(x, y)"],
        conclusion="LiableToPunishment(x, ImprisonmentUpTo3YearsOrFineOrBoth)",
        formula_unicode="∀x, y. Cheats(x, y) → LiableToPunishment(x, ImprisonmentUpTo3YearsOrFineOrBoth)",
        formula_latex=r"\forall x, y \ (\text{Cheats}(x, y) \to \text{LiableToPunishment}(x, \text{ImprisonmentUpTo3YearsOrFineOrBoth}))",
        formula_ascii="ALL x, y. (Cheats(x, y) -> LiableToPunishment(x, ImprisonmentUpTo3YearsOrFineOrBoth))",
        description="Whoever cheats shall be punished with imprisonment up to three years, or with fine, or with both."
    ))

    # Subsection 3: Aggravated Cheating with Knowledge of Wrongful Loss to Protected Person
    rules.append(StatutoryRule(
        rule_id="RULE-BNS-318-SS-3",
        section_number=318,
        source_component_id="BNS-SEC-318-SS-3",
        rule_name="Aggravated Cheating: Fiduciary/Protected Person",
        rule_type="PUNISHMENT_MAPPING",
        variables=["x", "y"],
        premises=["Cheats(x, y)", "BoundByLawOrContractToProtectInterest(x, y)", "KnowsLikelyToCauseWrongfulLossToProtectedPerson(x, y)"],
        conclusion="LiableToPunishment(x, ImprisonmentUpTo5YearsOrFineOrBoth)",
        formula_unicode="∀x, y. Cheats(x, y) ∧ BoundByLawOrContractToProtectInterest(x, y) ∧ KnowsLikelyToCauseWrongfulLossToProtectedPerson(x, y) → LiableToPunishment(x, ImprisonmentUpTo5YearsOrFineOrBoth)",
        formula_latex=r"\forall x, y \ (\text{Cheats}(x, y) \land \text{Fiduciary}(x, y) \land \text{KnowsWrongfulLoss}(x, y) \to \text{LiableToPunishment}(x, \text{ImprisonmentUpTo5YearsOrFineOrBoth}))",
        formula_ascii="ALL x, y. (Cheats(x, y) & BoundByLawOrContractToProtectInterest(x, y) & KnowsLikelyToCauseWrongfulLossToProtectedPerson(x, y) -> LiableToPunishment(x, ImprisonmentUpTo5YearsOrFineOrBoth))",
        description="Cheating with knowledge that offender was bound by law/contract to protect interest shall be punished up to five years, or fine, or both."
    ))

    # Subsection 4: Aggravated Cheating by Inducing Delivery of Valuable Security
    rules.append(StatutoryRule(
        rule_id="RULE-BNS-318-SS-4",
        section_number=318,
        source_component_id="BNS-SEC-318-SS-4",
        rule_name="Aggravated Cheating: Valuable Security",
        rule_type="PUNISHMENT_MAPPING",
        variables=["x", "y", "p"],
        premises=["Cheats(x, y)", "InducesDeliveryOfPropertyOrValuableSecurity(x, y, p)"],
        conclusion="LiableToPunishment(x, ImprisonmentUpTo7YearsAndFine)",
        formula_unicode="∀x, y, p. Cheats(x, y) ∧ InducesDeliveryOfPropertyOrValuableSecurity(x, y, p) → LiableToPunishment(x, ImprisonmentUpTo7YearsAndFine)",
        formula_latex=r"\forall x, y, p \ (\text{Cheats}(x, y) \land \text{InducesValuableSecurity}(x, y, p) \to \text{LiableToPunishment}(x, \text{ImprisonmentUpTo7YearsAndFine}))",
        formula_ascii="ALL x, y, p. (Cheats(x, y) & InducesDeliveryOfPropertyOrValuableSecurity(x, y, p) -> LiableToPunishment(x, ImprisonmentUpTo7YearsAndFine))",
        description="Cheating and dishonestly inducing delivery of property or valuable security shall be punished up to seven years, and fine."
    ))

    # -------------------------------------------------------------------------
    # Rule metadata used by the generic verification engine
    # -------------------------------------------------------------------------
    civil_breach_note = (
        "Deception is an essential element of cheating. Where the promise was made with an honest intention "
        "to perform and was only later broken, Section 318 Illustration (g) treats this as a civil breach of "
        "contract, not the criminal offence of cheating."
    )
    metadata = {
        # Exception 5 is raised by the victim's consent; the age condition is what must then be proven.
        "RULE-BNS-101-EXC-5": {"trigger_premises": ["VictimConsentsToRiskOfDeath(y)"]},
        "RULE-BNS-318-SS-1-DELIVERY": {"premise_notes": {"Deceives(x, y)": civil_breach_note}},
        "RULE-BNS-318-SS-1-HARM": {"premise_notes": {"Deceives(x, y)": civil_breach_note}},
    }
    return [
        r.model_copy(update={"formalization_level": "GOLD", **metadata.get(r.rule_id, {})})
        for r in rules
    ]
