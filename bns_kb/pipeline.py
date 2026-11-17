"""
End-to-End Pipeline Orchestrator for BNS Knowledge Base Construction.
"""
import json
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

from bns_kb.config import (
    DEFAULT_CSV_PATH,
    PILOT_SECTIONS,
    SCHEMA_VERSION,
    PIPELINE_VERSION
)
from bns_kb.ingestion import BNSIngestion
from bns_kb.extractors.rule_based_parser import RuleBasedBNSParser
from bns_kb.validators import validate_section
from bns_kb.storage.checkpoint import CheckpointManager
from bns_kb.storage.exporter import StorageExporter
from bns_kb.schemas.provenance import (
    ProvenanceMetadata,
    SectionStorageRecord,
    ReviewStatus
)

def _code_fingerprint() -> str:
    """
    Pipeline version plus a hash of the extraction and validation source code. Any edit to the
    parser or validators changes it, so checkpointed records are never reused across code changes.
    """
    import hashlib
    pkg = Path(__file__).resolve().parent
    h = hashlib.sha256()
    for f in sorted(list((pkg / "extractors").glob("*.py")) + list((pkg / "validators").glob("*.py"))):
        h.update(f.read_bytes())
    return f"{PIPELINE_VERSION}+{h.hexdigest()[:12]}"


class BNSKnowledgeBasePipeline:
    def __init__(
        self,
        csv_path: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        use_checkpoint: bool = True
    ):
        self.ingestion = BNSIngestion(csv_path or DEFAULT_CSV_PATH)
        self.code_fingerprint = _code_fingerprint()
        self.use_checkpoint = use_checkpoint
        
        if output_dir:
            out_p = Path(output_dir)
            self.checkpoint = CheckpointManager(out_p / "checkpoint.json") if use_checkpoint else None
            self.exporter = StorageExporter(
                jsonl_path=out_p / "knowledge_base.jsonl",
                components_csv_path=out_p / "review_components.csv",
                relationships_csv_path=out_p / "review_relationships.csv",
                validation_summary_path=out_p / "validation_summary.json"
            )
        else:
            self.checkpoint = CheckpointManager() if use_checkpoint else None
            self.exporter = StorageExporter()
        
        # Build section name mapping for cross-section punishment resolution
        all_sections = self.ingestion.get_all_sections()
        self.known_section_numbers: Set[int] = {s["section_number"] for s in all_sections}
        self.section_name_mapping: Dict[str, int] = {}
        for s in all_sections:
            clean_name = s["section_name"].lower().strip(" .—–-")
            self.section_name_mapping[clean_name] = s["section_number"]
            
        self.parser = RuleBasedBNSParser(self.section_name_mapping)

    def process_section(self, section_data: Dict[str, Any]) -> SectionStorageRecord:
        sec_num = section_data["section_number"]
        sec_name = section_data["section_name"]
        raw_text = section_data["raw_text"]
        sha256 = section_data["raw_text_sha256"]

        # Pass 1 & Pass 2 Extraction
        components, relationships = self.parser.parse(sec_num, sec_name, raw_text)

        # Multi-level Deterministic Validation Gate
        val_report = validate_section(
            section_number=sec_num,
            raw_text=raw_text,
            components=components,
            relationships=relationships,
            known_section_numbers=self.known_section_numbers
        )

        provenance = ProvenanceMetadata(
            raw_text_sha256=sha256,
            extractor_version=PIPELINE_VERSION,
            schema_version=SCHEMA_VERSION
        )

        record = SectionStorageRecord(
            section_number=sec_num,
            chapter_number=section_data["chapter_number"],
            chapter_name=section_data["chapter_name"],
            chapter_subtype=section_data.get("chapter_subtype"),
            section_name=sec_name,
            raw_text=raw_text,
            provenance=provenance,
            validation=val_report,
            review_status=ReviewStatus.PENDING_REVIEW,
            components=components,
            relationships=relationships
        )

        if self.checkpoint:
            self.checkpoint.mark_completed(sec_num, sha256, val_report.status.value, self.code_fingerprint, save=False)

        return record

    def _load_previous_records(self) -> Dict[int, SectionStorageRecord]:
        """Previously exported records, used to skip unchanged sections when checkpointing."""
        path = self.exporter.jsonl_path
        records: Dict[int, SectionStorageRecord] = {}
        if not path.exists():
            return records
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        rec = SectionStorageRecord.model_validate(json.loads(line))
                        records[rec.section_number] = rec
        except Exception:
            return {}
        return records

    def run(
        self,
        sections: Optional[List[int]] = None,
        pilot_only: bool = False
    ) -> Dict[str, Any]:
        """
        Runs the full extraction, validation, and storage pipeline.
        - If pilot_only=True: runs pilot sections [101, 103, 318].
        - If sections is provided: runs specified sections.
        - Otherwise: runs all 358 sections.
        """
        if pilot_only:
            target_data = self.ingestion.get_pilot_sections()
        elif sections:
            target_data = [self.ingestion.get_section(s) for s in sections]
        else:
            target_data = self.ingestion.get_all_sections()

        previous = self._load_previous_records() if self.checkpoint else {}
        records: List[SectionStorageRecord] = []
        reused = 0
        for s_data in target_data:
            sec_num = s_data["section_number"]
            sha256 = s_data["raw_text_sha256"]

            # Checkpoint: reuse the stored record when source text and pipeline version are unchanged
            prev = previous.get(sec_num)
            if (self.checkpoint and prev is not None
                    and prev.provenance.raw_text_sha256 == sha256
                    and self.checkpoint.is_completed(sec_num, sha256, self.code_fingerprint)):
                records.append(prev)
                reused += 1
                continue

            records.append(self.process_section(s_data))

        if self.checkpoint:
            self.checkpoint.save()
        summary = self.exporter.export_all(records)
        summary["sections_reused_from_checkpoint"] = reused
        summary["sections_extracted"] = len(records) - reused
        return summary
