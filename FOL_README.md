# First-Order Logic (FOL) Formalization Engine for Bharatiya Nyaya Sanhita (BNS), 2023

**Project**: Legal Reasoning Verification System  
**Stage**: Stage 3 — Formal Legal Representation  
**Domain**: Bharatiya Nyaya Sanhita, 2023 (Act No. 45 of 2023)  
**Deliverables**: 
- `data/output/formal_rules.jsonl` (1,281 formal FOL rules across all 358 sections)
- `data/output/formal_rules.csv` (Spreadsheet export for human audit)
- `data/output/predicate_ontology.json` (Legal predicate signatures & arities)
- `bns_fol/` (Pure-Python FOL AST, Predicate Ontology, Open-World 3-Valued Evaluator)

---

## 1. Executive Summary & Theoretical Motivation

Converting natural-language statutory text into formal logic is the central bridge in computational legal reasoning. While large language models (LLMs) can generate fluent text, they frequently commit catastrophic legal fallacies:
1. **Monotonicity Fallacy**: Assuming that establishing an offence's elements automatically implies guilt, ignoring statutory exceptions and provisos.
2. **Closed-World Fallacy**: Assuming that any fact not explicitly mentioned in a scenario is false (e.g., concluding lack of consent merely because consent was unmentioned).
3. **Threshold Conflation**: Merging distinct mental states (*intention* vs *knowledge* vs *grave provocation*) into vague embeddings.

The **BNS FOL Formalization Engine** solves these problems by transforming the verified statutory components from Stage 1 into a sound, typed **First-Order Logic (FOL)** representation evaluated under the **Open-World Assumption (3-Valued Kleene Logic)**.

---

## 2. Mathematical Formalization of Criminal Statutes

In criminal jurisprudence, liability is decomposed into three structural layers:
1. **Actus Reus & Mens Rea (Positive Elements)**: Objective conduct and culpable mental state.
2. **Defeasible Statutory Exceptions (Negative Elements)**: Legally enacted general and special exceptions that negate or mitigate liability.
3. **Provisos (Defeaters of Defences)**: Restrictive clauses enacted to limit when an exception may be invoked.

### 2.1 The General Statutory Offence Equation

For any statutory offence $\Phi$ (such as Murder under Section 101), the formal rule is formulated as:

$$\forall x, y \ \Big( \text{PrimaFacieOffence}_\Phi(x, y) \land \neg \text{Excepted}_\Phi(x, y) \longrightarrow \text{Liable}_\Phi(x, y) \Big)$$

Where:
- $\text{PrimaFacieOffence}_\Phi(x, y)$ is satisfied if any statutory element branch is met:
  $$\text{PrimaFacieOffence}_\Phi(x, y) \iff \bigvee_{k} \text{Clause}_k(x, y)$$
- $\text{Excepted}_\Phi(x, y)$ is satisfied if any statutory exception applies:
  $$\text{Excepted}_\Phi(x, y) \iff \bigvee_{j} \text{Exception}_j(x, y)$$

---

## 3. Deep-Dive Case Studies on Pilot Sections

### 3.1 Section 101: Murder

Section 101 of BNS 2023 opens with explicit defeasibility syntax:
> *"Except in the cases hereinafter excepted, culpable homicide is murder..."*

#### A. Positive Mental Element Branches (Clauses a–d)

1. **Clause (a) — Direct Intention to Cause Death**:
   $$\forall x, y \ \Big( \text{CausesDeath}(x, y) \land \text{IntentionToCauseDeath}(x, y) \longrightarrow \text{PrimaFacieMurder}(x, y) \Big)$$

2. **Clause (b) — Bodily Injury with Subjective Knowledge of Lethality**:
   $$\forall x, y \ \Big( \text{CausesDeath}(x, y) \land \text{IntentionToCauseBodilyInjury}(x, y) \land \text{KnowsInjuryLikelyToCauseDeath}(x, y) \longrightarrow \text{PrimaFacieMurder}(x, y) \Big)$$

3. **Clause (c) — Bodily Injury Sufficient in Ordinary Course of Nature**:
   $$\forall x, y \ \Big( \text{CausesDeath}(x, y) \land \text{IntentionToCauseBodilyInjury}(x, y) \land \text{BodilyInjurySufficientInOrdinaryCourse}(x, y) \longrightarrow \text{PrimaFacieMurder}(x, y) \Big)$$

