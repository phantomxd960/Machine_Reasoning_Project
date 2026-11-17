"""
Provenance, Human Review, and Storage Schemas.
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from bns_kb.schemas.components import Component
from bns_kb.schemas.relationships import Relationship

class ReviewStatus(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_CORRECTION = "NEEDS_CORRECTION"

class ValidationStatus(str, Enum):
    VALIDATED_SYNTAX = "VALIDATED_SYNTAX"
    WARNING = "WARNING"
    FAILED = "FAILED"

class ProvenanceMetadata(BaseModel):
    """
    Source traceability and extraction provenance.
    """
    source_dataset: str = "Bharatiya Nyaya Sanhita (BNS) 2023 Gazette of India"
    source_csv: str = "bns_sections.csv"
    raw_text_sha256: str
    extractor_version: str
    schema_version: str
    extracted_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: Optional[str] = None

class ValidationReport(BaseModel):
    """
    Multi-level deterministic validation result for a section.
    """
    section_number: int
    status: ValidationStatus
    structural_valid: bool
    source_verbatim_valid: bool
    coverage_ratio: float
    coverage_valid: bool
    relationship_valid: bool
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

class SectionStorageRecord(BaseModel):
    """
    Complete consolidated storage record for a single statutory section.
    """
    section_number: int
    chapter_number: int
    chapter_name: str
    chapter_subtype: Optional[str] = None
    section_name: str
    raw_text: str
    provenance: ProvenanceMetadata
    validation: ValidationReport
    review_status: ReviewStatus = ReviewStatus.PENDING_REVIEW
    reviewer_notes: Optional[str] = None
    reviewed_at: Optional[str] = None
    components: List[Component]
    relationships: List[Relationship]
