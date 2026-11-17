# Legal Reasoning and Verification Engine for Bharatiya Nyaya Sanhita (BNS), 2023

**Project**: Legal Reasoning Verification System  
**Stages**: Stage 5 (Verification Engine) & Stage 2 (Complex Legal Scenarios Evaluation)  
**Legal Domain**: Bharatiya Nyaya Sanhita, 2023 (Act No. 45 of 2023)  
**Deliverables**:
- `bns_verifier/engine.py` (Generic, rule-driven First-Order Logic verification engine)
- `bns_verifier/fact_extractor.py` (Optional LLM narrative → validated FOL facts)
- `bns_verifier/audit_trace.py` (Transparent reasoning trace and step logger)
- `bns_verifier/benchmark_runner.py` (Benchmark test runner across scenarios)
- `bns_verifier/llm_comparator.py` (Empirical comparator against standard LLM baselines)
- `bns_verifier/visualizer.py` (Interactive Google Colab / Jupyter visualizer)
- `run_verification_benchmark.py` (CLI tool to evaluate scenarios)
- `run_llm_comparison.py` (CLI tool to run side-by-side LLM vs. Verifier evaluation)
- `data/output/verification_audit_traces.jsonl` (Auditable step-by-step reasoning traces)
- `data/output/llm_vs_verifier_comparison.json` (Full comparison dataset)

---

## 1. Executive Summary & Research Problem

Standard Large Language Models (LLMs) answer legal queries by generating plausible-sounding natural language. In criminal law, this approach is fundamentally brittle because LLMs:
1. **Suffer from Closed-World Bias**: When facts are incomplete, LLMs assume unmentioned facts are false or rush to convict/acquit instead of recognizing missing information.
2. **Overlook Provisos (Proviso Blindness)**: When a statutory defence (e.g., *grave and sudden provocation*) is present, LLMs frequently grant the defence while missing the statutory proviso that explicitly cancels it (e.g., when the provocation was voluntarily provoked by the offender).
3. **Conflate Civil Breach with Crime**: LLMs routinely treat ordinary contract defaults as criminal fraud.
4. **Hallucinate Contradiction Resolutions**: When witnesses contradict forensic evidence, LLMs pick one side arbitrarily rather than identifying an evidentiary conflict.

The **Legal Verification Engine** replaces unconstrained language generation with **transparent, auditable First-Order Logic (FOL) deduction under the Open-World Assumption (3-Valued Kleene Logic)**.

---

## 2. Empirical Benchmark: LLM vs. Formal Verification Engine

We benchmarked two live LLM baselines against the **Formal Verification Engine** across the **20 curated BNS criminal law scenarios**. The LLM receives the narrative and the proposed charge and must return one of the verdicts.

| Verdict source | Correct | Source |
| :--- | :---: | :--- |
| Formal Verification Engine (hand-formalised facts) | **20/20** | `run_verification_benchmark.py` |
| gpt-4o-mini, direct verdict | 16/20 | `live:gpt-4o-mini` |
| gpt-4o, direct verdict | 18/20 | `live:gpt-4o` |

> **Source of the LLM verdicts.** Both runs are live (`--require-live`). Every record in `llm_vs_verifier_comparison*.json` carries an `llm_source` field (`live:<model>` or `offline_recorded`). The earlier pre-recorded `gpt-4o-mini` answers (11/20) remain in `bns_verifier/llm_comparator.py` only as an offline fallback and are labelled whenever they are used. Treat the comparison as an illustration of failure modes, not a definitive model evaluation: 20 cases, one prompt, and answers vary slightly between runs.

### Where the LLMs fail

**gpt-4o-mini**