4. **Clause (d) — Imminently Dangerous Act Without Lawful Excuse**:
   $$\forall x, y \ \Big( \text{CausesDeath}(x, y) \land \text{ImminentlyDangerousAct}(x) \land \text{KnowledgeOfProbabilityOfDeath}(x) \land \text{WithoutLawfulExcuse}(x) \longrightarrow \text{PrimaFacieMurder}(x, y) \Big)$$

#### B. Statutory Exceptions & Proviso Defeaters (Exceptions 1–5)

1. **Exception 1 — Grave and Sudden Provocation**:
   $$\begin{aligned}
   \forall x, y \ \Big( &\text{GraveAndSuddenProvocation}(y, x) \land \text{DeprivedOfSelfControl}(x) \\
   &\land \neg \text{ProvocationVoluntarilySought}(x) \\
   &\land \neg \text{ProvocationByLawfulPublicServant}(y) \\
   &\land \neg \text{ProvocationByLawfulPrivateDefence}(y) \\
   &\longrightarrow \text{Exception1GraveSuddenProvocation}(x, y) \Big)
   \end{aligned}$$

2. **Exception 2 — Private Defence Exceeded in Good Faith**:
   $$\forall x, y \ \Big( \text{ExceedsPrivateDefenceInGoodFaith}(x) \land \text{WithoutPremeditation}(x) \land \text{WithoutIntentionOfMoreHarmThanNecessary}(x) \longrightarrow \text{Exception2PrivateDefence}(x, y) \Big)$$

3. **Exception 3 — Public Servant Advancing Justice**:
   $$\forall x, y \ \Big( \text{PublicServantAdvancingJustice}(x) \land \text{WithoutPremeditation}(x) \longrightarrow \text{Exception3PublicServant}(x, y) \Big)$$

4. **Exception 4 — Sudden Fight Upon Sudden Quarrel**:
   $$\forall x, y \ \Big( \text{SuddenFightUponSuddenQuarrel}(x, y) \land \text{WithoutPremeditation}(x) \land \neg \text{TookUndueAdvantageOrActedCruelly}(x) \longrightarrow \text{Exception4SuddenFight}(x, y) \Big)$$

5. **Exception 5 — Consent of Adult Victim Above Age 18**:
   $$\forall x, y \ \Big( \text{VictimAboveAge18}(y) \land \text{VictimConsentsToRiskOfDeath}(y) \longrightarrow \text{Exception5Consent}(x, y) \Big)$$

#### C. Exception Overriding and Mitigated Offence Rules

- **Exception Aggregation**:
  $$\forall x, y \ \Big( \bigvee_{i=1}^5 \text{Exception}_i(x, y) \longrightarrow \text{ExceptedFromMurder}(x, y) \Big)$$

- **Final Substantive Murder Liability**:
  $$\forall x, y \ \Big( \text{PrimaFacieMurder}(x, y) \land \neg \text{ExceptedFromMurder}(x, y) \longrightarrow \text{Murder}(x, y) \Big)$$

- **Statutory Mitigation to Culpable Homicide Not Amounting to Murder**:
  $$\forall x, y \ \Big( \text{PrimaFacieMurder}(x, y) \land \text{ExceptedFromMurder}(x, y) \longrightarrow \text{CulpableHomicideNotAmountingToMurder}(x, y) \Big)$$

---

### 3.2 Section 103: Punishment for Murder

1. **Subsection (1) — General Murder Penalty**:
   $$\forall x, y \ \Big( \text{Murder}(x, y) \longrightarrow \text{LiableToPunishment}(x, \text{DeathOrImprisonmentForLifeAndFine}) \Big)$$

2. **Subsection (2) — Mob Lynching / Discriminatory Group Murder**:
   $$\begin{aligned}
   \forall g, x, y, \text{ground} \ \Big( &\text{GroupOfPersons}(g) \land \text{MemberOfGroup}(x, g) \land \text{ActingInConcertOnDiscriminatoryGround}(g, y, \text{ground}) \land \text{Murder}(x, y) \\
   &\longrightarrow \text{LiableToPunishment}(x, \text{DeathOrImprisonmentForLifeAndFine}) \Big)
   \end{aligned}$$

---

### 3.3 Section 318: Cheating

1. **Explanation 1 — Definitional Expansion**:
   $$\forall x, y, f \ \Big( \text{DishonestlyConcealsFact}(x, y, f) \longrightarrow \text{Deceives}(x, y) \Big)$$

