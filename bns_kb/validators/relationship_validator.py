"""
Relationship Validation for Directed Legal Edges.
"""
from typing import List, Set, Tuple
from bns_kb.schemas.components import Component
from bns_kb.schemas.relationships import Relationship

class RelationshipValidator:
    @staticmethod
    def validate(
        relationships: List[Relationship],
        components: List[Component],
        known_section_numbers: Set[int]
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Validates:
        1. Source and Target endpoint existence
        2. No self-loops
        3. Cross-reference targets point to valid sections
        Returns: (is_valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        comp_ids = {c.id for c in components}
        
        for r in relationships:
            # Check self-loop
            if r.source_id == r.target_id:
                errors.append(f"Relationship {r.id} is a self-loop: {r.source_id} -> {r.target_id}")

            # Source must exist in current section
            if r.source_id not in comp_ids:
                errors.append(f"Relationship {r.id} source ID not found: {r.source_id}")

            # Target may be in current section or cross-section (e.g. BNS-SEC-101-MAIN)
            if r.target_id not in comp_ids:
                if r.target_id.startswith("BNS-SEC-"):
                    # Parse section number from cross-section ID
                    try:
                        parts = r.target_id.split("-")
                        sec_num = int(parts[2])
                        if sec_num not in known_section_numbers:
                            warnings.append(f"Relationship {r.id} targets external section {sec_num} not in known dataset.")
                    except (IndexError, ValueError):
                        warnings.append(f"Relationship {r.id} targets unusual cross-statute ID: {r.target_id}")
                else:
                    errors.append(f"Relationship {r.id} target ID not found: {r.target_id}")

        is_valid = len(errors) == 0
        return is_valid, errors, warnings
