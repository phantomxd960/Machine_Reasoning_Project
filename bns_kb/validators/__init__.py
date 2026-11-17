"""
Unified Multi-Level Deterministic Validation Gate.
"""
from typing import List, Set
from bns_kb.schemas.components import Component
from bns_kb.schemas.relationships import Relationship
from bns_kb.schemas.provenance import ValidationReport, ValidationStatus
from bns_kb.validators.structural_validator import StructuralValidator
from bns_kb.validators.source_validator import SourceValidator
from bns_kb.validators.relationship_validator import RelationshipValidator

def validate_section(
    section_number: int,
    raw_text: str,
    components: List[Component],
    relationships: List[Relationship],
    known_section_numbers: Set[int]
) -> ValidationReport:
    """
    Executes all validation gates:
    - Structural (DAG, IDs, Hierarchy)
    - Source (Exact substring match, Coverage ratio)
    - Relationship (Endpoints, Cycles, Dangling references)
    """
    all_errors = []
    all_warnings = []

    # 1. Structural
    struct_valid, struct_errors, struct_warnings = StructuralValidator.validate(components)
    all_errors.extend(struct_errors)
    all_warnings.extend(struct_warnings)

    # 2. Source text & coverage
    verb_valid, cov_ratio, cov_valid, src_errors, src_warnings = SourceValidator.validate(raw_text, components)
    all_errors.extend(src_errors)
    all_warnings.extend(src_warnings)

    # 3. Relationships
    rel_valid, rel_errors, rel_warnings = RelationshipValidator.validate(
        relationships, components, known_section_numbers
    )
    all_errors.extend(rel_errors)
    all_warnings.extend(rel_warnings)

    if all_errors:
        status = ValidationStatus.FAILED
    elif all_warnings:
        status = ValidationStatus.WARNING
    else:
        status = ValidationStatus.VALIDATED_SYNTAX

    return ValidationReport(
        section_number=section_number,
        status=status,
        structural_valid=struct_valid,
        source_verbatim_valid=verb_valid,
        coverage_ratio=round(cov_ratio, 4),
        coverage_valid=cov_valid,
        relationship_valid=rel_valid,
        warnings=all_warnings,
        errors=all_errors
    )
