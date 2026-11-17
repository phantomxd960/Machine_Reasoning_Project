"""
Registry and Storage Exporters for Formal First-Order Logic Rules.
"""
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
import pandas as pd

from bns_fol.config import FORMAL_RULES_JSONL_PATH, FORMAL_RULES_CSV_PATH, PREDICATE_ONTOLOGY_JSON_PATH
from bns_fol.rules.schema import StatutoryRule
from bns_fol.ontology.signatures import PREDICATE_REGISTRY

class RuleRegistry:
    def __init__(self, rules: Optional[List[StatutoryRule]] = None):
        self._rules: List[StatutoryRule] = rules or []
        self._by_id: Dict[str, StatutoryRule] = {r.rule_id: r for r in self._rules}
        self._by_section: Dict[int, List[StatutoryRule]] = {}
        for r in self._rules:
            self._by_section.setdefault(r.section_number, []).append(r)

    def add_rule(self, rule: StatutoryRule):
        self._rules.append(rule)
        self._by_id[rule.rule_id] = rule
        self._by_section.setdefault(rule.section_number, []).append(rule)

    def get_by_id(self, rule_id: str) -> Optional[StatutoryRule]:
        return self._by_id.get(rule_id)

    def get_by_section(self, section_number: int) -> List[StatutoryRule]:
        return self._by_section.get(section_number, [])

    def get_all(self) -> List[StatutoryRule]:
        return list(self._rules)

    def export(
        self,
        jsonl_path: Optional[Path] = None,
        csv_path: Optional[Path] = None,
        ontology_json_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        j_path = Path(jsonl_path or FORMAL_RULES_JSONL_PATH)
        c_path = Path(csv_path or FORMAL_RULES_CSV_PATH)
        o_path = Path(ontology_json_path or PREDICATE_ONTOLOGY_JSON_PATH)

        j_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. Export formal_rules.jsonl
        with open(j_path, "w", encoding="utf-8") as f:
            for r in self._rules:
                f.write(r.model_dump_json() + "\n")

        # 2. Export formal_rules.csv
        rows = []
        for r in self._rules:
            rows.append({
                "rule_id": r.rule_id,
                "section_number": r.section_number,
                "source_component_id": r.source_component_id,
                "rule_name": r.rule_name,
                "rule_type": r.rule_type,
                "formalization_level": r.formalization_level,
                "variables": ", ".join(r.variables),
                "premises": " & ".join(r.premises),
                "conclusion": r.conclusion,
                "formula_unicode": r.formula_unicode,
                "description": r.description
            })
        df = pd.DataFrame(rows)
        df.to_csv(c_path, index=False, encoding="utf-8")

        # 3. Export predicate ontology
        ontology_dict = {k: v.model_dump() for k, v in PREDICATE_REGISTRY.items()}
        with open(o_path, "w", encoding="utf-8") as f:
            json.dump(ontology_dict, f, indent=2)

        return {
            "total_rules": len(self._rules),
            "sections_covered": len(self._by_section),
            "formal_rules_jsonl": str(j_path),
            "formal_rules_csv": str(c_path),
            "predicate_ontology_json": str(o_path)
        }