2. **Subsection (1) — Cheating by Delivery Inducement**:
   $$\forall x, y, p \ \Big( \text{Deceives}(x, y) \land \text{FraudulentlyOrDishonestlyInducesDelivery}(x, y, p) \longrightarrow \text{Cheats}(x, y) \Big)$$

3. **Subsection (1) — Cheating by Harm Inducement**:
   $$\forall x, y \ \Big( \text{Deceives}(x, y) \land \text{IntentionallyInducesHarmfulActOrOmission}(x, y) \longrightarrow \text{Cheats}(x, y) \Big)$$

4. **Subsection (2) — Basic Punishment (Up to 3 Years or Fine or Both)**:
   $$\forall x, y \ \Big( \text{Cheats}(x, y) \longrightarrow \text{LiableToPunishment}(x, \text{ImprisonmentUpTo3YearsOrFineOrBoth}) \Big)$$

5. **Subsection (3) — Aggravated Cheating (Fiduciary Duty / Up to 5 Years)**:
   $$\begin{aligned}
   \forall x, y \ \Big( &\text{Cheats}(x, y) \land \text{BoundByLawOrContractToProtectInterest}(x, y) \\
   &\land \text{KnowsLikelyToCauseWrongfulLossToProtectedPerson}(x, y) \\
   &\longrightarrow \text{LiableToPunishment}(x, \text{ImprisonmentUpTo5YearsOrFineOrBoth}) \Big)
   \end{aligned}$$

6. **Subsection (4) — Aggravated Cheating (Valuable Security / Up to 7 Years)**:
   $$\forall x, y, p \ \Big( \text{Cheats}(x, y) \land \text{InducesDeliveryOfPropertyOrValuableSecurity}(x, y, p) \longrightarrow \text{LiableToPunishment}(x, \text{ImprisonmentUpTo7YearsAndFine}) \Big)$$

---

## 4. Open-World 3-Valued Logic Semantics

To prevent jumping to conclusions when facts are missing, our engine evaluates under **Kleene 3-Valued Logic** ($\mathcal{T} = \{\text{TRUE}, \text{FALSE}, \text{UNKNOWN}\}$):

### 4.1 Truth Tables

| Operator | Left Operand ($A$) | Right Operand ($B$) | Result ($A \odot B$) | Legal Interpretation |
| :--- | :--- | :--- | :--- | :--- |
| **Negation** ($\neg$) | $\text{TRUE}$ | — | $\text{FALSE}$ | Fact proven false |
| | $\text{FALSE}$ | — | $\text{TRUE}$ | Negative fact proven true |
| | $\text{UNKNOWN}$ | — | $\text{UNKNOWN}$ | **Absence of proof is NOT proof of absence** |
| **Conjunction** ($\land$) | $\text{TRUE}$ | $\text{TRUE}$ | $\text{TRUE}$ | All elements verified |
| | $\text{FALSE}$ | Any | $\text{FALSE}$ | Essential element contradicted |
| | $\text{TRUE}$ | $\text{UNKNOWN}$ | $\text{UNKNOWN}$ | **Insufficient information** |
| **Disjunction** ($\lor$) | $\text{TRUE}$ | Any | $\text{TRUE}$ | Alternative statutory branch satisfied |
| | $\text{FALSE}$ | $\text{UNKNOWN}$ | $\text{UNKNOWN}$ | Inconclusive alternative |

---

## 5. Formal Deduction Walkthroughs (Evaluator Verification)

The unit tests (`tests/test_fol_pilot.py`) verify the formal engine against concrete legal scenarios:

### Case 1: Standard Murder Supported
- **Facts**: $\text{CausesDeath}(A, B) = \text{TRUE}$, $\text{IntentionToCauseDeath}(A, B) = \text{TRUE}$.
- **Deduction**:
  1. `RULE-BNS-101-CL-A` fires $\implies \text{PrimaFacieMurder}(A, B) = \text{TRUE}$.
  2. No exceptions alleged $\implies \text{ExceptedFromMurder}(A, B) = \text{FALSE}$.
  3. `RULE-BNS-101-FINAL` fires $\implies \text{Murder}(A, B) = \text{TRUE}$.
- **Output**: `STATUS = SUPPORTED`.

