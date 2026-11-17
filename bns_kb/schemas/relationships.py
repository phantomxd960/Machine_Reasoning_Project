"""
Relationship Schemas for Pass 2 Topology.
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class RelationType(str, Enum):
    HAS_CHILD = "HAS_CHILD"                         # Structural hierarchy (e.g. section to subsection)
    QUALIFIES = "QUALIFIES"                         # Explanation or proviso clarifying a rule
    EXCEPTION_TO = "EXCEPTION_TO"                   # Statutory exception negating or mitigating offence
    PROVIDES_ILLUSTRATION_FOR = "PROVIDES_ILLUSTRATION_FOR" # Illustration demonstrating application
    PUNISHES = "PUNISHES"                           # Punishment provision prescribing penalty for an offence
    CROSS_REFERENCES = "CROSS_REFERENCES"           # Statutory reference to another component or section

class Relationship(BaseModel):
    """
    Representation of a typed directed edge between two statutory components.
    """
    id: str = Field(description="Unique deterministic relation ID, e.g. BNS-REL-101-001")
    section_number: int = Field(description="Section context of the relationship")
    source_id: str = Field(description="Originating component ID")
    relation_type: RelationType = Field(description="Type of legal relationship")
    target_id: str = Field(description="Target component ID")
    evidence_quote: Optional[str] = Field(default=None, description="Verbatim text span or statutory phrase evidencing relation")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata or qualifying attributes")

class Pass2RelationshipOutput(BaseModel):
    """
    Model-facing output container for Pass 2 extraction.
    """
    section_number: int
    relationships: List[Relationship]