| Scenario | Category | Ground truth | LLM verdict | Failure mode |
| :--- | :--- | :--- | :--- | :--- |
| `SCEN-BNS-008` | `PROVISO_OVERRIDE` | `SUPPORTED` | `MITIGATED_DEFENCE_APPLIED` | Proviso Blindness |
| `SCEN-BNS-009` | `PROVISO_OVERRIDE` | `SUPPORTED` | `MITIGATED_DEFENCE_APPLIED` | Proviso Blindness |
| `SCEN-BNS-010` | `PROVISO_OVERRIDE` | `SUPPORTED` | `MITIGATED_DEFENCE_APPLIED` | Proviso Blindness |
| `SCEN-BNS-015` | `CONTRADICTORY_FACTS` | `CONFLICTING` | `CONTRADICTED` | Hallucinated Resolution |

**gpt-4o**

| Scenario | Category | Ground truth | LLM verdict | Failure mode |
| :--- | :--- | :--- | :--- | :--- |
| `SCEN-BNS-007` | `STATUTORY_EXCEPTION` | `MITIGATED_DEFENCE_APPLIED` | `SUPPORTED` | Statutory Misinterpretation |
| `SCEN-BNS-015` | `CONTRADICTORY_FACTS` | `CONFLICTING` | `CONTRADICTED` | Hallucinated Resolution |

gpt-4o-mini misses every proviso trap (a defence granted although a proviso cancels it), and both models resolve the SCEN-015 contradiction instead of flagging it. The engine handles both patterns by construction. See §8 for the live narrative → facts → verdict experiment.

---

## 3. How the Verification Engine Works

The verification process follows a multi-stage deterministic pipeline:

```
+-----------------------------------------------------------------------+
|               Input Legal Scenario (Narrative + Formal Facts)         |
+-----------------------------------+-----------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                Stage 1: Evidentiary Contradiction Gate                |
|  - Checks if facts assert both P and ~P (e.g. Intent & ~Intent)       |
|  - If conflict exists -> HALT & Output: CONFLICTING                   |
+-----------------------------------+-----------------------------------+
                                    | No contradiction
                                    v
+-----------------------------------------------------------------------+
|         Stage 2: Scenario Fact Model (Open-World Valuation)           |
|  - Evaluates facts under 3-Valued Kleene Logic: {TRUE, FALSE, UNKNOWN}|
|  - Undeclared facts are strictly UNKNOWN (never assumed False)        |
+-----------------------------------+-----------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|             Stage 3: Primary Rule / Offence Evaluation                |
|  - Evaluates Prima Facie rule branches (e.g. Sec 101 Clauses a–d)    |
|  - If any element is missing -> Output: INSUFFICIENT_INFORMATION      |
|  - If elements contradicted -> Output: CONTRADICTED                   |
|  - If prima facie branch satisfied -> Proceed to Defences Gate        |
+-----------------------------------+-----------------------------------+
                                    | Prima Facie Established
                                    v
+-----------------------------------------------------------------------+
|             Stage 4: Defeasible Exception & Proviso Gate              |
|  - Evaluates statutory exceptions (Sec 101 Exceptions 1–5)            |
|  - For each claimed defence, evaluates statutory provisos:            |
|    * Proviso (a): Was provocation voluntarily sought?                 |
|    * Proviso (b): Was it by a public servant in lawful duty?          |
|    * Proviso (c): Was it in lawful private defence?                   |
|    * Proviso (Cruelty): Did offender take undue advantage?            |
|  - If a proviso is violated -> Exception is DEFEATED!                |
|  - If a valid defence holds -> Output: MITIGATED_DEFENCE_APPLIED      |
|  - If all defences are ruled out or defeated -> Output: SUPPORTED     |
+-----------------------------------+-----------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|               Stage 5: Transparent Audit Trace Generation             |
|  - Logs every rule evaluated, satisfied premises, and explanations   |
|  - Produces structured JSONL trace + human-readable visual report     |
+-----------------------------------------------------------------------+
```

---

## 4. Step-by-Step Scenario Traces Walkthrough

