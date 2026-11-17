"""
Source Text and Coverage Validation.
"""
import re
from typing import List, Tuple
from bns_kb.schemas.components import Component
from bns_kb.config import MIN_COVERAGE_THRESHOLD

class SourceValidator:
    @staticmethod
    def validate(raw_text: str, components: List[Component]) -> Tuple[bool, float, bool, List[str], List[str]]:
        """
        Validates:
        1. Exact substring match: raw_text[char_start:char_end] == verbatim_text
        2. Non-whitespace character coverage ratio
        Returns: (is_verbatim_valid, coverage_ratio, is_coverage_valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        # 1. Exact substring check
        for c in components:
            slice_text = raw_text[c.char_start:c.char_end]
            if slice_text != c.verbatim_text:
                errors.append(
                    f"Component {c.id} span [{c.char_start}:{c.char_end}] does not match verbatim_text. "
                    f"Expected {repr(slice_text[:30])}, got {repr(c.verbatim_text[:30])}"
                )

        # 2. Coverage calculation
        raw_non_ws = len(re.sub(r"\s+", "", raw_text))
        comp_non_ws = sum(len(re.sub(r"\s+", "", c.verbatim_text)) for c in components)
        
        coverage_ratio = (comp_non_ws / raw_non_ws) if raw_non_ws > 0 else 1.0
        
        is_coverage_valid = coverage_ratio >= MIN_COVERAGE_THRESHOLD
        if not is_coverage_valid:
            warnings.append(
                f"Low non-whitespace coverage: {coverage_ratio*100:.2f}% (Threshold: {MIN_COVERAGE_THRESHOLD*100:.2f}%)"
            )

        is_verbatim_valid = len(errors) == 0
        return is_verbatim_valid, coverage_ratio, is_coverage_valid, errors, warnings
