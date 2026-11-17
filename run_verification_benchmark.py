"""
Command-Line Interface to execute Legal Scenario Verification Benchmark.
"""
import argparse
from bns_scenarios.benchmark_suite import get_benchmark_scenarios
from bns_verifier.benchmark_runner import VerificationBenchmarkRunner

def main():
    parser = argparse.ArgumentParser(description="Run BNS 2023 Legal Verification Benchmark")
    parser.add_argument("--category", type=str, default=None, help="Filter by ScenarioCategory")
    args = parser.parse_args()

    scenarios = get_benchmark_scenarios()
    if args.category:
        scenarios = [s for s in scenarios if s.category.value.lower() == args.category.lower()]

    print("🚀 Starting Legal Reasoning Verification Benchmark across Scenarios...\n")
    runner = VerificationBenchmarkRunner()
    summary = runner.run_benchmark(scenarios)

    print("="*85)
    print("⚖️ BNS 2023 LEGAL REASONING VERIFICATION BENCHMARK REPORT")
    print("="*85)
    print(f"Total Scenarios Evaluated  : {summary['total_scenarios_evaluated']}")
    print(f"Ground Truth Matches       : {summary['ground_truth_matches']}")
    print(f"Overall Accuracy           : {summary['verification_accuracy_pct']}%")
    print(f"Benchmark Status           : {'✅ 100% PERFECT ALIGNMENT' if summary['all_passed'] else '❌ MISMATCHES DETECTED'}")

    print("\n📊 Accuracy Breakdown by Complexity Category:")
    print("-" * 75)
    print(f"{'Category':30s} | {'Total':5s} | {'Correct':7s} | {'Accuracy':8s}")
    print("-" * 75)
    for cat, st in summary['category_breakdown'].items():
        print(f"{cat:30s} | {st['total']:<5d} | {st['correct']:<7d} | {st['accuracy_pct']:>6.1f}%")
    print("-" * 75)

    print("\n📋 Verdict Distribution:")
    for verd, count in summary['verdict_distribution'].items():
        print(f"  - {verd:26s}: {count}")

    sc = summary["sanction_checks"]
    print("\n⚖️ Sanction Derivation (PUNISHMENT_MAPPING rules, incl. aggravation):")
    print(f"  - Expected punishment derived : {sc['expected_punishment_derived']}/{sc['scenarios_with_expected_punishment']} supported scenarios")
    print(f"  - Fact warnings (ontology)    : {summary['fact_warnings']}")

    print("\n📁 Output Deliverables Generated:")
    print(f"  - Audit Traces (JSONL)     : {summary.get('audit_traces_jsonl')}")
    print(f"  - Benchmark Summary (JSON) : {summary.get('benchmark_summary_json')}")
    print("="*85)

if __name__ == "__main__":
    main()
