"""
Natural-Language -> First-Order Fact Extraction (the "neural" half of the neuro-symbolic loop).

An LLM reads a scenario narrative and proposes ground literals over the typed predicate ontology.
Every proposal is then checked deterministically before the verification engine sees it:

  * the predicate must exist in the ontology and be used with the right arity;
  * PERSON-typed arguments must be one of the scenario's declared actors;
  * derived legal conclusions (PrimaFacieMurder, Murder, Cheats, LiableToPunishment, ...) are rejected,
    because the extractor must report facts, never the verdict the engine is meant to check;
  * (grounded mode) every fact must cite a verbatim quote that really occurs in the narrative.

Three extraction strategies are provided and compared by run_fact_extraction.py:

  baseline  one LLM call returning a plain list of literals (no evidence required);
  grounded  one LLM call; each literal needs an evidence quote, checked against the narrative;
            Person(actor) facts are added deterministically and constants are normalised;
  loop      grounded extraction, then an engine-guided clarification loop: while the verdict is
            INSUFFICIENT_INFORMATION, the engine's missing facts are turned into targeted
            TRUE / FALSE / UNKNOWN questions, whose grounded answers are added before re-verifying.

Unmentioned facts must simply be omitted (open-world assumption); explicitly negated facts use '~'.
A live call requires OPENAI_API_KEY (or an injected client, which the unit tests use).
"""
import json
import os
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

from bns_fol.ontology.signatures import PREDICATE_REGISTRY, PredicateSignature
from bns_fol.ontology.types import LegalType
from bns_fol.rules.pilot_rules import get_pilot_rules
from bns_fol.semantics.model import format_atom, parse_literal
from bns_scenarios.schema import LegalScenario, LegalVerdict

MODES = ("baseline", "grounded", "loop")


def derived_predicates(rules=None) -> Set[str]:
    """Predicates that only the reasoning engine may conclude (never accepted as extracted facts)."""
    rules = rules or get_pilot_rules()
    conc = lambda r: parse_literal(r.conclusion)[1]
    derived = {conc(r) for r in rules if r.rule_type in ("OFFENCE_FINAL", "OFFENCE_MITIGATED", "EXCEPTION_OVERRIDE",
                                                          "PUNISHMENT_MAPPING", "EXCEPTION_DEFENCE")}
    element_premises = {parse_literal(p)[1] for r in rules if r.rule_type == "OFFENCE_ELEMENT" for p in r.premises}
    derived |= {conc(r) for r in rules if r.rule_type == "OFFENCE_ELEMENT" and conc(r) not in element_premises}
    return derived


def normalise_constant(value: str) -> str:
    """'religious community' -> 'ReligiousCommunity', '₹50Lakh' -> '50Lakh' (non-person constants only)."""
    words = re.findall(r"[A-Za-z0-9]+", value)
    if not words:
        return value.strip()
    return "".join(w[0].upper() + w[1:] for w in words)


