"""
Generic, rule-driven Legal Reasoning and Verification Engine for Bharatiya Nyaya Sanhita (BNS) 2023.

The engine contains no section-specific branches. Its behaviour is driven entirely by the
StatutoryRule data (rule types, premises, conclusions) and the predicate ontology:

  1. Evidentiary contradiction gate      P and ~P both asserted                -> CONFLICTING
  2. Open-world fact model (Kleene K3)   unstated atoms are UNKNOWN
  3. Definitional expansions             DEFINITIONAL_EXPANSION rules forward-chained to a fixpoint
  4. Dispatch on the proposed conclusion
     a. Defeasible offence  (an OFFENCE_FINAL rule concludes it, e.g. Murder):
          prima facie routes (OFFENCE_ELEMENT)      none TRUE -> INSUFFICIENT_INFORMATION / CONTRADICTED
          raised exceptions (EXCEPTION_DEFENCE)     provisos (PROVISO-category negated premises) checked first
              valid exception                       -> MITIGATED_DEFENCE_APPLIED
              raised but unresolved                 -> INSUFFICIENT_INFORMATION
              none surviving                        -> SUPPORTED (via the OFFENCE_FINAL rule)
     b. Strict conclusion (any other rule concludes it, e.g. Cheats, Exception5Consent):
          some route TRUE -> SUPPORTED; some UNKNOWN -> INSUFFICIENT_INFORMATION; all FALSE -> CONTRADICTED
     c. No executable rule concludes it      -> OUT_OF_SCOPE
  5. Sanctions                            PUNISHMENT_MAPPING rules evaluated for a supported offence

Only GOLD rules are executed; SCHEMATIC template rules are ignored.

A note on defences: an exception is examined once it is *raised*, i.e. its trigger premise(s) are TRUE
(by default the first premise; see StatutoryRule.trigger_premises). This mirrors the evidential burden
on the accused to raise a defence. Defences that are never raised are treated as absent, which is what
allows the final rule PrimaFacie ∧ ¬Excepted -> Offence to fire.
"""
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from bns_scenarios.schema import LegalScenario, LegalVerdict
from bns_verifier.audit_trace import ReasoningStep, VerificationAuditTrace
from bns_fol.ontology.signatures import PREDICATE_REGISTRY, PredicateSignature
from bns_fol.rules.pilot_rules import get_pilot_rules
from bns_fol.rules.schema import StatutoryRule
from bns_fol.semantics.model import ScenarioFactModel, canonical_atom, format_atom, parse_literal
from bns_fol.semantics.truth_values import TruthValue

T, F, U = TruthValue.TRUE, TruthValue.FALSE, TruthValue.UNKNOWN
_RANK = {T: 0, U: 1, F: 2}
_MAX_BINDINGS = 256


def _pred(literal: str) -> str:
    return parse_literal(literal)[1]


def _is_neg(literal: str) -> bool:
    return parse_literal(literal)[0]


def _dedup(items: List[str]) -> List[str]:
    return list(dict.fromkeys(items))


@dataclass
class RuleEval:
    rule: StatutoryRule
    value: TruthValue
    satisfied: List[str]
    missing: List[str]
    contradicted: List[str]
    binding: Dict[str, str]
    conclusion: str
    notes: List[str] = field(default_factory=list)


