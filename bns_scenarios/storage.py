"""
Scenario Storage and Exporter for Benchmark Dataset.
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

from bns_scenarios.schema import LegalScenario
from bns_scenarios.benchmark_suite import get_benchmark_scenarios

DEFAULT_SCENARIOS_JSONL = Path(__file__).resolve().parent.parent / "data" / "scenarios" / "benchmark_scenarios.jsonl"
DEFAULT_SCENARIOS_CSV = Path(__file__).resolve().parent.parent / "data" / "scenarios" / "benchmark_scenarios.csv"

def export_scenarios(
    scenarios: Optional[List[LegalScenario]] = None,
    jsonl_path: Optional[Path] = None,
    csv_path: Optional[Path] = None
) -> Dict[str, Any]:
    scens = scenarios or get_benchmark_scenarios()
    j_path = Path(jsonl_path or DEFAULT_SCENARIOS_JSONL)
    c_path = Path(csv_path or DEFAULT_SCENARIOS_CSV)

    j_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Export JSONL
    with open(j_path, "w", encoding="utf-8") as f:
        for s in scens:
            f.write(s.model_dump_json() + "\n")

    # 2. Export CSV
    rows = []
    for s in scens:
        rows.append({
            "scenario_id": s.scenario_id,
            "title": s.title,
            "category": s.category.value,
            "target_sections": ", ".join(str(sec) for sec in s.target_sections),
            "proposed_conclusion": s.proposed_conclusion,
            "ground_truth_verdict": s.ground_truth_verdict.value,
            "narrative": s.narrative,
            "facts": " | ".join(s.facts),
            "ground_truth_explanation": s.ground_truth_explanation
        })
    df = pd.DataFrame(rows)
    df.to_csv(c_path, index=False, encoding="utf-8")

    return {
        "total_scenarios": len(scens),
        "jsonl_path": str(j_path),
        "csv_path": str(c_path)
    }

def load_scenarios(jsonl_path: Optional[Path] = None) -> List[LegalScenario]:
    j_path = Path(jsonl_path or DEFAULT_SCENARIOS_JSONL)
    if not j_path.exists():
        # Export default
        export_scenarios(jsonl_path=j_path)
    
    scenarios = []
    with open(j_path, "r", encoding="utf-8") as f:
        for line in f:
            scenarios.append(LegalScenario.model_validate_json(line))
    return scenarios