### Example 1: `SCEN-BNS-004` (Valid Statutory Exception)
- **Scenario**: $Y$ spat in $X$'s face and assaulted $X$'s child. $X$ killed $Y$ in sudden passion.
- **Trace Output**:
  - **Step 1 (`RULE-BNS-101-CL-A`)**:
    - $\checkmark$ Satisfied: `CausesDeath(X, Y)`, `IntentionToCauseDeath(X, Y)`.
    - $\hookrightarrow$ Deduced: `PrimaFacieMurder(X, Y)`.
  - **Step 2 (`RULE-BNS-101-EXC-1`)**:
    - $\checkmark$ Satisfied: `GraveAndSuddenProvocation(Y, X)`, `DeprivedOfSelfControl(X)`.
    - $\checkmark$ Provisos Absent: `~ProvocationVoluntarilySought(X)`, `~ProvocationByLawfulPublicServant(Y)`, `~ProvocationByLawfulPrivateDefence(Y)`.
    - $\hookrightarrow$ Deduced: `Exception1GraveSuddenProvocation(X, Y)`.
  - **Step 3 (`RULE-BNS-101-MITIGATED`)**:
    - Prima facie murder is established BUT Exception 1 applies.
    - Final Verdict: **`MITIGATED_DEFENCE_APPLIED`** (Mitigated to Culpable Homicide Not Amounting to Murder).

### Example 2: `SCEN-BNS-008` (Proviso Overriding Exception)
- **Scenario**: $A$ insulted $Z$ deliberately to provoke a slap as an excuse to shoot him.
- **Trace Output**:
  - **Step 1 (`RULE-BNS-101-CL-A`)**:
    - $\checkmark$ Satisfied: `CausesDeath(A, Z)`, `IntentionToCauseDeath(A, Z)`.
    - $\hookrightarrow$ Deduced: `PrimaFacieMurder(A, Z)`.
  - **Step 2 (`PROVISO-101-EXC-1-A`)**:
    - $\checkmark$ Satisfied: `ProvocationVoluntarilySought(A)`.
    - Defeated Exception: *Exception 1 (Barred by Proviso a: Provocation voluntarily sought)*.
  - **Step 3 (`RULE-BNS-101-FINAL`)**:
    - All exceptions defeated by statutory provisos.
    - Final Verdict: **`SUPPORTED`** (Murder liability stands!).

### Example 3: `SCEN-BNS-012` (Open-World Incomplete Information)
- **Scenario**: Vehicle collision causing death; intent unstated.
- **Trace Output**:
  - **Step 1 (`RULE-BNS-101-CL-A`)**:
    - $\checkmark$ Satisfied: `CausesDeath(A, B)`.
    - $?$ Missing / Unknown: `IntentionToCauseDeath(A, B)`.
  - Antecedent evaluates to $\text{UNKNOWN}$ under 3-valued logic.
  - Final Verdict: **`INSUFFICIENT_INFORMATION`** (Engine refuses to guess guilt or innocence).

---

## 5. How to Trace the Verification Engine in Google Colab

To interactively trace scenarios with visual color-coded cards and reasoning steps in Google Colab, copy and paste this single self-contained cell into your Colab notebook:

```python
# ==============================================================================
# BNS Verification Engine Interactive Tracer for Google Colab
# ==============================================================================
import sys
import os
from pathlib import Path

# Ensure project repository is imported
if not os.path.exists("bns_verifier"):
    print("Cloning/accessing project repository...")

from bns_scenarios.benchmark_suite import get_benchmark_scenarios
from bns_verifier.engine import LegalVerificationEngine
from bns_verifier.visualizer import render_trace_html
from IPython.display import HTML, display
import ipywidgets as widgets

scenarios = get_benchmark_scenarios()
scen_dict = {s.scenario_id: s for s in scenarios}
engine = LegalVerificationEngine()

scenario_options = [
    (f"[{s.scenario_id}] {s.title} ({s.category.value})", s.scenario_id)
    for s in scenarios
]

def trace_scenario(scenario_id="SCEN-BNS-004"):
    sc = scen_dict.get(scenario_id)
    if not sc:
        print("Scenario not found.")
        return
    trace = engine.verify_scenario(sc)
    html_output = render_trace_html(trace, sc)
    display(HTML(html_output))

# Interactive Dropdown Widget
dropdown = widgets.Dropdown(
    options=scenario_options,
    value="SCEN-BNS-004",
    description="Select Scenario:",
    style={"description_width": "initial"},
    layout=widgets.Layout(width="70%")
)

widgets.interact(trace_scenario, scenario_id=dropdown)
```

