"""
Agreement-based triage between two independent verdict sources:

  * the neuro-symbolic pipeline (LLM fact extraction -> formal verification engine), and
  * a direct LLM verdict on the same narrative.

The two fail differently: the direct LLM tends to miss provisos that defeat a defence, while the
pipeline fails when a fact is extracted with the wrong polarity. When both agree the verdict is
accepted automatically (with the engine's audit trace as its justification); when they disagree
the case is routed to human review. This is selective prediction: lower coverage, higher accuracy.
"""
import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent / "data" / "output"


def triage(pipeline_verdict: str, llm_verdict: str) -> str:
    """'AUTO_ACCEPT' when the two sources agree, otherwise 'HUMAN_REVIEW'."""
    return "AUTO_ACCEPT" if pipeline_verdict == llm_verdict else "HUMAN_REVIEW"


def analyse(extraction_eval: Dict[str, Any], comparison: Dict[str, Any], mode: str = "loop") -> Dict[str, Any]:
    pipe = {r["scenario_id"]: r for r in extraction_eval["modes"][mode]["records"]}
    direct = {r["scenario_id"]: r for r in comparison["comparison_records"]}
    rows: List[Dict[str, Any]] = []
    for sid in sorted(set(pipe) & set(direct)):
        p, d = pipe[sid], direct[sid]
        gt = p["ground_truth"]
        decision = triage(p["verdict_from_extracted_facts"], d["llm_verdict"])
        rows.append({
            "scenario_id": sid, "ground_truth": gt,
            "pipeline_verdict": p["verdict_from_extracted_facts"], "llm_verdict": d["llm_verdict"],
            "decision": decision,
            "auto_verdict_correct": (p["verdict_from_extracted_facts"] == gt) if decision == "AUTO_ACCEPT" else None,
            "pipeline_unsafe": p["verdict_from_extracted_facts"] == "SUPPORTED" and gt != "SUPPORTED",
            "llm_unsafe": d["llm_verdict"] == "SUPPORTED" and gt != "SUPPORTED",
        })
    n = len(rows)
    auto = [r for r in rows if r["decision"] == "AUTO_ACCEPT"]
    review = [r for r in rows if r["decision"] == "HUMAN_REVIEW"]
    pct = lambda a, b: round(100 * a / b, 1) if b else 0.0
    return {
        "model": extraction_eval.get("model"), "pipeline_mode": mode, "scenarios": n,
        "pipeline_correct": sum(pipe[s]["end_to_end_correct"] for s in pipe if s in direct),
        "llm_correct": sum(r["llm_verdict"] == r["ground_truth"] for r in rows),
        "auto_accepted": len(auto), "coverage_pct": pct(len(auto), n),
        "auto_correct": sum(bool(r["auto_verdict_correct"]) for r in auto),
        "auto_accuracy_pct": pct(sum(bool(r["auto_verdict_correct"]) for r in auto), len(auto)),
        "unsafe_auto_accepted": sum(r["pipeline_unsafe"] for r in auto),
        "unsafe_routed_to_review": sum(r["pipeline_unsafe"] or r["llm_unsafe"] for r in review),
        "human_review": [r["scenario_id"] for r in review],
        "rows": rows,
    }


def load_and_analyse(extraction_file: str, comparison_file: str, mode: str = "loop") -> Dict[str, Any]:
    ext = json.loads((ROOT / extraction_file).read_text(encoding="utf-8"))
    cmp = json.loads((ROOT / comparison_file).read_text(encoding="utf-8"))
    return analyse(ext, cmp, mode)