### Case 2: Exception 1 Applied (Mitigated to Culpable Homicide)
- **Facts**:
  - $\text{CausesDeath}(X, Y) = \text{TRUE}$, $\text{IntentionToCauseDeath}(X, Y) = \text{TRUE}$.
  - $\text{GraveAndSuddenProvocation}(Y, X) = \text{TRUE}$, $\text{DeprivedOfSelfControl}(X) = \text{TRUE}$.
  - $\neg \text{ProvocationVoluntarilySought}(X) = \text{TRUE}$, $\neg \text{ProvocationByLawfulPublicServant}(Y) = \text{TRUE}$, $\neg \text{ProvocationByLawfulPrivateDefence}(Y) = \text{TRUE}$.
- **Deduction**:
  1. `RULE-BNS-101-CL-A` fires $\implies \text{PrimaFacieMurder}(X, Y) = \text{TRUE}$.
  2. `RULE-BNS-101-EXC-1` fires $\implies \text{Exception1}(X, Y) = \text{TRUE} \implies \text{ExceptedFromMurder}(X, Y) = \text{TRUE}$.
  3. `RULE-BNS-101-FINAL` is defeated ($\text{PrimaFacieMurder} \land \neg \text{Excepted}$ evaluates to $\text{FALSE}$).
  4. `RULE-BNS-101-MITIGATED` fires $\implies \text{CulpableHomicideNotAmountingToMurder}(X, Y) = \text{TRUE}$.
- **Output**: `STATUS = MITIGATED_DEFENCE_APPLIED`.

### Case 3: Proviso Defeating Exception
- **Facts**:
  - Offender $X$ voluntarily sought provocation from $Y$ as an excuse ($\text{ProvocationVoluntarilySought}(X) = \text{TRUE}$).
- **Deduction**:
  1. $\neg \text{ProvocationVoluntarilySought}(X)$ evaluates to $\text{FALSE}$.
  2. `RULE-BNS-101-EXC-1` antecedent evaluates to $\text{FALSE} \implies$ Exception 1 fails!
  3. Murder stands as `SUPPORTED`.

### Case 4: Open-World Incomplete Facts
- **Facts**: Scenario only states that $A$ struck $B$ and $B$ died. Intention is unmentioned.
- **Deduction**:
  - $\text{IntentionToCauseDeath}(A, B) = \text{UNKNOWN}$.
  - Engine reports: `STATUS = INSUFFICIENT_INFORMATION`.
  - Explanations list the exact missing premises: `['IntentionToCauseDeath(A, B)']`.

---

## 6. Full-Act Conversion Statistics

Running `python3 run_fol_pipeline.py` extracts formal rules across all **358 enacted sections**:

```
======================================================================
⚖️ FIRST-ORDER LOGIC (FOL) FORMALIZATION SUMMARY
======================================================================
Total Formal FOL Rules Generated : 1,281
Sections Covered                 : 358 (100.0%)

Formal Rule Distribution:
  - OFFENCE_ELEMENT         : 670
  - EXCEPTION_DEFENCE       : 26
  - EXCEPTION_OVERRIDE      : 5
  - OFFENCE_FINAL           : 1
  - OFFENCE_MITIGATED       : 1
  - PUNISHMENT_MAPPING      : 461
  - DEFINITIONAL_EXPANSION  : 117
======================================================================
```

---

## 6a. Formalisation Levels

Every rule carries `formalization_level`:

- **`GOLD`** (24 rules, Sections 101, 103, 318): hand-formalised over the typed ontology and **executed** by the verification engine.
- **`SCHEMATIC`** (1,257 rules, all other sections): auto-generated skeletons with placeholder predicates such as `Satisfies_Theft_1(x)`. They give full-Act coverage and provenance (each points to its KB component) but are **not executed**; refining a section means rewriting its rules as GOLD rules over ontology predicates.

The `formal_rules.csv` export includes a `formalization_level` column. Rule metadata also supports `trigger_premises` (what raises a defence) and `premise_notes` (legal notes shown when a premise is contradicted).

## 7. How to Run and Verify the Engine

### Run all Unit Tests (51 test cases)
```bash
python3 -m unittest discover tests
```

### Run Full FOL Conversion Pipeline
```bash
python3 run_fol_pipeline.py
```

### Inspect Output Files
- Primary JSONL: [`data/output/formal_rules.jsonl`](file:///Users/tharun/MR%20Project/data/output/formal_rules.jsonl)
- SpreadSheet CSV: [`data/output/formal_rules.csv`](file:///Users/tharun/MR%20Project/data/output/formal_rules.csv)
- Predicate Ontology: [`data/output/predicate_ontology.json`](file:///Users/tharun/MR%20Project/data/output/predicate_ontology.json)
