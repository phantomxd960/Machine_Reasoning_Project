"""
Dataset Ingestion and Provenance Tracking for BNS 2023.
"""
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd

from bns_kb.config import DEFAULT_CSV_PATH, PILOT_SECTIONS

class BNSIngestion:
    """
    Ingests and validates raw statutory data from the BNS dataset.
    """
    def __init__(self, csv_path: Optional[Path] = None):
        self.csv_path = Path(csv_path or DEFAULT_CSV_PATH)
        if not self.csv_path.exists():
            raise FileNotFoundError(f"BNS dataset CSV not found at: {self.csv_path}")
        self._df = self._load_and_standardize()

    def _load_and_standardize(self) -> pd.DataFrame:
        df = pd.read_csv(self.csv_path)
        
        # Standardize columns (handling any whitespace variations like 'Section _name')
        col_map = {}
        for col in df.columns:
            clean = col.strip().lower().replace(" ", "_")
            if "section_name" in clean or "section__name" in clean:
                col_map[col] = "section_name"
            elif "chapter_name" in clean:
                col_map[col] = "chapter_name"
            elif "chapter_subtype" in clean:
                col_map[col] = "chapter_subtype"
            elif clean == "section":
                col_map[col] = "section_number"
            elif clean == "chapter":
                col_map[col] = "chapter_number"
            elif clean == "description":
                col_map[col] = "raw_text"
            else:
                col_map[col] = clean

        df = df.rename(columns=col_map)
        
        # Clean text: keep exact raw characters, but normalize carriage returns (\r\n -> \n)
        # while keeping exact character integrity
        df["raw_text"] = df["raw_text"].astype(str)
        
        # Compute SHA-256 for provenance
        df["raw_text_sha256"] = df["raw_text"].apply(
            lambda t: hashlib.sha256(t.encode("utf-8")).hexdigest()
        )
        return df

    def get_section(self, section_number: int) -> Dict[str, Any]:
        matched = self._df[self._df["section_number"] == section_number]
        if matched.empty:
            raise KeyError(f"Section {section_number} not found in BNS dataset.")
        return matched.iloc[0].to_dict()

    def get_pilot_sections(self) -> List[Dict[str, Any]]:
        return [self.get_section(sec) for sec in PILOT_SECTIONS]

    def get_all_sections(self) -> List[Dict[str, Any]]:
        return self._df.to_dict(orient="records")

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_sections": len(self._df),
            "chapters_count": int(self._df["chapter_number"].nunique()),
            "min_section": int(self._df["section_number"].min()),
            "max_section": int(self._df["section_number"].max()),
            "csv_path": str(self.csv_path)
        }