### Try These 3 Key Scenarios in the Dropdown:
1. **`SCEN-BNS-004` (Exception 1)**: See how the engine evaluates sudden provocation and mitigates murder to culpable homicide.
2. **`SCEN-BNS-008` (Proviso a Override)**: See how Proviso (a) triggers and defeats the provocation defence because it was voluntarily sought.
3. **`SCEN-BNS-012` (Missing Intent)**: See how the Open-World evaluator identifies missing mental elements and outputs `INSUFFICIENT_INFORMATION`.

---

## 6. How to Run the Verification Engine from Terminal

### Run Verification Benchmark across all 20 Scenarios
```bash
python3 run_verification_benchmark.py
```

### Run Side-by-Side LLM vs. Verifier Comparison
```bash
python3 run_llm_comparison.py
```

### Run Unit Tests
```bash
python3 -m unittest discover tests
```

---

## 7. Engine v2: Generic, Rule-Driven Reasoning

The engine no longer contains section-specific branches. Every step is driven by the `StatutoryRule` data and the predicate ontology, so adding a correctly typed GOLD rule extends the engine without code changes.

| Stage | Driven by | Outcome |
| :--- | :--- | :--- |
| Contradiction gate | Facts asserting `P` and `~P` | `CONFLICTING` |
| Open-world fact model | Facts (atoms canonicalised, so `P(A,B)` = `P(A, B)`) | Unstated atoms are `UNKNOWN` |
| Definitional expansion | `DEFINITIONAL_EXPANSION` rules, forward-chained to a fixpoint | e.g. concealment ⇒ `Deceives` |
| Defeasible offence | An `OFFENCE_FINAL` rule concludes the proposed predicate | Prima facie routes, then **raised** exceptions |
| Provisos | Negated premises whose predicate category is `PROVISO` | Named `PROVISO-…` step; defence defeated |
| Strict conclusion | Any other rule concludes the predicate (e.g. `Cheats`, `Exception5Consent`) | TRUE / UNKNOWN / FALSE route |
| Out of scope | No GOLD rule concludes the predicate | `OUT_OF_SCOPE` (new verdict) |
| Sanctions | `PUNISHMENT_MAPPING` rules after a supported offence | `applicable_sanctions` (incl. 103(2), 318(3), 318(4)) |

