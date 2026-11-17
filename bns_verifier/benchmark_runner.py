"""
Benchmark Runner for Legal Scenario Verification.
Evaluates scenario suites, verifies ground truth alignment, and computes accuracy metrics.
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

from bns_scenarios.schema import LegalScenario, LegalVerdict, ScenarioCategory
from bns_scenarios.benchmark_suite import get_benchmark_scenarios
from bns_verifier.audit_trace import VerificationAuditTrace
from bns_verifier.engine import LegalVerificationEngine

DEFAULT_TRACES_JSONL = Path(__file__).resolve().parent.parent / "data" / "output" / "verification_audit_traces.jsonl"
DEFAULT_BENCHMARK_JSON = Path(__file__).resolve().parent.parent / "data" / "output" / "verification_benchmark_summary.json"

class VerificationBenchmarkRunner:
    def __init__(self, engine: Optional[LegalVerificationEngine] = None):
        self.engine = engine or LegalVerificationEngine()

    def run_benchmark(
        self,
        scenarios: Optional[List[LegalScenario]] = None,
        export_traces: bool = True,
        traces_path: Optional[Path] = None,
        summary_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        scens = scenarios or get_benchmark_scenarios()
        traces: List[VerificationAuditTrace] = []

        total = len(scens)
        matched = 0
        category_stats: Dict[str, Dict[str, int]] = {}
        verdict_stats: Dict[str, int] = {}
        failed_scenarios = []

        for sc in scens:
            trace = self.engine.verify_scenario(sc)
            traces.append(trace)

            cat_str = sc.category.value
            if cat_str not in category_stats:
                category_stats[cat_str] = {"total": 0, "correct": 0}
            category_stats[cat_str]["total"] += 1

            v_str = trace.computed_verdict.value
            verdict_stats[v_str] = verdict_stats.get(v_str, 0) + 1

            if trace.verdict_matches_ground_truth:
                matched += 1
                category_stats[cat_str]["correct"] += 1
            else:
                failed_scenarios.append({
                    "scenario_id": sc.scenario_id,
                    "title": sc.title,
                    "expected": sc.ground_truth_verdict.value,
                    "computed": trace.computed_verdict.value,
                    "explanation": trace.final_legal_explanation
                })

        accuracy_pct = round((matched / total * 100), 2) if total > 0 else 0.0

        sanction_checked = [t for t in traces if t.sanction_matches_expected is not None]
        sanction_matched = sum(1 for t in sanction_checked if t.sanction_matches_expected)
        fact_warning_count = sum(len(t.fact_warnings) for t in traces)

        # Category breakdown with percentages
        category_breakdown = {}
        for cat, st in category_stats.items():
            acc = round((st["correct"] / st["total"] * 100), 1) if st["total"] > 0 else 0.0
            category_breakdown[cat] = {
                "total": st["total"],
                "correct": st["correct"],
                "accuracy_pct": acc
            }

        summary = {
            "total_scenarios_evaluated": total,
            "ground_truth_matches": matched,
            "verification_accuracy_pct": accuracy_pct,
            "category_breakdown": category_breakdown,
            "verdict_distribution": verdict_stats,
            "failed_scenarios": failed_scenarios,
            "sanction_checks": {
                "scenarios_with_expected_punishment": len(sanction_checked),
                "expected_punishment_derived": sanction_matched,
            },
            "fact_warnings": fact_warning_count,
            "all_passed": (matched == total)
        }

        if export_traces:
            t_path = Path(traces_path or DEFAULT_TRACES_JSONL)
            s_path = Path(summary_path or DEFAULT_BENCHMARK_JSON)
            t_path.parent.mkdir(parents=True, exist_ok=True)

            with open(t_path, "w", encoding="utf-8") as f:
                for tr in traces:
                    f.write(tr.model_dump_json() + "\n")

            with open(s_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)

            summary["audit_traces_jsonl"] = str(t_path)
            summary["benchmark_summary_json"] = str(s_path)

        return summary
