"""
Command-Line Interface: agreement-based triage between the neuro-symbolic pipeline and a direct
LLM verdict. Reads saved live results (no API calls):

  data/output/fact_extraction_eval[_<model>].json   (from run_fact_extraction.py)
  data/output/llm_vs_verifier_comparison[_<model>].json   (from run_llm_comparison.py)

    python run_hybrid_analysis.py
"""
import json
import sys

from bns_verifier.hybrid import ROOT, load_and_analyse

PAIRS = [
    ("gpt-4o-mini", "fact_extraction_eval.json", "llm_vs_verifier_comparison.json"),
    ("gpt-4o", "fact_extraction_eval_gpt-4o.json", "llm_vs_verifier_comparison_gpt-4o.json"),
]


def main():
    results = []
    for model, ext, cmp in PAIRS:
        if not (ROOT / ext).exists() or not (ROOT / cmp).exists():
            print(f"Skipping {model}: run run_fact_extraction.py and run_llm_comparison.py --require-live first.")
            continue
        results.append(load_and_analyse(ext, cmp))
    if not results:
        sys.exit(1)

    print("=" * 100)
    print("AGREEMENT TRIAGE: neuro-symbolic pipeline (loop mode) x direct LLM verdict")
    print("=" * 100)
    print(f"{'Model':12s} | {'Pipeline':>8s} | {'LLM':>5s} | {'Auto-accepted':>13s} | {'Accuracy on auto':>16s} | "
          f"{'Unsafe auto':>11s} | {'Unsafe -> review':>16s}")
    print("-" * 100)
    for r in results:
        n = r["scenarios"]
        print(f"{r['model']:12s} | {r['pipeline_correct']:>4d}/{n:<3d} | {r['llm_correct']:>2d}/{n:<2d} | "
              f"{r['auto_accepted']:>5d} ({r['coverage_pct']:4.1f}%) | {r['auto_correct']:>4d}/{r['auto_accepted']:<2d} "
              f"({r['auto_accuracy_pct']:5.1f}%) | {r['unsafe_auto_accepted']:>11d} | {r['unsafe_routed_to_review']:>16d}")
    print("-" * 100)
    for r in results:
        print(f"{r['model']}: human review -> {', '.join(r['human_review'])}")
    out = ROOT / "hybrid_triage.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Saved -> {out}")


if __name__ == "__main__":
    main()
