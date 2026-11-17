"""
Main Command-Line Interface to run the BNS Knowledge Base Construction Pipeline.
"""
import argparse
import json
from bns_kb.pipeline import BNSKnowledgeBasePipeline

def main():
    parser = argparse.ArgumentParser(description="Build and Validate BNS 2023 Knowledge Base")
    parser.add_argument("--pilot", action="store_true", help="Run only pilot sections (101, 103, 318)")
    parser.add_argument("--no-checkpoint", action="store_true", help="Ignore existing checkpoints")
    args = parser.parse_args()

    pipeline = BNSKnowledgeBasePipeline(use_checkpoint=not args.no_checkpoint)

    target_desc = "Pilot Sections (101, 103, 318)" if args.pilot else "All 358 Enacted Sections"
    print(f"🚀 Starting BNS Knowledge Base Construction Pipeline: {target_desc}")

    summary = pipeline.run(pilot_only=args.pilot)

    print("\n" + "="*70)
    print("🎯 EXTRACTION & VALIDATION PIPELINE EXECUTION SUMMARY")
    print("="*70)
    print(f"Total Sections Processed   : {summary['total_sections_processed']}")
    print(f"Extracted / Reused (ckpt)  : {summary['sections_extracted']} / {summary['sections_reused_from_checkpoint']}")
    print(f"Syntactically Validated    : {summary['syntactically_validated_sections']} ({summary['validation_pass_rate_pct']}%)")
    print(f"Zero-Warning Sections      : {summary['zero_warning_sections']}")
    print(f"Mean Character Coverage    : {summary['mean_coverage_ratio_pct']}%")
    print(f"Min Character Coverage     : {summary['min_coverage_ratio_pct']}%")
    print(f"Total Legal Components     : {summary['total_components']}")
    print(f"Total Legal Relationships  : {summary['total_relationships']}")
    
    print("\n📊 Component Distribution:")
    for c_type, count in summary['component_distribution'].items():
        print(f"  - {c_type:20s}: {count}")

    print("\n🔗 Relationship Distribution:")
    for r_type, count in summary['relationship_distribution'].items():
        print(f"  - {r_type:26s}: {count}")

    print("\n📁 Output Deliverables Generated:")
    for name, path in summary['files'].items():
        print(f"  - {name:26s}: {path}")
    print("="*70)

if __name__ == "__main__":
    main()
