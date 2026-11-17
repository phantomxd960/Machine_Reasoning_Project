"""
Command-Line Interface to run LLM vs. Formal Verification Engine Comparative Benchmark.

By default the LLM is queried live when OPENAI_API_KEY is set; otherwise the pre-recorded
gpt-4o-mini responses stored in bns_verifier/llm_comparator.py are used. The report always
states which source produced the LLM verdicts.
"""
import argparse
from bns_verifier.llm_comparator import LLMComparator


def main():
    parser = argparse.ArgumentParser(description="Compare an LLM baseline with the formal verification engine")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model name for live evaluation")
    parser.add_argument("--require-live", action="store_true",
                        help="Fail instead of falling back to the recorded responses when no API key is available")
    parser.add_argument("--no-export", action="store_true", help="Do not overwrite the comparison JSON/CSV files")
    args = parser.parse_args()

    print("🚀 Starting Empirical Comparative Evaluation: LLM vs. Formal Verification Engine...\n")
    comparator = LLMComparator(model_name=args.model, allow_offline=not args.require_live)
    summary = comparator.run_comparison(export=not args.no_export)

    total = summary["total_scenarios"]
    source = summary["llm_response_source"]
    source_desc = (f"LIVE queries to {summary['llm_model']}" if source.startswith("live")
                   else "PRE-RECORDED gpt-4o-mini responses (no OPENAI_API_KEY set)" if source == "offline_recorded"
                   else source)

    print("=" * 95)
    print("⚖️ EMPIRICAL COMPARISON: STANDARD LLM BASELINE vs. FORMAL VERIFICATION ENGINE")
    print("=" * 95)
    print(f"Total Scenarios Evaluated           : {total}")
    print(f"LLM Response Source                 : {source_desc}")
    print(f"Formal Verification Engine Accuracy : {summary['verifier_accuracy_pct']}%  ({summary['verifier_correct']}/{total} Correct)")
    print(f"LLM Baseline Accuracy               : {summary['llm_accuracy_pct']}%  ({summary['llm_correct']}/{total} Correct)")
    print(f"Accuracy Difference (Delta)         : {summary['accuracy_gap_pct']:+.1f} percentage points")

    print("\n📊 LLM Failure Mode Analysis (labelled by scenario category):")
    print("-" * 80)
    for mode, count in summary['llm_failure_breakdown'].items():
        if mode != "NONE":
            print(f"  • {mode:60s}: {count} failure{'s' if count != 1 else ''}")
    print("-" * 80)

    print("\n📋 Side-by-Side Scenario Evaluation Table:")
    print("-" * 95)
    print(f"{'Scenario ID':13s} | {'Ground Truth':26s} | {'Verifier Verdict':26s} | {'LLM Verdict':26s} | {'LLM Status':10s}")
    print("-" * 95)
    for r in summary['comparison_records']:
        status_tag = "✅ MATCH" if r['llm_correct'] else "❌ FAILED"
        print(f"{r['scenario_id']:13s} | {r['ground_truth']:26s} | {r['verifier_verdict']:26s} | {r['llm_verdict']:26s} | {status_tag:10s}")
    print("-" * 95)

    if not args.no_export:
        print("\n📁 Output Deliverables Generated:")
        print(f"  - Comparison JSON : {summary.get('json_path')}")
        print(f"  - Comparison CSV  : {summary.get('csv_path')}")
    print("=" * 95)


if __name__ == "__main__":
    main()
