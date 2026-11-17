"""
Command-Line Interface: evaluate LLM fact extraction (narrative -> FOL facts) and the full
neuro-symbolic loop (extracted facts -> verification engine) against the benchmark.

Three strategies are compared (see bns_verifier/fact_extractor.py):
  baseline  plain literal list, no evidence
  grounded  every literal must cite a verbatim narrative quote; constants normalised
  loop      grounded + engine-guided clarification of missing facts

Requires OPENAI_API_KEY. Without it, the script explains what it would do and exits.

    python run_fact_extraction.py                              # all modes, all 20 scenarios
    python run_fact_extraction.py --modes loop --scenario SCEN-BNS-012
"""
import argparse
import json
import sys
from pathlib import Path

from bns_scenarios.benchmark_suite import get_benchmark_scenarios
from bns_scenarios.schema import LegalVerdict
from bns_verifier.engine import LegalVerificationEngine
from bns_verifier.fact_extractor import MODES, FactExtractor, NeuroSymbolicPipeline, compare_facts

OUT_PATH = Path(__file__).resolve().parent / "data" / "output" / "fact_extraction_eval.json"


def evaluate(pipeline, scenarios, mode):
    records = []
    for sc in scenarios:
        out = pipeline.run(sc, mode=mode)
        trace = out["trace"]
        cmp = compare_facts(out["facts"], sc.facts)
        verdict = trace.computed_verdict
        records.append({
            "scenario_id": sc.scenario_id, "extracted": out["facts"], "rejected": out["rejected"],
            "evidence": out["evidence"], **cmp, "llm_calls": out["llm_calls"],
            "clarification_rounds": out["clarification_rounds"],
            "verdict_from_extracted_facts": verdict.value, "ground_truth": sc.ground_truth_verdict.value,
            "end_to_end_correct": trace.verdict_matches_ground_truth,
            "unsafe_supported": verdict == LegalVerdict.SUPPORTED and sc.ground_truth_verdict != LegalVerdict.SUPPORTED,
        })
        print(f"  [{mode:8s}] {sc.scenario_id}: P={cmp['precision']:.2f} R={cmp['recall']:.2f} "
              f"rejected={len(out['rejected']):2d} calls={out['llm_calls']} verdict={verdict.value} "
              f"({'OK' if trace.verdict_matches_ground_truth else 'WRONG'})")
    n = len(records)
    avg = lambda k: round(sum(r[k] for r in records) / n, 3) if n else 0
    return {
        "mode": mode, "scenarios": n, "mean_precision": avg("precision"), "mean_recall": avg("recall"),
        "mean_f1": avg("f1"), "end_to_end_correct": sum(r["end_to_end_correct"] for r in records),
        "end_to_end_accuracy_pct": round(100 * sum(r["end_to_end_correct"] for r in records) / n, 1) if n else 0,
        "unsafe_supported": sum(r["unsafe_supported"] for r in records),
        "rejected_proposals": sum(len(r["rejected"]) for r in records),
        "llm_calls": sum(r["llm_calls"] for r in records), "records": records,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate LLM narrative-to-facts extraction")
    parser.add_argument("--scenario", default=None, help="Run a single scenario ID")
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--modes", default=",".join(MODES), help=f"Comma-separated subset of {MODES}")
    parser.add_argument("--no-export", action="store_true")
    parser.add_argument("--out", default=None, help="Output JSON path (default data/output/fact_extraction_eval.json)")
    args = parser.parse_args()

    extractor = FactExtractor(model=args.model)
    if not extractor.is_available:
        print("OPENAI_API_KEY is not set (or the openai package is missing).")
        print("This tool sends each scenario narrative to the LLM, validates the returned facts against the")
        print("ontology, compares them with the hand-written facts, and re-runs the verifier on them.")
        sys.exit(1)

    modes = [m.strip() for m in args.modes.split(",") if m.strip()]
    scenarios = get_benchmark_scenarios()
    if args.scenario:
        scenarios = [s for s in scenarios if s.scenario_id == args.scenario]
    pipeline = NeuroSymbolicPipeline(extractor, LegalVerificationEngine())

    results = {}
    for mode in modes:
        print(f"\n=== Mode: {mode} ===")
        results[mode] = evaluate(pipeline, scenarios, mode)

    n = len(scenarios)
    print("\n" + "=" * 92)
    print(f"NARRATIVE -> FACTS -> VERDICT  ({args.model}, {n} scenarios, temperature 0)")
    print("=" * 92)
    print(f"{'Mode':10s} | {'Precision':>9s} | {'Recall':>6s} | {'F1':>5s} | {'Verdict correct':>15s} | "
          f"{'Unsafe SUPPORTED':>16s} | {'LLM calls':>9s}")
    print("-" * 92)
    for m, s in results.items():
        print(f"{m:10s} | {s['mean_precision']:9.3f} | {s['mean_recall']:6.3f} | {s['mean_f1']:5.3f} | "
              f"{s['end_to_end_correct']:>6d}/{n:<2d} ({s['end_to_end_accuracy_pct']:5.1f}%) | "
              f"{s['unsafe_supported']:16d} | {s['llm_calls']:9d}")
    print("=" * 92)

    if not args.no_export:
        out_path = Path(args.out) if args.out else OUT_PATH
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"model": args.model, "scenarios": n, "modes": results}
        out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Saved -> {out_path}")


if __name__ == "__main__":
    main()
