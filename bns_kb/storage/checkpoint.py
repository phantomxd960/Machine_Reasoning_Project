"""
Checkpoint Manager for BNS Pipeline.
Tracks processed sections and source hashes to avoid redundant extractions.
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional
from bns_kb.config import CHECKPOINT_PATH

class CheckpointManager:
    def __init__(self, checkpoint_path: Optional[Path] = None):
        self.path = Path(checkpoint_path or CHECKPOINT_PATH)
        self._data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {"completed_sections": {}}
        return {"completed_sections": {}}

    def is_completed(self, section_number: int, current_sha256: str, pipeline_version: Optional[str] = None) -> bool:
        """
        True when the section was already processed from identical source text (same SHA-256)
        and, if given, by the same pipeline version (so parser changes force re-extraction).
        """
        sec_str = str(section_number)
        record = self._data.get("completed_sections", {}).get(sec_str)
        if not record or record.get("raw_text_sha256") != current_sha256:
            return False
        if pipeline_version is not None and record.get("pipeline_version") != pipeline_version:
            return False
        return True

    def mark_completed(self, section_number: int, sha256: str, status: str, pipeline_version: Optional[str] = None,
                       save: bool = True):
        if "completed_sections" not in self._data:
            self._data["completed_sections"] = {}
        self._data["completed_sections"][str(section_number)] = {
            "raw_text_sha256": sha256,
            "status": status,
            "pipeline_version": pipeline_version
        }
        if save:
            self.save()

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    def clear(self):
        self._data = {"completed_sections": {}}
        self.save()
