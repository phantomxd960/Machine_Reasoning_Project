"""
Exporters for Knowledge Base (JSONL) and Human Review (CSV).
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

from bns_kb.config import (
    KNOWLEDGE_BASE_JSONL_PATH,
    REVIEW_COMPONENTS_CSV_PATH,
    REVIEW_RELATIONSHIPS_CSV_PATH,
    VALIDATION_SUMMARY_PATH,
)
from bns_kb.schemas.provenance import SectionStorageRecord

class StorageExporter:
    def __init__(
        self,
        jsonl_path: Optional[Path] = None,
        components_csv_path: Optional[Path] = None,
        relationships_csv_path: Optional[Path] = None,
        validation_summary_path: Optional[Path] = None,
    ):
        self.jsonl_path = Path(jsonl_path or KNOWLEDGE_BASE_JSONL_PATH)
        self.components_csv_path = Path(components_csv_path or REVIEW_COMPONENTS_CSV_PATH)
        self.relationships_csv_path = Path(relationships_csv_path or REVIEW_RELATIONSHIPS_CSV_PATH)
        self.validation_summary_path = Path(validation_summary_path or VALIDATION_SUMMARY_PATH)

        # Ensure output directory exists
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)

    def export_all(self, records: List[SectionStorageRecord]) -> Dict[str, Any]:
        """
        Exports records to JSONL, review CSVs, and validation summary.
        """
        # 1. Export knowledge_base.jsonl
        with open(self.jsonl_path, "w", encoding="utf-8") as f:
            for rec in records:
                f.write(rec.model_dump_json() + "\n")

        # 2. Export review_components.csv
        comp_rows = []
        for rec in records:
            for c in rec.components:
                comp_rows.append({
                    "section_number": rec.section_number,
                    "section_name": rec.section_name,
                    "chapter_number": rec.chapter_number,
                    "component_id": c.id,
                    "component_type": c.component_type.value,
                    "statutory_label": c.statutory_label or "",
                    "parent_id": c.parent_id or "",
                    "char_start": c.char_start,
                    "char_end": c.char_end,
                    "is_punishment": c.is_punishment,
                    "is_definition": c.is_definition,
                    "verbatim_text": c.verbatim_text,
                    "review_status": rec.review_status.value,
                    "reviewer_notes": rec.reviewer_notes or ""
                })
        df_comps = pd.DataFrame(comp_rows)
        df_comps.to_csv(self.components_csv_path, index=False, encoding="utf-8")

        # 3. Export review_relationships.csv
        rel_rows = []
        for rec in records:
            for r in rec.relationships:
                rel_rows.append({
                    "relationship_id": r.id,
                    "section_number": rec.section_number,
                    "source_id": r.source_id,
                    "relation_type": r.relation_type.value,
                    "target_id": r.target_id,
                    "confidence": r.confidence,
                    "evidence_quote": r.evidence_quote or "",
                    "review_status": rec.review_status.value,
                    "reviewer_notes": rec.reviewer_notes or ""
                })
        df_rels = pd.DataFrame(rel_rows)
        df_rels.to_csv(self.relationships_csv_path, index=False, encoding="utf-8")

        # 4. Generate validation summary
        summary = self._compute_summary(records, df_comps, df_rels)
        with open(self.validation_summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return summary

    def _compute_summary(
        self,
        records: List[SectionStorageRecord],
        df_comps: pd.DataFrame,
        df_rels: pd.DataFrame
    ) -> Dict[str, Any]:
        total_sections = len(records)
        passed_sections = sum(1 for r in records if r.validation.status.value in ("VALIDATED_SYNTAX", "WARNING"))
        perfect_sections = sum(1 for r in records if r.validation.status.value == "VALIDATED_SYNTAX")
        coverage_ratios = [r.validation.coverage_ratio for r in records]
        
        comp_type_counts = df_comps["component_type"].value_counts().to_dict() if not df_comps.empty else {}
        rel_type_counts = df_rels["relation_type"].value_counts().to_dict() if not df_rels.empty else {}

        return {
            "total_sections_processed": total_sections,
            "syntactically_validated_sections": passed_sections,
            "zero_warning_sections": perfect_sections,
            "validation_pass_rate_pct": round((passed_sections / total_sections * 100), 2) if total_sections else 0,
            "mean_coverage_ratio_pct": round((sum(coverage_ratios) / len(coverage_ratios) * 100), 2) if coverage_ratios else 0,
            "min_coverage_ratio_pct": round((min(coverage_ratios) * 100), 2) if coverage_ratios else 0,
            "total_components": len(df_comps),
            "total_relationships": len(df_rels),
            "component_distribution": comp_type_counts,
            "relationship_distribution": rel_type_counts,
            "files": {
                "knowledge_base_jsonl": str(self.jsonl_path),
                "review_components_csv": str(self.components_csv_path),
                "review_relationships_csv": str(self.relationships_csv_path),
                "validation_summary_json": str(self.validation_summary_path),
            }
        }
