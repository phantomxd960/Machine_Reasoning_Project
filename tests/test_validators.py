import unittest
from bns_kb.schemas.components import Component, ComponentType
from bns_kb.schemas.relationships import Relationship, RelationType
from bns_kb.validators.structural_validator import StructuralValidator
from bns_kb.validators.source_validator import SourceValidator
from bns_kb.validators.relationship_validator import RelationshipValidator

class TestValidators(unittest.TestCase):
    def test_structural_duplicate_id(self):
        c1 = Component(
            id="BNS-SEC-1-MAIN",
            section_number=1,
            component_type=ComponentType.MAIN_PROVISION,
            verbatim_text="hello",
            char_start=0,
            char_end=5
        )
        c2 = Component(
            id="BNS-SEC-1-MAIN",
            section_number=1,
            component_type=ComponentType.SUBSECTION,
            verbatim_text="world",
            char_start=6,
            char_end=11
        )
        is_valid, errors, _ = StructuralValidator.validate([c1, c2])
        self.assertFalse(is_valid)
        self.assertTrue(any("Duplicate" in e for e in errors))

    def test_structural_cycle(self):
        c1 = Component(
            id="BNS-SEC-1-A",
            section_number=1,
            component_type=ComponentType.SUBSECTION,
            parent_id="BNS-SEC-1-B",
            verbatim_text="a",
            char_start=0,
            char_end=1
        )
        c2 = Component(
            id="BNS-SEC-1-B",
            section_number=1,
            component_type=ComponentType.SUBSECTION,
            parent_id="BNS-SEC-1-A",
            verbatim_text="b",
            char_start=2,
            char_end=3
        )
        is_valid, errors, _ = StructuralValidator.validate([c1, c2])
        self.assertFalse(is_valid)
        self.assertTrue(any("Cycle" in e for e in errors))

    def test_source_verbatim_mismatch(self):
        raw = "Except in the cases hereinafter excepted..."
        comp = Component(
            id="BNS-SEC-101-MAIN",
            section_number=101,
            component_type=ComponentType.MAIN_PROVISION,
            verbatim_text="Paraphrased non-verbatim text",
            char_start=0,
            char_end=20
        )
        is_verb_valid, _, _, errors, _ = SourceValidator.validate(raw, [comp])
        self.assertFalse(is_verb_valid)
        self.assertTrue(any("does not match" in e for e in errors))

    def test_relationship_self_loop(self):
        comp = Component(
            id="BNS-SEC-101-MAIN",
            section_number=101,
            component_type=ComponentType.MAIN_PROVISION,
            verbatim_text="abc",
            char_start=0,
            char_end=3
        )
        rel = Relationship(
            id="BNS-REL-01",
            section_number=101,
            source_id="BNS-SEC-101-MAIN",
            relation_type=RelationType.QUALIFIES,
            target_id="BNS-SEC-101-MAIN"
        )
        is_valid, errors, _ = RelationshipValidator.validate([rel], [comp], {101})
        self.assertFalse(is_valid)
        self.assertTrue(any("self-loop" in e for e in errors))

if __name__ == "__main__":
    unittest.main()
