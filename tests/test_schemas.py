import unittest
from bns_kb.schemas.components import Component, ComponentType
from bns_kb.schemas.relationships import Relationship, RelationType
from bns_kb.schemas.provenance import SectionStorageRecord, ProvenanceMetadata, ValidationReport, ValidationStatus, ReviewStatus

class TestSchemas(unittest.TestCase):
    def test_component_creation(self):
        comp = Component(
            id="BNS-SEC-101-MAIN",
            section_number=101,
            component_type=ComponentType.MAIN_PROVISION,
            verbatim_text="culpable homicide is murder",
            char_start=0,
            char_end=26
        )
        self.assertEqual(comp.id, "BNS-SEC-101-MAIN")
        self.assertEqual(comp.component_type, ComponentType.MAIN_PROVISION)
        self.assertFalse(comp.is_punishment)

    def test_relationship_creation(self):
        rel = Relationship(
            id="BNS-REL-101-001",
            section_number=101,
            source_id="BNS-SEC-101-MAIN",
            relation_type=RelationType.HAS_CHILD,
            target_id="BNS-SEC-101-CL-A",
            evidence_quote="(a) if the act..."
        )
        self.assertEqual(rel.relation_type, RelationType.HAS_CHILD)
        self.assertEqual(rel.confidence, 1.0)

    def test_storage_record_serialization(self):
        comp = Component(
            id="BNS-SEC-101-MAIN",
            section_number=101,
            component_type=ComponentType.MAIN_PROVISION,
            verbatim_text="text",
            char_start=0,
            char_end=4
        )
        prov = ProvenanceMetadata(
            raw_text_sha256="abc123hash",
            extractor_version="1.0",
            schema_version="1.0"
        )
        val = ValidationReport(
            section_number=101,
            status=ValidationStatus.VALIDATED_SYNTAX,
            structural_valid=True,
            source_verbatim_valid=True,
            coverage_ratio=1.0,
            coverage_valid=True,
            relationship_valid=True
        )
        record = SectionStorageRecord(
            section_number=101,
            chapter_number=6,
            chapter_name="Of Offences Affecting the Human Body",
            section_name="Murder",
            raw_text="text",
            provenance=prov,
            validation=val,
            components=[comp],
            relationships=[]
        )
        json_data = record.model_dump_json()
        self.assertIn("BNS-SEC-101-MAIN", json_data)
        self.assertIn("PENDING_REVIEW", json_data)

if __name__ == "__main__":
    unittest.main()
