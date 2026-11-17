"""
Systematic First-Order Logic Rule Generator across all BNS 2023 Sections.
Integrates gold-standard pilot formalizations and automated statutory derivation.
"""
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Set, Optional
from bns_fol.config import KB_JSONL_PATH, PILOT_SECTIONS
from bns_fol.rules.schema import StatutoryRule
from bns_fol.rules.pilot_rules import get_pilot_rules

class BNSFOLGenerator:
    """
    Transforms structured Knowledge Base components and relationships into formal First-Order Logic rules.
    """
    def __init__(self, kb_path: Optional[Path] = None):
        self.kb_path = Path(kb_path or KB_JSONL_PATH)

    def generate_all_rules(self) -> List[StatutoryRule]:
        if not self.kb_path.exists():
            raise FileNotFoundError(f"Knowledge Base JSONL not found at: {self.kb_path}")

        all_rules: List[StatutoryRule] = []

        # 1. Add gold-standard pilot rules (Sections 101, 103, 318)
        pilot_rules = get_pilot_rules()
        pilot_rule_ids = {r.rule_id for r in pilot_rules}
        all_rules.extend(pilot_rules)

        # 2. Process all 358 sections from Knowledge Base
        with open(self.kb_path, "r", encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                sec_num = rec["section_number"]
                sec_name = rec["section_name"]
                comps = rec.get("components", [])

                # Skip pilot sections since they are hand-crafted to gold-standard perfection
                if sec_num in PILOT_SECTIONS:
                    continue

                sec_rules = self._generate_section_rules(sec_num, sec_name, comps, rec.get("relationships", []))
                all_rules.extend(sec_rules)

        # Every auto-generated rule is a schematic skeleton (placeholder predicates); only pilot rules are GOLD.
        return [r if r.formalization_level == "GOLD" else r.model_copy(update={"formalization_level": "SCHEMATIC"})
                for r in all_rules]

    def _generate_section_rules(
        self,
        sec_num: int,
        sec_name: str,
        components: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]]
    ) -> List[StatutoryRule]:
        rules: List[StatutoryRule] = []
        clean_name = re.sub(r"[^A-Za-z0-9]", "", sec_name.title())

        # Check for punishment provisions
        for c in components:
            c_id = c["id"]
            c_type = c["component_type"]
            text = c["verbatim_text"]
            is_punish = c.get("is_punishment", False)

            if is_punish or c_type == "PUNISHMENT":
                rule_id = f"RULE-{c_id}"
                rule_name = f"Punishment for {sec_name} ({c.get('statutory_label') or 'Main'})"
                
                # Extract sanction terms
                sanction_match = re.search(r'\b(?:punished with|punishable with)\s+([^.,;]+)', text, re.I)
                sanction_desc = sanction_match.group(1).strip() if sanction_match else "StatutorySanction"
                clean_sanction = re.sub(r"[^A-Za-z0-9]", "", sanction_desc.title())[:40]

                premise = f"CommitsOffence_{clean_name}(x)"
                conclusion = f"LiableToPunishment(x, {clean_sanction})"

                rules.append(StatutoryRule(
                    rule_id=rule_id,
                    section_number=sec_num,
                    source_component_id=c_id,
                    rule_name=rule_name,
                    rule_type="PUNISHMENT_MAPPING",
                    variables=["x"],
                    premises=[premise],
                    conclusion=conclusion,
                    formula_unicode=f"∀x. {premise} → {conclusion}",
                    formula_latex=rf"\forall x \ (\text{{{premise}}} \to \text{{{conclusion}}})",
                    formula_ascii=f"ALL x. ({premise} -> {conclusion})",
                    description=f"Statutory penalty under BNS Section {sec_num}: {text[:100]}..."
                ))

            elif c_type == "EXCEPTION":
                rule_id = f"RULE-{c_id}"
                label = c.get("statutory_label") or "Exception"
                exc_pred = f"AppliesException_{clean_name}_{re.sub(r'[^A-Za-z0-9]', '', label)}"

                rules.append(StatutoryRule(
                    rule_id=rule_id,
                    section_number=sec_num,
                    source_component_id=c_id,
                    rule_name=f"{label} for {sec_name}",
                    rule_type="EXCEPTION_DEFENCE",
                    variables=["x"],
                    premises=[f"SatisfiesConditions_{clean_name}_{label.replace(' ', '')}(x)"],
                    conclusion=f"{exc_pred}(x)",
                    formula_unicode=f"∀x. SatisfiesConditions_{clean_name}_{label.replace(' ', '')}(x) → {exc_pred}(x)",
                    formula_latex=rf"\forall x \ (\text{{SatisfiesConditions}}(x) \to \text{{{exc_pred}}}(x))",
                    formula_ascii=f"ALL x. (SatisfiesConditions_{clean_name}_{label.replace(' ', '')}(x) -> {exc_pred}(x))",
                    description=f"Statutory exception under Section {sec_num}: {text[:100]}..."
                ))

            elif c_type == "DEFINITIONAL_EXPANSION" or c.get("is_definition", False):
                rule_id = f"RULE-{c_id}"
                rules.append(StatutoryRule(
                    rule_id=rule_id,
                    section_number=sec_num,
                    source_component_id=c_id,
                    rule_name=f"Definition of {sec_name}",
                    rule_type="DEFINITIONAL_EXPANSION",
                    variables=["x"],
                    premises=[f"SatisfiesElements_{clean_name}(x)"],
                    conclusion=f"DefinedAs_{clean_name}(x)",
                    formula_unicode=f"∀x. SatisfiesElements_{clean_name}(x) → DefinedAs_{clean_name}(x)",
                    formula_latex=rf"\forall x \ (\text{{SatisfiesElements}}_{clean_name}(x) \to \text{{DefinedAs}}_{clean_name}(x))",
                    formula_ascii=f"ALL x. (SatisfiesElements_{clean_name}(x) -> DefinedAs_{clean_name}(x))",
                    description=f"Statutory definition under Section {sec_num}: {text[:100]}..."
                ))

            else:
                # Standard substantive provision clause / subsection
                rule_id = f"RULE-{c_id}"
                label = c.get("statutory_label") or "Provision"
                clean_lbl = re.sub(r"[^A-Za-z0-9]", "", label)
                premise = f"Satisfies_{clean_name}_{clean_lbl}(x)" if clean_lbl else f"Satisfies_{clean_name}(x)"
                conclusion = f"CommitsOffence_{clean_name}(x)"

                rules.append(StatutoryRule(
                    rule_id=rule_id,
                    section_number=sec_num,
                    source_component_id=c_id,
                    rule_name=f"Elements for {sec_name} ({label})",
                    rule_type="OFFENCE_ELEMENT",
                    variables=["x"],
                    premises=[premise],
                    conclusion=conclusion,
                    formula_unicode=f"∀x. {premise} → {conclusion}",
                    formula_latex=rf"\forall x \ (\text{{{premise}}} \to \text{{{conclusion}}})",
                    formula_ascii=f"ALL x. ({premise} -> {conclusion})",
                    description=f"Statutory provision elements under Section {sec_num} ({label}): {text[:100]}..."
                ))

        return rules