def _norm_text(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", s.lower())).strip()


def is_grounded(quote: str, narrative: str, threshold: float = 0.85) -> bool:
    """True when `quote` occurs in the narrative (case/punctuation-insensitive, small typos tolerated)."""
    q, n = _norm_text(quote or ""), _norm_text(narrative)
    if len(q) < 4:
        return False
    if q in n:
        return True
    # tolerate light paraphrase (dropped/changed words) but not invented text
    matched = sum(b.size for b in SequenceMatcher(None, q, n, autojunk=False).get_matching_blocks() if b.size >= 3)
    return matched / len(q) >= threshold


_UNCERTAINTY_CUES = re.compile(
    r"\b(unknown|unclear|uncertain|unproven|not proven|not established|silent|no proof|no evidence|"
    r"cannot be determined|undetermined|unverified|remains? unknown)\b", re.I)
_NEGATION_CUES = re.compile(
    r"\b(not|no|never|without|absence|absent|lack|lacked|lacking|nor|neither|none|denied|n't)\b|n't\b", re.I)


def evidence_check(literal: str, quote: str) -> Optional[str]:
    """Deterministic polarity guard on the cited evidence. Returns a rejection reason or None.

    * A quote that reports uncertainty ('age remains unknown', 'records are silent') cannot establish a
      literal either way: under the open-world assumption the atom must stay UNKNOWN.
    * A negated literal needs a negation cue in its quote; otherwise the LLM has inferred a negative
      from text that does not state one (e.g. reading 'deprived of self-control' as 'no intention').
    """
    if _UNCERTAINTY_CUES.search(quote or ""):
        return "evidence reports uncertainty, so the atom stays UNKNOWN (open world)"
    if literal.strip().startswith(("~", "¬")) and not _NEGATION_CUES.search(quote or ""):
        return "negated fact, but the evidence quote contains no negation"
    return None


class ExtractionResult(BaseModel):
    accepted: List[str] = Field(default_factory=list, description="Validated ground literals")
    rejected: List[Dict[str, str]] = Field(default_factory=list, description="Rejected proposals with reasons")
    evidence: Dict[str, str] = Field(default_factory=dict, description="Accepted literal -> narrative quote")
    source: str = Field(description="e.g. live:gpt-4o-mini")
    mode: str = "baseline"
    llm_calls: int = 1
    raw_response: Optional[str] = None


def validate_facts(
    candidates: List[str],
    actors: List[str],
    ontology: Optional[Dict[str, PredicateSignature]] = None,
    forbidden: Optional[Set[str]] = None,
    normalise: bool = False,
) -> Tuple[List[str], List[Dict[str, str]]]:
    ontology = ontology or PREDICATE_REGISTRY
    forbidden = derived_predicates() if forbidden is None else forbidden
    accepted, rejected = [], []
    for raw in candidates:
        if not isinstance(raw, str) or not raw.strip():
            rejected.append({"fact": str(raw), "reason": "empty or non-string proposal"})
            continue
        is_neg, pred, args = parse_literal(raw)
        if normalise:  # 'accused: X' -> 'X' (LLMs sometimes copy the role labels)
            args = [a.split(":")[-1].strip().strip("'\"") for a in args]
        sig = ontology.get(pred)
        reason = None
        if sig is None:
            reason = f"unknown predicate '{pred}'"
        elif pred in forbidden:
            reason = f"'{pred}' is a legal conclusion the engine derives; it cannot be asserted as a fact"
        elif len(args) != sig.arity:
            reason = f"'{pred}' expects {sig.arity} argument(s), got {len(args)}"
        else:
            if normalise:
                args = [a if t == LegalType.PERSON else normalise_constant(a) for a, t in zip(args, sig.arg_types)]
            for a, t in zip(args, sig.arg_types):
                if t == LegalType.PERSON and a not in actors:
                    reason = f"argument '{a}' of '{pred}' must be one of the actors {actors}"
                    break
        if reason:
            rejected.append({"fact": raw.strip(), "reason": reason})
        else:
            lit = ("~" if is_neg else "") + format_atom(pred, args)
            if lit not in accepted:
                accepted.append(lit)
    return accepted, rejected


def compare_facts(extracted: List[str], gold: List[str]) -> Dict[str, Any]:
    """Precision / recall of extracted literals against hand-formalised literals (spacing-insensitive)."""
    norm = lambda f: (("~" if parse_literal(f)[0] else "") + format_atom(*parse_literal(f)[1:]))
    e, g = {norm(f) for f in extracted}, {norm(f) for f in gold}
    tp = len(e & g)
    precision = tp / len(e) if e else 0.0
    recall = tp / len(g) if g else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3),
            "missed": sorted(g - e), "extra": sorted(e - g)}


_RULES_COMMON = (
    "1. Only state facts the narrative supports. If something is not mentioned, OMIT it (open-world "
    "assumption) - never guess.\n"
    "2. Negate with '~' ONLY when the narrative says the thing did NOT happen. If the narrative says a "
    "matter is unknown, unproven or that the record is silent, OMIT it - unknown is not false.\n"
    "3. A general statement such as 'no excuse existed' negates only the defences it actually names; "
    "never invent facts about age, consent, contracts or groups that the narrative does not discuss.\n"
    "4. Mental states (intention, knowledge, premeditation) may be stated when the described conduct "
    "clearly shows them, as a reasonable fact-finder would (e.g. deliberately shooting someone dead shows "
    "an intention to cause death). Cite the conduct as evidence.\n"
    "5. Follow the argument roles exactly (e.g. in GraveAndSuddenProvocation the PROVOKER comes first), "
    "but write only the constants: GraveAndSuddenProvocation(B, A), never role labels.\n"
    "   Acting under provocation, in passion or in a sudden fight does NOT negate an intention to kill or "
    "injure; those defences presuppose the intentional act.\n"
    "6. Never state legal conclusions such as Murder, Cheats or LiableToPunishment.\n"
    "7. Non-person arguments (property, grounds, groups, concealed facts) are short CamelCase constants.\n"
)


