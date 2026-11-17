"""
Structural Validation for Components (DAG, IDs, Hierarchy).
"""
from typing import List, Tuple
from bns_kb.schemas.components import Component

class StructuralValidator:
    @staticmethod
    def validate(components: List[Component]) -> Tuple[bool, List[str], List[str]]:
        """
        Validates ID uniqueness, parent-child referential integrity, and acyclicity.
        Returns: (is_valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        if not components:
            return False, ["No components extracted."], []

        comp_ids = set()
        for c in components:
            if c.id in comp_ids:
                errors.append(f"Duplicate component ID found: {c.id}")
            comp_ids.add(c.id)

        # Check parent existence
        for c in components:
            if c.parent_id is not None:
                if c.parent_id not in comp_ids:
                    # Allow cross-section parent or external reference if prefixed with BNS-SEC
                    if not c.parent_id.startswith("BNS-SEC-"):
                        errors.append(f"Component {c.id} references non-existent parent: {c.parent_id}")

        # Check acyclicity (no self-loops or cycles)
        parent_map = {c.id: c.parent_id for c in components if c.parent_id}
        for cid in comp_ids:
            visited = set()
            curr = cid
            while curr in parent_map:
                if curr in visited:
                    errors.append(f"Cycle detected in component hierarchy involving: {curr}")
                    break
                visited.add(curr)
                curr = parent_map[curr]

        is_valid = len(errors) == 0
        return is_valid, errors, warnings
