"""
Configuration for the BNS Knowledge Base Construction Pipeline.
"""
from pathlib import Path
from pydantic import BaseModel, Field

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
OUTPUT_DATA_DIR = DATA_DIR / "output"

# Default files
DEFAULT_CSV_PATH = RAW_DATA_DIR / "bns_sections.csv"
KNOWLEDGE_BASE_JSONL_PATH = OUTPUT_DATA_DIR / "knowledge_base.jsonl"
REVIEW_COMPONENTS_CSV_PATH = OUTPUT_DATA_DIR / "review_components.csv"
REVIEW_RELATIONSHIPS_CSV_PATH = OUTPUT_DATA_DIR / "review_relationships.csv"
VALIDATION_SUMMARY_PATH = OUTPUT_DATA_DIR / "validation_summary.json"
CHECKPOINT_PATH = OUTPUT_DATA_DIR / "checkpoint.json"

# Pilot Sections for testing and validation
PILOT_SECTIONS = [101, 103, 318]

# Validation Thresholds
MIN_COVERAGE_THRESHOLD = 0.95  # 95% non-whitespace character coverage
SCHEMA_VERSION = "1.0.0"
PIPELINE_VERSION = "bns_kb_v1.1"  # v1.1: roman-numeral disambiguation, DEFINITION type