class FactExtractor:
    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None, client: Any = None,
                 ontology: Optional[Dict[str, PredicateSignature]] = None):
        self.model = model
        self.ontology = ontology or PREDICATE_REGISTRY
        self.forbidden = derived_predicates()
        self._client = client
        if self._client is None:
            key = api_key or os.getenv("OPENAI_API_KEY")
            if key:
                try:
                    from openai import OpenAI
                    self._client = OpenAI(api_key=key)
                except ImportError:
                    self._client = None

    @property
    def is_available(self) -> bool:
        return self._client is not None

    # ------------------------------------------------------------------ prompts
    def _vocabulary(self, with_roles: bool) -> str:
        lines = []
        for s in self.ontology.values():
            if s.name in self.forbidden:
                continue
            if with_roles and s.arg_names:
                sig = ", ".join(s.arg_names)
            else:
                sig = ", ".join(t.value for t in s.arg_types)
            lines.append(f"- {s.name}({sig}): {s.description}")
        return "\n".join(lines)

    def build_prompt(self, narrative: str, actors: List[str]) -> str:
        """Baseline prompt (v1): plain list of literals, no evidence."""
        return (
            "Translate the criminal-law scenario below into ground first-order facts.\n\n"
            f"ACTORS (use exactly these constants for persons): {', '.join(actors)}\n\n"
            f"ALLOWED PREDICATES:\n{self._vocabulary(with_roles=False)}\n\n"
            "RULES:\n"
            "1. Only state facts the narrative explicitly supports. If something is not mentioned, OMIT it "
            "(open-world assumption) - never guess.\n"
            "2. If the narrative explicitly says something did NOT happen, write it negated with '~', e.g. "
            "~ProvocationVoluntarilySought(A).\n"
            "3. Never state legal conclusions such as Murder, Cheats or LiableToPunishment.\n"
            "4. Non-person arguments (property, grounds, groups) may be short CamelCase constants.\n"
            'Respond as JSON: {"facts": ["Pred(A, B)", "~Pred(A)", ...]}\n\n'
            f"SCENARIO:\n{narrative}"
        )

    def build_grounded_prompt(self, narrative: str, actors: List[str]) -> str:
        return (
            "Translate the criminal-law scenario below into ground first-order facts. Every fact must be "
            "justified by a VERBATIM quote copied from the scenario text.\n\n"
            f"ACTORS (use exactly these constants for persons): {', '.join(actors)}\n\n"
            f"ALLOWED PREDICATES (argument roles in order):\n{self._vocabulary(with_roles=True)}\n\n"
            f"RULES:\n{_RULES_COMMON}"
            "8. 'evidence' must be an exact substring of the scenario. Facts without such a quote are discarded.\n"
            'Respond as JSON: {"facts": [{"fact": "Pred(A, B)", "evidence": "exact quote"}, ...]}\n\n'
            f"SCENARIO:\n{narrative}"
        )

    def build_clarification_prompt(self, narrative: str, actors: List[str], questions: List[str]) -> str:
        roles = []
        for q in questions:
            sig = self.ontology.get(parse_literal(q)[1])
            if sig:
                roles.append(f"- {sig.name}({', '.join(sig.arg_names)}): {sig.description}")
        qs = "\n".join(f"{i + 1}. {q}" for i, q in enumerate(questions))
        return (
            "A formal legal verifier could not reach a verdict because the following atoms are unknown. "
            "For EACH atom decide, using ONLY the scenario text, whether it is TRUE, FALSE or UNKNOWN.\n\n"
            f"ACTORS: {', '.join(actors)}\n\nPREDICATE MEANINGS:\n{chr(10).join(dict.fromkeys(roles))}\n\n"
            f"ATOMS:\n{qs}\n\n"
            "RULES:\n"
            "- TRUE or FALSE needs a VERBATIM quote from the scenario that shows it; otherwise answer UNKNOWN.\n"
            "- If the scenario says the matter is unknown, unproven or silent, answer UNKNOWN.\n"
            "- Mental states may be TRUE when the described conduct clearly shows them; quote that conduct. "
            "Provocation, passion or a sudden fight does NOT make an intention FALSE.\n"
            "- The quote must be about the atom itself; an unrelated sentence is not evidence.\n"
            "- If an atom contains a placeholder such as ?p, put the concrete CamelCase constant in 'fact'.\n"
            'Respond as JSON: {"answers": [{"atom": "Pred(A, B)", "status": "TRUE|FALSE|UNKNOWN", '
            '"fact": "Pred(A, B)", "evidence": "exact quote"}, ...]}\n\n'
            f"SCENARIO:\n{narrative}"
        )

    # ------------------------------------------------------------------ LLM call
    def _ask(self, prompt: str) -> str:
        if not self.is_available:
            raise RuntimeError("Fact extraction needs OPENAI_API_KEY (or an injected client).")
        res = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a precise legal knowledge engineer. You output only JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        return res.choices[0].message.content

    # ------------------------------------------------------------------ extraction
    def extract(self, narrative: str, actors: List[str], mode: str = "baseline") -> ExtractionResult:
        """mode 'baseline' (v1 prompt, plain literals) or 'grounded' (evidence-checked)."""
        if mode == "baseline":
            content = self._ask(self.build_prompt(narrative, actors))
            try:
                candidates = json.loads(content).get("facts", [])
            except (json.JSONDecodeError, AttributeError):
                return ExtractionResult(rejected=[{"fact": str(content)[:200], "reason": "response was not valid JSON"}],
                                        source=f"live:{self.model}", mode=mode, raw_response=content)
            candidates = [c if isinstance(c, str) else str(c.get("fact", "")) if isinstance(c, dict) else str(c)
                          for c in candidates]
            accepted, rejected = validate_facts(candidates, actors, self.ontology, self.forbidden)
            return ExtractionResult(accepted=accepted, rejected=rejected, source=f"live:{self.model}",
                                    mode=mode, raw_response=content)

        content = self._ask(self.build_grounded_prompt(narrative, actors))
        try:
            items = json.loads(content).get("facts", [])
        except (json.JSONDecodeError, AttributeError):
            items, content = [], content
        accepted, rejected, evidence = [], [], {}
        for item in items:
            fact = item.get("fact", "") if isinstance(item, dict) else str(item)
            quote = item.get("evidence", "") if isinstance(item, dict) else ""
            if not is_grounded(quote, narrative):
                rejected.append({"fact": str(fact), "reason": f"evidence not found in narrative: '{str(quote)[:80]}'"})
                continue
            guard = evidence_check(str(fact), str(quote))
            if guard:
                rejected.append({"fact": str(fact), "reason": guard})
                continue
            ok, bad = validate_facts([fact], actors, self.ontology, self.forbidden, normalise=True)
            rejected.extend(bad)
            for lit in ok:
                if lit not in accepted:
                    accepted.append(lit)
                    evidence[lit] = quote
        # Declared actors are persons by construction of the scenario (not an LLM judgement),
        # except constants the extraction itself identifies as groups.
        groups = {parse_literal(f)[2][0] for f in accepted if parse_literal(f)[1] == "GroupOfPersons"}
        groups |= {parse_literal(f)[2][0] for f in accepted if parse_literal(f)[1] == "ActingInConcertOnDiscriminatoryGround"}
        for a in actors:
            if a in groups:
                continue
            lit = f"Person({a})"
            if lit not in accepted:
                accepted.insert(0, lit)
                evidence[lit] = "(declared actor)"
        return ExtractionResult(accepted=accepted, rejected=rejected, evidence=evidence,
                                source=f"live:{self.model}", mode="grounded", raw_response=content)

    def clarify(self, narrative: str, actors: List[str], questions: List[str],
                known: List[str]) -> Tuple[List[str], List[Dict[str, str]], Dict[str, str], List[Dict[str, Any]]]:
        """Ask targeted questions about unknown atoms. Returns (new literals, rejected, evidence, answer log)."""
        content = self._ask(self.build_clarification_prompt(narrative, actors, questions))
        try:
            answers = json.loads(content).get("answers", [])
        except (json.JSONDecodeError, AttributeError):
            return [], [{"fact": str(content)[:200], "reason": "response was not valid JSON"}], {}, []
        known_atoms = {format_atom(*parse_literal(k)[1:]) for k in known}
        asked_preds = {parse_literal(q)[1] for q in questions}
        new, rejected, evidence, log = [], [], {}, []
        for a in answers if isinstance(answers, list) else []:
            if not isinstance(a, dict):
                continue
            status = str(a.get("status", "UNKNOWN")).upper()
            atom = str(a.get("fact") or a.get("atom") or "").lstrip("~¬").strip()
            quote = str(a.get("evidence", ""))
            log.append({"atom": a.get("atom"), "status": status, "evidence": quote})
            if status not in ("TRUE", "FALSE"):
                continue
            _, pred, _ = parse_literal(atom)
            if pred not in asked_preds:
                rejected.append({"fact": atom, "reason": "answer does not correspond to a question"})
                continue
            if not is_grounded(quote, narrative):
                rejected.append({"fact": atom, "reason": f"evidence not found in narrative: '{quote[:80]}'"})
                continue
            literal = ("~" if status == "FALSE" else "") + atom
            guard = evidence_check(literal, quote)
            if guard:
                rejected.append({"fact": literal, "reason": guard})
                continue
            ok, bad = validate_facts([literal], actors, self.ontology, self.forbidden, normalise=True)
            rejected.extend(bad)
            for lit in ok:
                if format_atom(*parse_literal(lit)[1:]) in known_atoms or lit in new:
                    continue  # never overwrite or contradict a fact that is already known
                new.append(lit)
                evidence[lit] = quote
        return new, rejected, evidence, log