**Raised defences.** An exception is examined once its trigger premise is TRUE (the first premise, or `trigger_premises` on the rule; Exception 5 is triggered by the victim's consent). A raised defence whose conditions or provisos are still `UNKNOWN` makes `¬ExceptedFromMurder` UNKNOWN, so the verdict is `INSUFFICIENT_INFORMATION` with the missing proviso facts listed (`unresolved_exceptions`). Defences that are never raised are treated as absent, mirroring the accused's evidential burden.

**What changed compared with v1**

- All five exceptions are evaluated (v1 never checked Exception 3).
- Unknown provisos no longer let murder through as `SUPPORTED`.
- Section 103(2) now requires `Murder(x, y)`; penalty and aggravation rules are executed (benchmark: expected punishment derived in 10/10 supported scenarios).
- A conclusion outside the formalised sections returns `OUT_OF_SCOPE` instead of a default `SUPPORTED`.
- Facts are checked against the ontology (`fact_warnings` for unknown predicates or wrong arity).
- Only rules with `formalization_level == "GOLD"` are executed; the 1,257 auto-generated template rules are marked `SCHEMATIC`.
- Legal notes live in the rule data (`premise_notes`), e.g. the Section 318 Illustration (g) civil-breach explanation.

### Closing the neuro-symbolic loop (needs `OPENAI_API_KEY`)

`bns_verifier/fact_extractor.py` asks an LLM to translate a narrative into facts over the ontology, and `NeuroSymbolicPipeline` passes them to the engine. Every proposal is validated deterministically: known predicate, correct arity, person arguments must be declared actors, and **legal conclusions (Murder, Cheats, LiableToPunishment, …) are rejected**. Three modes are compared:

| Mode | What it does |
| :--- | :--- |
| `baseline` | One call; plain list of literals. |
| `grounded` | Each literal needs a **verbatim evidence quote**, checked against the narrative; the prompt shows **argument roles** (`ARG_ROLES` in the ontology, e.g. `GraveAndSuddenProvocation(provoker, accused)`); `Person(actor)` facts are added deterministically; constants are normalised. Two **evidence guards** reject quotes that report uncertainty ("age remains unknown") and negated facts whose quote has no negation. |
| `loop` | `grounded`, then up to two **engine-guided clarification rounds**: while the verdict is `INSUFFICIENT_INFORMATION`, the engine's `missing_facts` become targeted TRUE / FALSE / UNKNOWN questions, each answer needing its own quote. Answers can add atoms but never flip a known one. |

## 8. Live Results: Narrative → Facts → Verdict

All runs live, temperature 0, 20 scenarios. *Unsafe SUPPORTED* = the pipeline convicts where the ground truth is not `SUPPORTED`.

| Model | Mode | Precision | Recall | F1 | Verdict correct | Unsafe SUPPORTED | LLM calls |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| gpt-4o-mini | baseline | 0.58 | 0.60 | 0.54 | **9/20** | 0 | 20 |
| gpt-4o-mini | grounded | 0.85 | 0.69 | 0.75 | **10/20** | 0 | 20 |
| gpt-4o-mini | loop | 0.72 | 0.75 | 0.71 | **15/20** | 0 | 37 |
| gpt-4o | baseline | 0.85 | 0.78 | 0.80 | **10/20** | 0 | 20 |
| gpt-4o | grounded | 0.90 | 0.80 | 0.84 | **12/20** | 1 | 20 |
| gpt-4o | loop | 0.83 | 0.82 | 0.81 | **13/20** | 2 | 33 |

- **Grounding raises fact precision**; requiring a quote removes invented facts.
- **The engine-guided loop gives the largest end-to-end gain**: the engine's missing-facts list turns into targeted questions.
- **The remaining errors are polarity mistakes** (e.g. "deprived of self-control" read as *no intention to kill*). With hand-formalised facts the engine is 20/20, so fact extraction is the bottleneck.
- A stronger extractor (gpt-4o) produces more accurate facts but is not automatically safer: one missed negation can flip a verdict.

### Agreement triage (`bns_verifier/hybrid.py`)

The direct LLM verdict and the loop pipeline fail on different cases. Accepting a verdict automatically only when both agree, and routing disagreements to a human:

| Model | Loop alone | Direct LLM alone | Auto-accepted (coverage) | Correct when auto-accepted | Unsafe auto-accepted |
| :--- | :---: | :---: | :---: | :---: | :---: |
| gpt-4o-mini | 15/20 | 16/20 | 11 (55.0%) | **11/11** | 0 |
| gpt-4o | 13/20 | 18/20 | 12 (60.0%) | **12/12** | 0 |

```bash
python run_llm_comparison.py --require-live --model gpt-4o-mini
python run_llm_comparison.py --require-live --model gpt-4o            # then copy to *_gpt-4o.json
python run_fact_extraction.py                                          # baseline, grounded, loop
python run_fact_extraction.py --model gpt-4o --out data/output/fact_extraction_eval_gpt-4o.json
python run_fact_extraction.py --modes loop --scenario SCEN-BNS-008
python run_hybrid_analysis.py                                          # triage from saved results, no API calls
```

> Caveats: 20 self-authored cases; results vary by ±1–2 cases between runs even at temperature 0; the extraction rules were written while inspecting these same narratives, so held-out scenarios are needed before claiming generalisation.
