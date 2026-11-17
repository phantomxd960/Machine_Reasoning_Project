"""
Component Schemas for Pass 1 Decomposition.
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class ComponentType(str, Enum):
    MAIN_PROVISION = "MAIN_PROVISION"
    SUBSECTION = "SUBSECTION"
    CLAUSE = "CLAUSE"
    SUBCLAUSE = "SUBCLAUSE"
    EXPLANATION = "EXPLANATION"
    PROVISO = "PROVISO"
    EXCEPTION = "EXCEPTION"
    ILLUSTRATION = "ILLUSTRATION"
    PUNISHMENT = "PUNISHMENT"
    DEFINITION = "DEFINITION"

class Component(BaseModel):
    """
    Representation of an individual legal component within a statutory section.
    """
    id: str = Field(description="Unique deterministic identifier (e.g. BNS-SEC-101-EXC-1)")
    section_number: int = Field(description="Section number in BNS 2023 (1-358)")
    component_type: ComponentType = Field(description="Legal component classification")
    statutory_label: Optional[str] = Field(default=None, description="Legislative marker, e.g. '(1)', '(a)', 'Explanation 1'")
    parent_id: Optional[str] = Field(default=None, description="Immediate structural parent component ID")
    verbatim_text: str = Field(description="Exact verbatim text of the component from the enacted statute")
    char_start: int = Field(description="0-based start character offset in raw section text")
    char_end: int = Field(description="0-based end character offset in raw section text")
    is_punishment: bool = Field(default=False, description="Whether component specifies penal consequence")
    is_definition: bool = Field(default=False, description="Whether component defines a legal term")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional component metadata")

class Pass1ComponentOutput(BaseModel):
    """
    Model-facing output container for Pass 1 extraction.
    """
    section_number: int
    components: List[Component]
