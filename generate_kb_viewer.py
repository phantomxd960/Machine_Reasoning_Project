"""
generate_kb_viewer.py
Refreshes the self-contained knowledge-base visualiser (view_kb.html) from
data/output/knowledge_base.jsonl by replacing the page's embedded `const data = [...]` array.
Run it after `python run_kb_pipeline.py`.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VIEW = ROOT / "view_kb.html"
KB = ROOT / "data" / "output" / "knowledge_base.jsonl"

EXTRA_CSS = "  .comp-type-DEFINITION { border-left-color: var(--badge-explanation); }\n  .comp-type-SUBCLAUSE { border-left-color: var(--badge-clause); }\n"


def main():
    html = VIEW.read_text(encoding="utf-8")
    records = [json.loads(l) for l in KB.read_text(encoding="utf-8").splitlines() if l.strip()]
    payload = json.dumps(records, ensure_ascii=False).replace("</", "<\\/")

    start = html.index("const data = ")
    end = html.index("];\n", start) + 2
    html = html[:start] + "const data = " + payload + ";" + html[end:]

    if ".comp-type-DEFINITION" not in html:
        anchor = "  .comp-type-MAIN_PROVISION"
        html = html.replace(anchor, EXTRA_CSS + anchor, 1)

    VIEW.write_text(html, encoding="utf-8")
    comps = sum(len(r["components"]) for r in records)
    rels = sum(len(r["relationships"]) for r in records)
    print(f"Updated {VIEW.name}: {len(records)} sections, {comps} components, {rels} relationships.")


if __name__ == "__main__":
    main()