@dataclass
class _Run:
    """Mutable state for one verification run."""
    scenario: LegalScenario
    model: ScenarioFactModel
    steps: List[ReasoningStep] = field(default_factory=list)
    rules_used: List[str] = field(default_factory=list)
    applied: List[str] = field(default_factory=list)
    defeated: List[str] = field(default_factory=list)
    unresolved: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class LegalVerificationEngine:
    """
    Evaluates scenario facts against GOLD statutory First-Order Logic rules under three-valued
    open-world semantics, resolving defeasible exceptions, provisos, missing information and sanctions.
    """

    def __init__(
        self,
        rules: Optional[List[StatutoryRule]] = None,
        ontology: Optional[Dict[str, PredicateSignature]] = None,
    ):
        all_rules = rules if rules is not None else get_pilot_rules()
        self.rules: List[StatutoryRule] = [r for r in all_rules if r.formalization_level == "GOLD"]
        self.ignored_schematic_rules = len(all_rules) - len(self.rules)
        self.ontology = ontology or PREDICATE_REGISTRY
        self.rules_by_id = {r.rule_id: r for r in self.rules}
        self.by_conclusion: Dict[str, List[StatutoryRule]] = defaultdict(list)
        for r in self.rules:
            self.by_conclusion[_pred(r.conclusion)].append(r)

    # =====================================================================================
    # Public API
    # =====================================================================================
    def verify_scenario(self, scenario: LegalScenario) -> VerificationAuditTrace:
        warnings = self._check_facts_against_ontology(scenario.facts)

        # ---- Gate 1: evidentiary contradiction -------------------------------------------
        pos, neg = set(), set()
        for f in scenario.facts:
            is_neg, pred, args = parse_literal(f)
            (neg if is_neg else pos).add(format_atom(pred, args))
        conflicts = sorted(pos & neg)
        if conflicts:
            conflicting = [f"{c} vs ~{c}" for c in conflicts]
            step = ReasoningStep(
                step_number=1, rule_id="CONTRADICTION_GATE", rule_name="Evidentiary Conflict Detection",
                rule_type="VALIDATION", premises_satisfied=[], premises_missing=[],
                premises_contradicted=conflicting,
                step_explanation="Scenario contains mutually contradictory premises. Reasoning halted."
            )
            return VerificationAuditTrace(
                scenario_id=scenario.scenario_id, scenario_title=scenario.title,
                target_sections=scenario.target_sections, proposed_conclusion=scenario.proposed_conclusion,
                computed_verdict=LegalVerdict.CONFLICTING, ground_truth_verdict=scenario.ground_truth_verdict,
                verdict_matches_ground_truth=(scenario.ground_truth_verdict == LegalVerdict.CONFLICTING),
                applicable_rules=[], reasoning_steps=[step], conflicting_facts=conflicting,
                fact_warnings=warnings,
                final_legal_explanation=f"Contradictory evidence detected in premises: {', '.join(conflicting)}."
            )

        # ---- Gate 2: open-world fact model -----------------------------------------------
        model = ScenarioFactModel(scenario.title)
        for f in scenario.facts:
            model.add_fact(f, value=T, source="Scenario Narrative")
        run = _Run(scenario=scenario, model=model, warnings=warnings)

        # ---- Gate 3: definitional expansions ---------------------------------------------
        self._apply_definitional_expansions(run)

        # ---- Gate 4: dispatch on the proposed conclusion ---------------------------------
        _, pred, args = parse_literal(scenario.proposed_conclusion)
        finals = [r for r in self.by_conclusion.get(pred, []) if r.rule_type == "OFFENCE_FINAL"]
        if finals:
            verdict, explanation = self._verify_defeasible_offence(run, finals[0], args)
        elif self.by_conclusion.get(pred):
            verdict, explanation = self._verify_strict_conclusion(run, pred, args)
        else:
            verdict = LegalVerdict.OUT_OF_SCOPE
            explanation = (
                f"No executable (GOLD) rule concludes '{pred}'. The engine currently reasons over the "
                f"hand-formalised sections ({', '.join(str(s) for s in sorted({r.section_number for r in self.rules}))}); "
                f"this conclusion is outside that scope, so no verdict is given."
            )

        # ---- Gate 5: sanctions -------------------------------------------------------------
        sanctions: List[str] = []
        if verdict == LegalVerdict.SUPPORTED and args:
            sanctions = self._derive_sanctions(run, accused=args[0])
            if sanctions:
                explanation += f" Applicable sanction(s): {'; '.join(sanctions)}."
        expected = scenario.expected_punishment
        sanction_match = (canonical_atom(expected) in sanctions) if (expected and verdict == LegalVerdict.SUPPORTED) else None

        return VerificationAuditTrace(
            scenario_id=scenario.scenario_id, scenario_title=scenario.title,
            target_sections=scenario.target_sections, proposed_conclusion=scenario.proposed_conclusion,
            computed_verdict=verdict, ground_truth_verdict=scenario.ground_truth_verdict,
            verdict_matches_ground_truth=(verdict == scenario.ground_truth_verdict),
            applicable_rules=_dedup(run.rules_used), reasoning_steps=run.steps,
            applied_exceptions=run.applied, defeated_exceptions=run.defeated,
            missing_facts=_dedup(run.missing), conflicting_facts=[],
            unresolved_exceptions=run.unresolved, applicable_sanctions=sanctions,
            sanction_matches_expected=sanction_match, fact_warnings=run.warnings,
            final_legal_explanation=explanation
        )

    # =====================================================================================
    # Reasoning procedures
    # =====================================================================================
    def _apply_definitional_expansions(self, run: _Run) -> None:
        """Forward-chains DEFINITIONAL_EXPANSION rules until no new fact is derived."""
        expansions = [r for r in self.rules if r.rule_type == "DEFINITIONAL_EXPANSION"]
        changed = True
        while changed:
            changed = False
            for r in expansions:
                for b in self._bindings(r, run.model, {}):
                    ev = self._eval(r, run.model, b)
                    if ev.value == T and run.model.evaluate_literal(ev.conclusion) != T:
                        self._record(run, ev, explanation=f"Definitional expansion: {ev.conclusion} follows from {', '.join(ev.satisfied)}.")
                        run.model.add_fact(ev.conclusion, source=f"Deduced from {r.rule_id}")
                        run.rules_used.append(r.rule_id)
                        changed = True

    def _verify_defeasible_offence(self, run: _Run, final_rule: StatutoryRule, args: List[str]) -> Tuple[LegalVerdict, str]:
        model = run.model
        base = self._unify(final_rule.conclusion, args, final_rule)
        if base is None:
            return LegalVerdict.OUT_OF_SCOPE, f"Proposed conclusion does not match the form of {final_rule.conclusion}."
        offence_atom = model.get_ground_atom(final_rule.conclusion, base)
        pf_literal = next(p for p in final_rule.premises if not _is_neg(p))
        ex_literal = next((p for p in final_rule.premises if _is_neg(p)), None)
        pf_atom = model.get_ground_atom(pf_literal, base)
        pf_args = parse_literal(pf_atom)[2]

        # ---- Prima facie routes -------------------------------------------------------------
        routes = [r for r in self.by_conclusion.get(_pred(pf_literal), []) if r.rule_type == "OFFENCE_ELEMENT"]
        established: Optional[RuleEval] = None
        missing, contradicted = [], []
        for r in routes:
            ev = self._best(r, model, self._unify(r.conclusion, pf_args, r) or {})
            self._record(run, ev)
            if ev.value == T:
                established = ev
                run.rules_used.append(r.rule_id)
                model.add_fact(ev.conclusion, source=f"Deduced from {r.rule_id}")
                break
            (missing if ev.value == U else contradicted).extend(ev.missing if ev.value == U else ev.contradicted)

        if not established:
            if missing:
                run.missing.extend(missing)
                return LegalVerdict.INSUFFICIENT_INFORMATION, (
                    f"Cannot establish {pf_atom}: no statutory route is complete. "
                    f"Missing factual evidence for elements ({', '.join(_dedup(missing))})."
                )
            return LegalVerdict.CONTRADICTED, (
                f"{pf_atom} is negated: every statutory route fails on a premise proven false "
                f"({', '.join(_dedup(contradicted))}), so {offence_atom} cannot hold."
            )

        if ex_literal is None:
            return self._conclude_final(run, final_rule, base, established, offence_atom)

        # ---- Raised exceptions and their provisos ------------------------------------------------
        ex_atom = model.get_ground_atom(ex_literal, base)
        ex_args = parse_literal(ex_atom)[2]
        overrides = [r for r in self.by_conclusion.get(_pred(ex_literal), []) if r.rule_type == "EXCEPTION_OVERRIDE"]
        exception_preds = _dedup([_pred(o.premises[0]) for o in overrides])
        exceptions = [r for p in exception_preds for r in self.by_conclusion.get(p, []) if r.rule_type == "EXCEPTION_DEFENCE"]

        unresolved_missing: List[str] = []
        for r in exceptions:
            b = self._unify(r.conclusion, ex_args, r) or {}
            triggers = r.trigger_premises or [next(p for p in r.premises if not _is_neg(p))]
            if not all(model.evaluate_literal(t, b) == T for t in triggers):
                continue  # defence not raised

            provisos = [p for p in r.premises if _is_neg(p) and self._category(p) == "PROVISO"]
            triggered = [(i, p) for i, p in enumerate(provisos) if model.evaluate_literal(p, b) == F]
            if triggered:
                letters = [chr(ord("a") + i) for i, _ in triggered] if len(provisos) > 1 else []
                atoms = [model.get_ground_atom(p, b) for _, p in triggered]
                label = f"Proviso {', '.join(letters)}" if letters else "Proviso"
                step_id = r.rule_id.replace("RULE-BNS-", "PROVISO-") + (f"-{''.join(l.upper() for l in letters)}" if letters else "")
                run.defeated.append(f"{r.rule_name} (Barred by {label}: {', '.join(atoms)})")
                run.steps.append(ReasoningStep(
                    step_number=len(run.steps) + 1, rule_id=step_id, rule_name=f"{label} Override",
                    rule_type="PROVISO_OVERRIDE", premises_satisfied=atoms, premises_missing=[],
                    premises_contradicted=[],
                    step_explanation=f"{', '.join(atoms)} holds, so the proviso to {r.rule_name.split(':')[0]} applies and the defence is defeated."
                ))
                continue

            ev = self._best(r, model, b)
            self._record(run, ev)
            if ev.value == T:
                run.applied.append(r.rule_name)
                run.rules_used.append(r.rule_id)
                model.add_fact(ev.conclusion, source=f"Deduced from {r.rule_id}")
                for o in overrides:
                    if _pred(o.premises[0]) == _pred(r.conclusion):
                        oev = self._best(o, model, self._unify(o.conclusion, ex_args, o) or {})
                        if oev.value == T:
                            self._record(run, oev)
                            run.rules_used.append(o.rule_id)
                            model.add_fact(oev.conclusion, source=f"Deduced from {o.rule_id}")
            elif ev.value == U:
                run.unresolved.append(r.rule_name)
                unresolved_missing.extend(ev.missing)

        pf_name = established.rule.rule_name
        if run.applied:
            for m in self.rules:
                if m.rule_type == "OFFENCE_MITIGATED" and _pred(pf_literal) in map(_pred, m.premises):
                    mev = self._best(m, model, self._unify(m.premises[0], pf_args, m) or {})
                    if mev.value == T:
                        self._record(run, mev)
                        run.rules_used.append(m.rule_id)
                        model.add_fact(mev.conclusion, source=f"Deduced from {m.rule_id}")
            return LegalVerdict.MITIGATED_DEFENCE_APPLIED, (
                f"Prima facie {_pred(final_rule.conclusion).lower()} established under {pf_name}, "
                f"BUT statutory defence applied: {', '.join(run.applied)}. "
                f"{_pred(final_rule.conclusion)} is defeated and mitigated to Culpable Homicide Not Amounting to Murder."
                if _pred(final_rule.conclusion) == "Murder" else
                f"Prima facie offence established under {pf_name}, BUT statutory defence applied: {', '.join(run.applied)}."
            )

        if run.unresolved:
            run.missing.extend(unresolved_missing)
            return LegalVerdict.INSUFFICIENT_INFORMATION, (
                f"Prima facie elements established under {pf_name}, but the raised defence(s) "
                f"{', '.join(run.unresolved)} cannot be resolved: missing ({', '.join(_dedup(unresolved_missing))}). "
                f"Under three-valued logic ¬{ex_atom} is UNKNOWN, so {offence_atom} cannot be concluded."
            )

        # No surviving exception: close ExceptedFrom… as FALSE and fire the final rule.
        model.add_fact(f"~{ex_atom}", source="No statutory exception raised, or every raised exception was defeated or failed")
        return self._conclude_final(run, final_rule, base, established, offence_atom)

    def _conclude_final(self, run: _Run, final_rule: StatutoryRule, base: Dict[str, str],
                        established: RuleEval, offence_atom: str) -> Tuple[LegalVerdict, str]:
        ev = self._best(final_rule, run.model, base)
        self._record(run, ev)
        run.rules_used.append(final_rule.rule_id)
        run.model.add_fact(ev.conclusion, source=f"Deduced from {final_rule.rule_id}")
        defeated = f" ({', '.join(run.defeated)})" if run.defeated else ""
        return LegalVerdict.SUPPORTED, (
            f"{_pred(final_rule.conclusion)} fully supported under Section {final_rule.section_number} "
            f"({established.rule.rule_name}). All prima facie elements proven; no statutory exceptions apply{defeated}."
        )

    def _verify_strict_conclusion(self, run: _Run, pred: str, args: List[str]) -> Tuple[LegalVerdict, str]:
        model = run.model
        candidates = [r for r in self.by_conclusion[pred] if self._unify(r.conclusion, args, r) is not None]
        if not candidates:
            return LegalVerdict.OUT_OF_SCOPE, f"No executable rule concludes '{pred}' with {len(args)} argument(s)."
        target = format_atom(pred, args)
        missing, contradicted, notes = [], [], []
        for r in candidates:
            ev = self._best(r, model, self._unify(r.conclusion, args, r))
            self._record(run, ev)
            if ev.value == T:
                run.rules_used.append(r.rule_id)
                model.add_fact(ev.conclusion, source=f"Deduced from {r.rule_id}")
                return LegalVerdict.SUPPORTED, (
                    f"{target} is supported under {r.rule_name} (Section {r.section_number}): "
                    f"all premises proven ({', '.join(ev.satisfied)})."
                )
            run.rules_used.append(r.rule_id)
            if ev.value == U:
                missing.extend(ev.missing)
            else:
                contradicted.extend(ev.contradicted)
                notes.extend(ev.notes)
        if missing:
            run.missing.extend(missing)
            return LegalVerdict.INSUFFICIENT_INFORMATION, (
                f"Cannot establish {target}: missing essential elements ({', '.join(_dedup(missing))})."
            )
        note_txt = f" {' '.join(_dedup(notes))}" if notes else ""
        return LegalVerdict.CONTRADICTED, (
            f"{target} is contradicted: every statutory route fails on a premise proven false "
            f"({', '.join(_dedup(contradicted))}).{note_txt}"
        )

    def _derive_sanctions(self, run: _Run, accused: str) -> List[str]:
        sanctions: List[str] = []
        for r in self.rules:
            if r.rule_type != "PUNISHMENT_MAPPING":
                continue
            c_args = parse_literal(r.conclusion)[2]
            base = {c_args[0]: accused} if c_args and c_args[0] in r.variables else {}
            ev = self._best(r, run.model, base)
            if ev.value == T:
                self._record(run, ev, explanation=f"Sanction rule fires: {ev.conclusion}.")
                run.rules_used.append(r.rule_id)
                sanctions.append(ev.conclusion)
        return _dedup(sanctions)

    # =====================================================================================
    # Evaluation primitives
    # =====================================================================================
    def _unify(self, rule_literal: str, args: List[str], rule: StatutoryRule) -> Optional[Dict[str, str]]:
        """Binds the variables of a rule literal (usually its conclusion) to the given ground arguments."""
        r_args = parse_literal(rule_literal)[2]
        if len(r_args) != len(args):
            return None
        b: Dict[str, str] = {}
        for ra, ga in zip(r_args, args):
            if ra in rule.variables:
                if b.get(ra, ga) != ga:
                    return None
                b[ra] = ga
            elif ra != ga:
                return None
        return b

    def _bindings(self, rule: StatutoryRule, model: ScenarioFactModel, base: Dict[str, str]) -> List[Dict[str, str]]:
        """
        Enumerates bindings for variables not fixed by `base` (e.g. the property p in cheating or the
        group g in Section 103(2)) by matching premises against known facts. Variables that no fact
        can bind stay unbound, so their premises evaluate to UNKNOWN.
        """
        results = [dict(base)]
        for prem in rule.premises:
            _, pred, p_args = parse_literal(prem)
            if not any(a in rule.variables for a in p_args):
                continue
            nxt = []
            for b in results:
                if all(a in b for a in p_args if a in rule.variables):
                    nxt.append(b)
                    continue
                matched = False
                for f_args, _val in model.facts_for(pred):
                    if len(f_args) != len(p_args):
                        continue
                    nb, ok = dict(b), True
                    for pa, fa in zip(p_args, f_args):
                        if pa in rule.variables:
                            if nb.setdefault(pa, fa) != fa:
                                ok = False
                                break
                        elif pa != fa:
                            ok = False
                            break
                    if ok:
                        nxt.append(nb)
                        matched = True
                if not matched:
                    nxt.append(b)
            seen, results = set(), []
            for b in nxt:
                key = tuple(sorted(b.items()))
                if key not in seen:
                    seen.add(key)
                    results.append(b)
            results = results[:_MAX_BINDINGS]
        return results

    def _eval(self, rule: StatutoryRule, model: ScenarioFactModel, binding: Dict[str, str]) -> RuleEval:
        disp = {v: binding.get(v, f"?{v}") for v in rule.variables}
        sat, miss, con, notes = [], [], [], []
        value = T
        for p in rule.premises:
            val = model.evaluate_literal(p, disp)
            is_neg, ground = model.ground(p, disp)
            shown = f"~{ground}" if is_neg else ground
            if val == T:
                sat.append(shown)
            elif val == F:
                con.append(shown)
                if p in rule.premise_notes:
                    notes.append(rule.premise_notes[p])
            else:
                miss.append(shown)
            value = value & val
        return RuleEval(rule, value, sat, miss, con, disp, model.get_ground_atom(rule.conclusion, disp), notes)

    def _best(self, rule: StatutoryRule, model: ScenarioFactModel, base: Dict[str, str]) -> RuleEval:
        evals = [self._eval(rule, model, b) for b in self._bindings(rule, model, base)]
        return min(evals, key=lambda e: (_RANK[e.value], len(e.missing)))

    def _record(self, run: _Run, ev: RuleEval, explanation: Optional[str] = None) -> None:
        state = {T: "TRUE", F: "FALSE", U: "UNKNOWN"}[ev.value]
        run.steps.append(ReasoningStep(
            step_number=len(run.steps) + 1, rule_id=ev.rule.rule_id, rule_name=ev.rule.rule_name,
            rule_type=ev.rule.rule_type, premises_satisfied=ev.satisfied, premises_missing=ev.missing,
            premises_contradicted=ev.contradicted, deduced_fact=ev.conclusion if ev.value == T else None,
            step_explanation=explanation or (
                f"Rule {ev.rule.rule_id} antecedent evaluates to {state} under three-valued logic"
                + (f"; deduced {ev.conclusion}." if ev.value == T else ".")
            )
        ))

    def _category(self, literal: str) -> Optional[str]:
        sig = self.ontology.get(_pred(literal))
        return sig.category if sig else None

    def _check_facts_against_ontology(self, facts: List[str]) -> List[str]:
        warnings = []
        for f in facts:
            _, pred, args = parse_literal(f)
            sig = self.ontology.get(pred)
            if sig is None:
                warnings.append(f"{f.strip()}: predicate '{pred}' is not in the ontology, so no rule can use it")
            elif sig.arity != len(args):
                warnings.append(f"{f.strip()}: '{pred}' expects {sig.arity} argument(s) but got {len(args)}")
        return warnings