class NeuroSymbolicPipeline:
    """Narrative -> (LLM) facts -> (engine) verdict, with engine-guided clarification rounds."""

    def __init__(self, extractor: FactExtractor, engine=None, max_rounds: int = 2, max_questions: int = 12):
        from bns_verifier.engine import LegalVerificationEngine
        self.extractor = extractor
        self.engine = engine or LegalVerificationEngine()
        self.max_rounds = max_rounds
        self.max_questions = max_questions

    def run(self, scenario: LegalScenario, mode: str = "loop") -> Dict[str, Any]:
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}")
        ext = self.extractor.extract(scenario.narrative, scenario.actors,
                                     mode="baseline" if mode == "baseline" else "grounded")
        facts, rejected, evidence = list(ext.accepted), list(ext.rejected), dict(ext.evidence)
        trace = self.engine.verify_scenario(scenario.model_copy(update={"facts": facts}))
        calls, rounds = 1, []
        while (mode == "loop" and len(rounds) < self.max_rounds
               and trace.computed_verdict == LegalVerdict.INSUFFICIENT_INFORMATION and trace.missing_facts):
            known = {format_atom(*parse_literal(f)[1:]) for f in facts}
            questions = []
            for m in trace.missing_facts:
                atom = m.lstrip("~¬").strip()
                if format_atom(*parse_literal(atom)[1:]) not in known and atom not in questions:
                    questions.append(atom)
            questions = questions[: self.max_questions]
            if not questions:
                break
            new, bad, ev, log = self.extractor.clarify(scenario.narrative, scenario.actors, questions, facts)
            calls += 1
            rejected.extend(bad)
            evidence.update(ev)
            rounds.append({"questions": questions, "answers": log, "added": new})
            if not new:
                break
            facts.extend(new)
            trace = self.engine.verify_scenario(scenario.model_copy(update={"facts": facts}))
        return {"facts": facts, "rejected": rejected, "evidence": evidence, "trace": trace,
                "llm_calls": calls, "clarification_rounds": rounds}
