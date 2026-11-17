"""
Configuration for BNS First-Order Logic (FOL) Formalization Engine.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = DATA_DIR / "output"

KB_JSONL_PATH = OUTPUT_DIR / "knowledge_base.jsonl"
FORMAL_RULES_JSONL_PATH = OUTPUT_DIR / "formal_rules.jsonl"
FORMAL_RULES_CSV_PATH = OUTPUT_DIR / "formal_rules.csv"
PREDICATE_ONTOLOGY_JSON_PATH = OUTPUT_DIR / "predicate_ontology.json"

PILOT_SECTIONS = [101, 103, 318]
