"""
Command-Line Interface to execute First-Order Logic (FOL) Rule Generation across BNS 2023.
"""
import argparse
from bns_fol.rules.generator import BNSFOLGenerator
from bns_fol.rules.registry import RuleRegistry
from bns_fol.rules.pilot_rules import get_pilot_rules

def main():
    parser = argparse.ArgumentParser(description="Generate and Export BNS First-Order Logic (FOL) Rules")
    parser.add_argument("--pilot-only", action="store_true", help="Export only pilot rules (Sections 101, 103, 318)")
    args = parser.parse_args()

    print("🚀 Starting BNS First-Order Logic (FOL) Formalization Engine...")

    if args.pilot_only:
        print("Mode: Pilot Sections Benchmark (101, 103, 318)")
        rules = get_pilot_rules()
    else:
        print("Mode: Full Conversion across all 358 Enacted Sections")
        generator = BNSFOLGenerator()
        rules = generator.generate_all_rules()

    registry = RuleRegistry(rules)
    export_summary = registry.export()

    print("\n" + "="*70)
    print("⚖️ FIRST-ORDER LOGIC (FOL) FORMALIZATION SUMMARY")
    print("="*70)
    print(f"Total Formal FOL Rules Generated : {export_summary['total_rules']}")
    print(f"Sections Covered                 : {export_summary['sections_covered']}")
    
    # Rule types breakdown
    rule_types = {}
    for r in rules:
        rule_types[r.rule_type] = rule_types.get(r.rule_type, 0) + 1

    print("\n📊 Formal Rule Distribution:")
    for r_type, count in rule_types.items():
        print(f"  - {r_type:24s}: {count}")

    print("\n📁 Output Deliverables Generated:")
    print(f"  - Formal Rules (JSONL)         : {export_summary['formal_rules_jsonl']}")
    print(f"  - Formal Rules (CSV)           : {export_summary['formal_rules_csv']}")
    print(f"  - Predicate Ontology (JSON)    : {export_summary['predicate_ontology_json']}")
    print("="*70)

if __name__ == "__main__":
    main()
