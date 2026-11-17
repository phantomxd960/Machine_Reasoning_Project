"""
Interactive Visualizer for Reasoning Traces in Google Colab and Jupyter Notebooks.
"""
from typing import Optional
try:
    from IPython.display import HTML, display
except ImportError:
    HTML = None
    display = None

from bns_scenarios.schema import LegalScenario
from bns_verifier.engine import LegalVerificationEngine
from bns_verifier.audit_trace import VerificationAuditTrace

def render_trace_html(trace: VerificationAuditTrace, scenario: Optional[LegalScenario] = None) -> str:
    verdict_colors = {
        "SUPPORTED": "#16a34a",
        "MITIGATED_DEFENCE_APPLIED": "#ea580c",
        "INSUFFICIENT_INFORMATION": "#0284c7",
        "CONFLICTING": "#dc2626",
        "CONTRADICTED": "#b91c1c",
        "OUT_OF_SCOPE": "#64748b"
    }
    v_color = verdict_colors.get(trace.computed_verdict.value, "#64748b")
    match_tag = "<span style='background:#16a34a; color:#fff; padding:3px 8px; border-radius:4px; font-size:0.75rem; font-weight:bold;'>MATCHES GROUND TRUTH</span>" if trace.verdict_matches_ground_truth else "<span style='background:#dc2626; color:#fff; padding:3px 8px; border-radius:4px; font-size:0.75rem; font-weight:bold;'>MISMATCH</span>"

    html = f"""
    <div style="font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background:#0f172a; color:#f8fafc; padding:20px; border-radius:10px; max-width:900px; margin-bottom:20px;">
      <div style="border-bottom:2px solid #334155; padding-bottom:12px; margin-bottom:16px; display:flex; justify-content:space-between; align-items:flex-start;">
        <div>
          <span style="font-size:1.25rem; font-weight:700; color:#38bdf8;">[{trace.scenario_id}] {trace.scenario_title}</span>
          <div style="color:#94a3b8; font-size:0.85rem; margin-top:4px;">
            Target Sections: {', '.join(str(s) for s in trace.target_sections)} • Proposed Charge: <code style="color:#facc15;">{trace.proposed_conclusion}</code>
          </div>
        </div>
        <div>{match_tag}</div>
      </div>
    """

    if scenario:
        html += f"""
        <div style="background:#1e293b; padding:12px 16px; border-radius:6px; margin-bottom:16px; border-left:4px solid #38bdf8;">
          <div style="font-size:0.8rem; font-weight:700; color:#94a3b8; text-transform:uppercase; margin-bottom:4px;">Scenario Narrative</div>
          <div style="font-size:0.9rem; line-height:1.5; color:#cbd5e1;">{scenario.narrative}</div>
        </div>
        """

    html += f"""
      <div style="background:{v_color}22; border:1px solid {v_color}; padding:14px 18px; border-radius:8px; margin-bottom:16px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <span style="font-size:0.8rem; font-weight:700; color:#94a3b8; text-transform:uppercase;">Computed Verdict</span>
            <div style="font-size:1.3rem; font-weight:800; color:{v_color}; margin-top:2px;">{trace.computed_verdict.value}</div>
          </div>
          <div style="text-align:right;">
            <span style="font-size:0.75rem; color:#94a3b8;">Ground Truth:</span>
            <div style="font-size:0.95rem; font-weight:600; color:#e2e8f0;">{trace.ground_truth_verdict.value}</div>
          </div>
        </div>
        <div style="margin-top:10px; font-size:0.88rem; color:#f1f5f9; line-height:1.4;">
          <strong>Legal Explanation:</strong> {trace.final_legal_explanation}
        </div>
      </div>

      <div style="font-size:1.0rem; font-weight:700; color:#e2e8f0; margin-bottom:10px;">Step-by-Step Reasoning Trace</div>
    """

    for st in trace.reasoning_steps:
        st_color = "#3b82f6" if st.deduced_fact else ("#ef4444" if st.premises_contradicted else "#eab308")
        html += f"""
        <div style="background:#1e293b; border-left:4px solid {st_color}; padding:10px 14px; border-radius:6px; margin-bottom:10px;">
          <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
            <span style="font-weight:700; color:#e2e8f0; font-size:0.85rem;">Step {st.step_number}: {st.rule_name}</span>
            <code style="color:#38bdf8; font-size:0.75rem;">{st.rule_id}</code>
          </div>
        """
        if st.premises_satisfied:
            html += f"<div style='font-size:0.8rem; color:#4ade80;'>✔ Satisfied: <code>{', '.join(st.premises_satisfied)}</code></div>"
        if st.premises_missing:
            html += f"<div style='font-size:0.8rem; color:#facc15;'>? Missing / Unknown: <code>{', '.join(st.premises_missing)}</code></div>"
        if st.premises_contradicted:
            html += f"<div style='font-size:0.8rem; color:#f87171;'>✘ Contradicted: <code>{', '.join(st.premises_contradicted)}</code></div>"
        if st.deduced_fact:
            html += f"<div style='font-size:0.85rem; color:#38bdf8; margin-top:4px; font-weight:600;'>↳ Deduced: <code>{st.deduced_fact}</code></div>"

        html += f"<div style='font-size:0.75rem; color:#94a3b8; margin-top:4px;'>{st.step_explanation}</div></div>"

    if trace.applied_exceptions:
        html += f"<div style='background:#7c2d12; color:#fed7aa; padding:8px 12px; border-radius:6px; font-size:0.8rem; margin-top:8px;'><strong>Defences Applied:</strong> {', '.join(trace.applied_exceptions)}</div>"
    if trace.defeated_exceptions:
        html += f"<div style='background:#1e3a8a; color:#bfdbfe; padding:8px 12px; border-radius:6px; font-size:0.8rem; margin-top:8px;'><strong>Defences Overridden by Provisos:</strong> {', '.join(trace.defeated_exceptions)}</div>"
    if trace.unresolved_exceptions:
        html += f"<div style='background:#713f12; color:#fef08a; padding:8px 12px; border-radius:6px; font-size:0.8rem; margin-top:8px;'><strong>Raised Defences Still Unresolved:</strong> {', '.join(trace.unresolved_exceptions)}</div>"
    if trace.applicable_sanctions:
        html += f"<div style='background:#14532d; color:#bbf7d0; padding:8px 12px; border-radius:6px; font-size:0.8rem; margin-top:8px;'><strong>Applicable Sanctions:</strong> <code>{'; '.join(trace.applicable_sanctions)}</code></div>"
    if trace.fact_warnings:
        html += f"<div style='background:#3f3f46; color:#e4e4e7; padding:8px 12px; border-radius:6px; font-size:0.8rem; margin-top:8px;'><strong>Fact Warnings:</strong> {'; '.join(trace.fact_warnings)}</div>"

    html += "</div>"
    return html

def display_scenario_trace(scenario_id: str = "SCEN-BNS-004"):
    from bns_scenarios.benchmark_suite import get_benchmark_scenarios
    scens = {s.scenario_id: s for s in get_benchmark_scenarios()}
    sc = scens.get(scenario_id)
    if not sc:
        print(f"Scenario {scenario_id} not found.")
        return
    engine = LegalVerificationEngine()
    trace = engine.verify_scenario(sc)
    html = render_trace_html(trace, sc)
    display(HTML(html))
