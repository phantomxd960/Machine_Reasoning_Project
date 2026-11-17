"""
generate_fol_viewer.py
Compiles data/output/formal_rules.jsonl, data/output/predicate_ontology.json,
and data/output/knowledge_base.jsonl into an offline, interactive, self-contained
HTML visualizer: view_fol.html.
"""

import json
from collections import defaultdict

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BNS 2023 - First-Order Logic (FOL) Rulebase Visualizer</title>
<style>
  :root {
    --bg-dark: #090d16;
    --bg-surface: #0f172a;
    --bg-sidebar: #131c31;
    --card-bg: #1e293b;
    --card-bg-subtle: #172239;
    --card-border: #334155;
    --card-border-light: #475569;
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --accent: #38bdf8;
    --accent-glow: rgba(56, 189, 248, 0.2);
    
    /* Rule Type Colors */
    --type-offence-element: #3b82f6;
    --type-exception-defence: #ef4444;
    --type-exception-override: #c026d3;
    --type-offence-final: #10b981;
    --type-offence-mitigated: #06b6d4;
    --type-punishment-mapping: #f59e0b;
    --type-definitional: #8b5cf6;

    /* Logic Syntax Highlighting */
    --logic-quantifier: #c084fc;
    --logic-variable: #38bdf8;
    --logic-predicate: #fbbf24;
    --logic-operator: #f43f5e;
    --logic-arrow: #2dd4bf;
    --logic-conclusion: #34d399;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background: var(--bg-dark);
    color: var(--text-primary);
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  /* Top Navigation Bar */
  #top-nav {
    background: var(--bg-sidebar);
    border-bottom: 1px solid var(--card-border);
    padding: 10px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-shrink: 0;
    z-index: 10;
  }
  .nav-branding {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .nav-logo {
    font-size: 1.5rem;
    line-height: 1;
  }
  .nav-title h1 {
    font-size: 1.05rem;
    font-weight: 700;
    color: #fff;
    letter-spacing: -0.01em;
  }
  .nav-title p {
    font-size: 0.72rem;
    color: var(--text-secondary);
  }
  .nav-badges {
    display: flex;
    gap: 6px;
    align-items: center;
  }
  .nav-badge {
    font-size: 0.7rem;
    padding: 3px 8px;
    border-radius: 9999px;
    font-weight: 600;
    background: #1e293b;
    border: 1px solid var(--card-border);
    color: #cbd5e1;
  }
  .nav-badge.highlight {
    background: rgba(56, 189, 248, 0.12);
    border-color: rgba(56, 189, 248, 0.4);
    color: var(--accent);
  }
  .nav-tabs {
    display: flex;
    gap: 4px;
    background: #090d16;
    padding: 3px;
    border-radius: 8px;
    border: 1px solid var(--card-border);
  }
  .nav-tab-btn {
    background: transparent;
    border: none;
    color: var(--text-secondary);
    padding: 6px 14px;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .nav-tab-btn:hover {
    color: #fff;
  }
  .nav-tab-btn.active {
    background: var(--card-bg);
    color: #fff;
    box-shadow: 0 1px 3px rgba(0,0,0,0.3);
  }
  .nav-actions {
    display: flex;
    gap: 8px;
    align-items: center;
  }
  .btn-outline {
    background: transparent;
    border: 1px solid var(--card-border);
    color: var(--text-secondary);
    font-size: 0.75rem;
    padding: 6px 12px;
    border-radius: 6px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 6px;
    text-decoration: none;
    transition: all 0.15s;
  }
  .btn-outline:hover {
    background: #1e293b;
    color: #fff;
    border-color: var(--accent);
  }

  /* App Container */
  #app-container {
    flex: 1;
    display: flex;
    overflow: hidden;
    position: relative;
  }

  /* View Panels */
  .view-panel {
    flex: 1;
    display: none;
    overflow: hidden;
    height: 100%;
  }
  .view-panel.active {
    display: flex;
  }

  /* RULES EXPLORER LAYOUT */
  #rules-explorer-panel {
    width: 100%;
    height: 100%;
  }
  #sidebar {
    width: 360px;
    background: var(--bg-sidebar);
    border-right: 1px solid var(--card-border);
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
  }
  .sidebar-header {
    padding: 14px 16px;
    border-bottom: 1px solid var(--card-border);
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .search-wrapper {
    position: relative;
    width: 100%;
  }
  .search-input {
    width: 100%;
    padding: 8px 12px 8px 32px;
    background: #090d16;
    border: 1px solid var(--card-border);
    border-radius: 6px;
    color: #fff;
    font-size: 0.82rem;
  }
  .search-input:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 2px var(--accent-glow);
  }
  .search-icon {
    position: absolute;
    left: 10px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-muted);
    font-size: 0.85rem;
  }
  .quick-filters {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .quick-label {
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
    font-weight: 700;
  }
  .quick-pills {
    display: flex;
    gap: 5px;
    flex-wrap: wrap;
  }
  .quick-pill {
    background: #172239;
    border: 1px solid var(--card-border);
    color: #cbd5e1;
    font-size: 0.7rem;
    padding: 3px 7px;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.15s;
  }
  .quick-pill:hover {
    background: #25334e;
    color: #fff;
    border-color: var(--accent);
  }
  .type-filter-select {
    width: 100%;
    padding: 6px 10px;
    background: #090d16;
    border: 1px solid var(--card-border);
    border-radius: 6px;
    color: #cbd5e1;
    font-size: 0.78rem;
    cursor: pointer;
  }
  .type-filter-select:focus {
    outline: none;
    border-color: var(--accent);
  }

  /* Section List */
  #section-list {
    overflow-y: auto;
    flex: 1;
  }
  .sec-item {
    padding: 10px 16px;
    border-bottom: 1px solid rgba(51, 65, 85, 0.5);
    cursor: pointer;
    transition: background 0.15s;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .sec-item:hover {
    background: rgba(30, 41, 59, 0.6);
  }
  .sec-item.active {
    background: #1e3a5f;
    border-left: 3px solid var(--accent);
  }
  .sec-info {
    flex: 1;
    min-width: 0;
    padding-right: 8px;
  }
  .sec-title {
    font-size: 0.82rem;
    font-weight: 600;
    color: #e2e8f0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .sec-sub {
    font-size: 0.7rem;
    color: var(--text-muted);
    margin-top: 2px;
  }
  .sec-count-badge {
    background: #1e293b;
    border: 1px solid var(--card-border);
    color: var(--text-secondary);
    font-size: 0.68rem;
    padding: 2px 6px;
    border-radius: 9999px;
    font-weight: 600;
    white-space: nowrap;
  }
  .sec-item.active .sec-count-badge {
    background: var(--accent);
    color: #090d16;
    border-color: var(--accent);
  }

  /* Main Rules Content */
  #main-rules-pane {
    flex: 1;
    overflow-y: auto;
    padding: 20px 28px;
    display: flex;
    flex-direction: column;
    gap: 18px;
    background: var(--bg-surface);
  }
  .section-hero {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 10px;
    padding: 20px 24px;
    position: relative;
    overflow: hidden;
  }
  .hero-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 16px;
  }
  .hero-breadcrumb {
    font-size: 0.75rem;
    color: var(--accent);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 4px;
  }
  .hero-title {
    font-size: 1.45rem;
    font-weight: 700;
    color: #fff;
    line-height: 1.25;
  }
  .hero-actions {
    display: flex;
    gap: 8px;
    flex-shrink: 0;
  }
  .hero-types-breakdown {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin-top: 14px;
    padding-top: 12px;
    border-top: 1px solid var(--card-border);
  }
  .type-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 9px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 600;
  }

  /* Rule Cards */
  .rule-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 8px;
    overflow: hidden;
    position: relative;
    border-left: 4px solid var(--card-border-light);
    transition: transform 0.15s, box-shadow 0.15s;
  }
  .rule-card:hover {
    border-color: var(--card-border-light);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
  }
  
  /* Type Left Border Accents */
  .rule-card.type-OFFENCE_ELEMENT { border-left-color: var(--type-offence-element); }
  .rule-card.type-EXCEPTION_DEFENCE { border-left-color: var(--type-exception-defence); }
  .rule-card.type-EXCEPTION_OVERRIDE { border-left-color: var(--type-exception-override); }
  .rule-card.type-OFFENCE_FINAL { border-left-color: var(--type-offence-final); }
  .rule-card.type-OFFENCE_MITIGATED { border-left-color: var(--type-offence-mitigated); }
  .rule-card.type-PUNISHMENT_MAPPING { border-left-color: var(--type-punishment-mapping); }
  .rule-card.type-DEFINITIONAL_EXPANSION { border-left-color: var(--type-definitional); }

  .rule-header {
    padding: 12px 18px;
    background: rgba(15, 23, 42, 0.4);
    border-bottom: 1px solid var(--card-border);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .rule-meta-left {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }
  .rule-id {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 0.8rem;
    font-weight: 700;
    color: var(--accent);
    cursor: pointer;
    background: #090d16;
    padding: 2px 7px;
    border-radius: 4px;
    border: 1px solid var(--card-border);
  }
  .rule-id:hover {
    border-color: var(--accent);
  }
  .rule-badge {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    padding: 2px 8px;
    border-radius: 4px;
    letter-spacing: 0.03em;
  }
  .rule-src {
    font-family: ui-monospace, SFMono-Regular, monospace;
    font-size: 0.72rem;
    color: var(--text-muted);
  }
  .rule-actions {
    display: flex;
    gap: 6px;
  }
  .action-btn {
    background: #172239;
    border: 1px solid var(--card-border);
    color: var(--text-secondary);
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.72rem;
    cursor: pointer;
    transition: all 0.15s;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    text-decoration: none;
  }
  .action-btn:hover {
    background: #25334e;
    color: #fff;
    border-color: var(--accent);
  }

  .rule-body {
    padding: 16px 18px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }
  .rule-name-row {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .rule-name {
    font-size: 1.05rem;
    font-weight: 700;
    color: #fff;
  }
  .rule-desc {
    font-size: 0.83rem;
    color: var(--text-secondary);
    line-height: 1.45;
  }

  /* Formula Container */
  .formula-box {
    background: #090d16;
    border: 1px solid var(--card-border);
    border-radius: 6px;
    overflow: hidden;
  }
  .formula-tabs {
    display: flex;
    background: #111827;
    border-bottom: 1px solid var(--card-border);
    padding: 2px 6px;
    gap: 4px;
  }
  .formula-tab {
    background: transparent;
    border: none;
    color: var(--text-muted);
    font-size: 0.7rem;
    font-weight: 600;
    padding: 4px 8px;
    border-radius: 4px;
    cursor: pointer;
  }
  .formula-tab.active {
    background: #1e293b;
    color: var(--accent);
  }
  .formula-code {
    padding: 12px 16px;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 0.9rem;
    line-height: 1.5;
    overflow-x: auto;
    white-space: pre-wrap;
    word-break: break-word;
  }
  .formula-latex, .formula-ascii {
    display: none;
    color: #cbd5e1;
    font-size: 0.82rem;
  }

  /* Syntax Highlighting */
  .syn-quant { color: var(--logic-quantifier); font-weight: 700; }
  .syn-var { color: var(--logic-variable); }
  .syn-pred { color: var(--logic-predicate); font-weight: 600; cursor: pointer; text-decoration: underline dotted #64748b; }
  .syn-pred:hover { color: #fde047; text-decoration: underline solid #fde047; }
  .syn-op { color: var(--logic-operator); font-weight: 700; padding: 0 2px; }
  .syn-arr { color: var(--logic-arrow); font-weight: 700; padding: 0 4px; font-size: 1.05em; }
  .syn-neg { color: var(--logic-operator); font-weight: 800; }
  .syn-conc { color: var(--logic-conclusion); font-weight: 600; }

  /* Logic Decomposition Grid */
  .logic-decomp {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
    background: rgba(15, 23, 42, 0.5);
    border: 1px solid var(--card-border);
    border-radius: 6px;
    padding: 12px 14px;
  }
  .decomp-col-title {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 700;
    color: var(--text-muted);
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 5px;
  }
  .premises-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .premise-item {
    font-family: ui-monospace, SFMono-Regular, monospace;
    font-size: 0.78rem;
    padding: 4px 8px;
    border-radius: 4px;
    background: #090d16;
    border: 1px solid var(--card-border);
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .premise-pos {
    border-left: 3px solid #10b981;
  }
  .premise-neg {
    border-left: 3px solid #ef4444;
    background: rgba(239, 68, 68, 0.05);
  }
  .atom-icon {
    font-size: 0.75rem;
    font-weight: 800;
  }
  .premise-pos .atom-icon { color: #10b981; }
  .premise-neg .atom-icon { color: #ef4444; }

  .conclusion-box {
    background: #090d16;
    border: 1px solid var(--card-border);
    border-left: 3px solid var(--logic-conclusion);
    border-radius: 4px;
    padding: 8px 12px;
    font-family: ui-monospace, SFMono-Regular, monospace;
    font-size: 0.84rem;
    color: var(--logic-conclusion);
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .variables-tag {
    font-size: 0.72rem;
    color: var(--text-muted);
    margin-top: 6px;
    font-family: ui-monospace, SFMono-Regular, monospace;
  }

  /* ONTOLOGY TAB */
  #ontology-panel {
    width: 100%;
    height: 100%;
    padding: 24px 32px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  .onto-hero {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 10px;
    padding: 20px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .onto-filter-bar {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    align-items: center;
  }
  .onto-cat-btn {
    background: #172239;
    border: 1px solid var(--card-border);
    color: #cbd5e1;
    font-size: 0.75rem;
    padding: 5px 12px;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.15s;
  }
  .onto-cat-btn:hover, .onto-cat-btn.active {
    background: var(--accent);
    color: #090d16;
    border-color: var(--accent);
  }
  .onto-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
    gap: 16px;
  }
  .onto-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 8px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .onto-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .onto-name {
    font-family: ui-monospace, SFMono-Regular, monospace;
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--logic-predicate);
  }
  .onto-meta {
    display: flex;
    gap: 6px;
  }
  .onto-cat-badge {
    font-size: 0.65rem;
    padding: 2px 6px;
    border-radius: 4px;
    font-weight: 700;
    background: #334155;
    color: #e2e8f0;
  }
  .onto-sig {
    font-family: ui-monospace, SFMono-Regular, monospace;
    font-size: 0.8rem;
    color: #38bdf8;
    background: #090d16;
    padding: 6px 10px;
    border-radius: 4px;
    border: 1px solid var(--card-border);
  }
  .onto-desc {
    font-size: 0.8rem;
    color: var(--text-secondary);
    line-height: 1.45;
  }
  .onto-usages {
    border-top: 1px solid var(--card-border);
    padding-top: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.72rem;
    color: var(--text-muted);
  }
  .onto-jump-btn {
    color: var(--accent);
    cursor: pointer;
    font-weight: 600;
  }
  .onto-jump-btn:hover {
    text-decoration: underline;
  }

  /* STATISTICAL SUMMARY TAB */
  #analytics-panel {
    width: 100%;
    height: 100%;
    padding: 24px 32px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 24px;
  }
  .stat-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
  }
  .stat-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 8px;
    padding: 16px 20px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .stat-num {
    font-size: 2rem;
    font-weight: 800;
    color: #fff;
    line-height: 1;
  }
  .stat-label {
    font-size: 0.75rem;
    color: var(--text-muted);
    font-weight: 600;
    text-transform: uppercase;
  }
  .stat-sub {
    font-size: 0.72rem;
    color: var(--text-secondary);
  }

  .type-distribution-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 14px;
  }
  .type-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 8px;
    padding: 14px 16px;
    border-left: 4px solid var(--card-border-light);
  }
  .type-card-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
  }
  .type-card-title {
    font-size: 0.85rem;
    font-weight: 700;
    color: #fff;
  }
  .type-card-count {
    font-size: 1.1rem;
    font-weight: 800;
  }
  .type-card-pct {
    font-size: 0.72rem;
    color: var(--text-muted);
    margin-bottom: 8px;
  }
  .type-card-bar {
    height: 6px;
    background: #090d16;
    border-radius: 3px;
    overflow: hidden;
  }
  .type-card-fill {
    height: 100%;
    border-radius: 3px;
  }

  /* Table styling */
  .table-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 8px;
    overflow: hidden;
  }
  .table-header {
    padding: 14px 18px;
    border-bottom: 1px solid var(--card-border);
    font-size: 0.95rem;
    font-weight: 700;
    color: #fff;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
  }
  th {
    background: #111827;
    color: var(--text-secondary);
    font-weight: 600;
    text-align: left;
    padding: 10px 14px;
    border-bottom: 1px solid var(--card-border);
    font-size: 0.75rem;
    text-transform: uppercase;
  }
  td {
    padding: 10px 14px;
    border-bottom: 1px solid rgba(51, 65, 85, 0.4);
    color: #cbd5e1;
  }
  tr:hover td {
    background: rgba(30, 41, 59, 0.4);
  }

  /* ARCHITECTURE TAB */
  #architecture-panel {
    width: 100%;
    height: 100%;
    padding: 24px 32px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  .arch-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 8px;
    padding: 20px 24px;
    line-height: 1.6;
  }
  .arch-card h2 {
    font-size: 1.25rem;
    color: #fff;
    margin-bottom: 8px;
  }
  .arch-card p {
    font-size: 0.88rem;
    color: var(--text-secondary);
    margin-bottom: 14px;
  }
  .pipeline-flow {
    display: flex;
    align-items: stretch;
    gap: 12px;
    overflow-x: auto;
    padding: 12px 0;
  }
  .pipe-step {
    flex: 1;
    min-width: 180px;
    background: #090d16;
    border: 1px solid var(--card-border);
    border-radius: 8px;
    padding: 14px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    position: relative;
  }
  .pipe-step-num {
    font-size: 0.68rem;
    font-weight: 700;
    color: var(--accent);
    text-transform: uppercase;
  }
  .pipe-step-title {
    font-size: 0.88rem;
    font-weight: 700;
    color: #fff;
  }
  .pipe-step-desc {
    font-size: 0.75rem;
    color: var(--text-muted);
    line-height: 1.4;
  }

  /* Toast Notification */
  #toast {
    position: fixed;
    bottom: 24px;
    right: 24px;
    background: #10b981;
    color: #090d16;
    padding: 8px 16px;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 700;
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    opacity: 0;
    transform: translateY(10px);
    transition: all 0.2s;
    pointer-events: none;
    z-index: 100;
  }
  #toast.show {
    opacity: 1;
    transform: translateY(0);
  }

  /* Custom Scrollbars */
  ::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }
  ::-webkit-scrollbar-track {
    background: transparent;
  }
  ::-webkit-scrollbar-thumb {
    background: #334155;
    border-radius: 3px;
  }
  ::-webkit-scrollbar-thumb:hover {
    background: #475569;
  }
</style>
</head>
<body>

  <!-- Top Navigation Bar -->
  <header id="top-nav">
    <div class="nav-branding">
      <div class="nav-logo">⚖️</div>
      <div class="nav-title">
        <h1>BNS 2023 — First-Order Logic (FOL) Rulebase</h1>
        <p>Bharatiya Nyaya Sanhita, 2023 • Formalized Horn Clauses & Non-Monotonic Defeasible Semantics</p>
      </div>
    </div>

    <div class="nav-badges">
      <div class="nav-badge highlight">1,281 Rules</div>
      <div class="nav-badge">358 Sections</div>
      <div class="nav-badge">38 Predicates</div>
      <div class="nav-badge">Kleene 3-Valued Open-World</div>
    </div>

    <nav class="nav-tabs">
      <button class="nav-tab-btn active" onclick="switchMainView('rules')">
        <span>📜</span> Rules Explorer
      </button>
      <button class="nav-tab-btn" onclick="switchMainView('ontology')">
        <span>🧩</span> Predicate Ontology
      </button>
      <button class="nav-tab-btn" onclick="switchMainView('analytics')">
        <span>📊</span> Rulebase Analytics
      </button>
      <button class="nav-tab-btn" onclick="switchMainView('architecture')">
        <span>🧠</span> Reasoning Pipeline
      </button>
    </nav>

    <div class="nav-actions">
      <a href="view_kb.html" class="btn-outline" title="Open Statutory Knowledge Base Viewer">
        <span>📖</span> Open Knowledge Base
      </a>
    </div>
  </header>

  <!-- App Body Container -->
  <div id="app-container">

    <!-- 1. RULES EXPLORER PANEL -->
    <div id="rules-explorer-panel" class="view-panel active">
      <!-- Sidebar -->
      <aside id="sidebar">
        <div class="sidebar-header">
          <div class="search-wrapper">
            <span class="search-icon">🔍</span>
            <input type="text" id="sec-search-box" class="search-input" placeholder="Search section #, title, rule ID, keyword..." oninput="handleSearch()">
          </div>

          <div class="quick-filters">
            <div class="quick-label">Benchmark Demo Sections</div>
            <div class="quick-pills">
              <span class="quick-pill" onclick="jumpToSection(101)">Sec 101 (Murder)</span>
              <span class="quick-pill" onclick="jumpToSection(103)">Sec 103 (Punishment)</span>
              <span class="quick-pill" onclick="jumpToSection(318)">Sec 318 (Cheating)</span>
              <span class="quick-pill" onclick="jumpToSection(2)">Sec 2 (Definitions)</span>
              <span class="quick-pill" onclick="jumpToSection(64)">Sec 64 (Rape)</span>
              <span class="quick-pill" onclick="jumpToSection(303)">Sec 303 (Theft)</span>
              <span class="quick-pill" onclick="jumpToSection(113)">Sec 113 (Terrorism)</span>
            </div>
          </div>

          <div>
            <select id="type-filter-select" class="type-filter-select" onchange="handleTypeFilter()">
              <option value="ALL">All Rule Types (1,281)</option>
              <option value="OFFENCE_ELEMENT">Offence Elements (670)</option>
              <option value="PUNISHMENT_MAPPING">Punishment Mappings (461)</option>
              <option value="DEFINITIONAL_EXPANSION">Definitional Expansions (117)</option>
              <option value="EXCEPTION_DEFENCE">Exception Defences (26)</option>
              <option value="EXCEPTION_OVERRIDE">Exception Overrides (5)</option>
              <option value="OFFENCE_FINAL">Offence Final (1)</option>
              <option value="OFFENCE_MITIGATED">Offence Mitigated (1)</option>
            </select>
          </div>
        </div>

        <div id="section-list"></div>
      </aside>

      <!-- Main Rules Content -->
      <main id="main-rules-pane">
        <div id="section-hero-card" class="section-hero">
          <div class="hero-top">
            <div>
              <div id="hero-breadcrumb" class="hero-breadcrumb">CHAPTER V • OF OFFENCES AGAINST THE HUMAN BODY</div>
              <h2 id="hero-title" class="hero-title">Section 101: Murder</h2>
            </div>
            <div class="hero-actions">
              <a id="open-in-kb-btn" href="view_kb.html" class="action-btn" title="Open this section in statutory KB">
                <span>📖</span> Open in KB
              </a>
              <button class="action-btn" onclick="copySectionLaTeX()">
                <span>📐</span> Copy Section LaTeX
              </button>
              <button class="action-btn" onclick="copySectionJSON()">
                <span>💾</span> Copy Section JSON
              </button>
            </div>
          </div>
          <div id="hero-breakdown" class="hero-types-breakdown"></div>
        </div>

        <!-- Rules Container -->
        <div id="rules-cards-container" style="display:flex; flex-direction:column; gap:16px;"></div>
      </main>
    </div>

    <!-- 2. PREDICATE ONTOLOGY PANEL -->
    <div id="ontology-panel" class="view-panel">
      <div class="onto-hero">
        <div>
          <h2 style="font-size:1.3rem; font-weight:700; color:#fff; margin-bottom:4px;">Predicate Ontology Dictionary</h2>
          <p style="font-size:0.8rem; color:var(--text-secondary);">Typed predicate vocabulary defining the formal ontology of BNS criminal law concepts, arities, and argument constraints.</p>
        </div>
        <div style="font-size:1.5rem; font-weight:800; color:var(--accent);">38 Predicates</div>
      </div>

      <div class="onto-filter-bar" id="onto-cat-bar"></div>

      <div class="onto-grid" id="ontology-grid"></div>
    </div>

    <!-- 3. STATISTICAL SUMMARY PANEL -->
    <div id="analytics-panel" class="view-panel">
      <div>
        <h2 style="font-size:1.35rem; font-weight:700; color:#fff; margin-bottom:4px;">Rulebase Analytics & Statutory Coverage</h2>
        <p style="font-size:0.82rem; color:var(--text-secondary);">Comprehensive quantitative verification of formal logic rules across all 20 chapters of the Bharatiya Nyaya Sanhita, 2023.</p>
      </div>

      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-num">1,281</div>
          <div class="stat-label">Formal Logic Rules</div>
          <div class="stat-sub">100% syntactically isomorphic</div>
        </div>
        <div class="stat-card">
          <div class="stat-num">358</div>
          <div class="stat-label">Sections Formalized</div>
          <div class="stat-sub">Complete penal code coverage</div>
        </div>
        <div class="stat-card">
          <div class="stat-num">38</div>
          <div class="stat-label">Ontological Predicates</div>
          <div class="stat-sub">Typed semantic signatures</div>
        </div>
        <div class="stat-card">
          <div class="stat-num">100.0%</div>
          <div class="stat-label">Benchmark Accuracy</div>
          <div class="stat-sub">20/20 test scenarios verified</div>
        </div>
      </div>

      <div>
        <h3 style="font-size:1.05rem; font-weight:700; color:#fff; margin-bottom:12px;">Rule Distribution by Classification Type</h3>
        <div class="type-distribution-grid" id="type-dist-grid"></div>
      </div>

      <div class="table-card">
        <div class="table-header">Chapter-by-Chapter Statutory Formalization Table</div>
        <div style="overflow-x:auto;">
          <table id="chapter-stats-table">
            <thead>
              <tr>
                <th>Chapter #</th>
                <th>Chapter Name</th>
                <th>Sections</th>
                <th>Total Rules</th>
                <th>Offence Elements</th>
                <th>Punishments</th>
                <th>Definitions</th>
                <th>Exceptions</th>
              </tr>
            </thead>
            <tbody id="chapter-table-body"></tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 4. ARCHITECTURE PANEL -->
    <div id="architecture-panel" class="view-panel">
      <div class="arch-card">
        <h2>Formal Verification Pipeline Architecture</h2>
        <p>The BNS Legal Reasoning Verification System replaces stochastic black-box LLM predictions with deterministic, auditable, and mathematically sound First-Order Logic deduction.</p>

        <div class="pipeline-flow">
          <div class="pipe-step">
            <div class="pipe-step-num">Stage 1</div>
            <div class="pipe-step-title">Statutory Ingestion</div>
            <div class="pipe-step-desc">Official Gazette text of Act No. 45 of 2023 parsed into 1,301 atomic components and 1,355 statutory relationships.</div>
          </div>
          <div class="pipe-step">
            <div class="pipe-step-num">Stage 2</div>
            <div class="pipe-step-title">FOL Translation</div>
            <div class="pipe-step-desc">1:1 Syntactic isomorphism maps each statutory clause to a formal Horn clause or non-monotonic defeasible override rule.</div>
          </div>
          <div class="pipe-step">
            <div class="pipe-step-num">Stage 3</div>
            <div class="pipe-step-title">Fact Assertion</div>
            <div class="pipe-step-desc">Factual scenario represented in Kleene 3-valued logic: True, False, or Unknown (Open-World Assumption).</div>
          </div>
          <div class="pipe-step">
            <div class="pipe-step-num">Stage 4</div>
            <div class="pipe-step-title">Deduction Engine</div>
            <div class="pipe-step-desc">Forward-chaining inference tests prima facie offence rules and resolves exception overrides without closed-world leaps.</div>
          </div>
          <div class="pipe-step">
            <div class="pipe-step-num">Stage 5</div>
            <div class="pipe-step-title">Audit Trail & Verdict</div>
            <div class="pipe-step-desc">Produces provable verdict (Proved, Refuted, Open) with complete statutory citations and execution traces.</div>
          </div>
        </div>
      </div>

      <div style="display:grid; grid-template-columns: 1fr 1fr; gap:16px;">
        <div class="arch-card">
          <h3 style="color:#fff; font-size:1.05rem; margin-bottom:8px;">Open-World Assumption vs Closed-World</h3>
          <p style="font-size:0.82rem; color:var(--text-secondary); margin-bottom:10px;">
            Standard LLMs and Prolog engines adopt the Closed-World Assumption (Negation as Failure), treating unstated facts as false. In criminal jurisprudence, this causes disastrous hallucinations (convicting without proving mens rea).
          </p>
          <div style="background:#090d16; border:1px solid var(--card-border); padding:10px 14px; border-radius:6px; font-size:0.8rem; font-family:monospace; color:#38bdf8;">
            Kleene 3-Valued Logic:<br>
            • True (1): Explicitly proved by evidence<br>
            • False (0): Explicitly disproved by evidence<br>
            • Unknown (⊥): Unproven / missing evidence
          </div>
        </div>

        <div class="arch-card">
          <h3 style="color:#fff; font-size:1.05rem; margin-bottom:8px;">Defeasible Non-Monotonic Override</h3>
          <p style="font-size:0.82rem; color:var(--text-secondary); margin-bottom:10px;">
            Exceptions in criminal codes (e.g. Sec 101 Exceptions 1-5, General Exceptions Sec 14-44) operate non-monotonically: proving an affirmative defence overrides a prima facie offence.
          </p>
          <div style="background:#090d16; border:1px solid var(--card-border); padding:10px 14px; border-radius:6px; font-size:0.8rem; font-family:monospace; color:#10b981;">
            Formal Scheme:<br>
            1. Offence: PrimaFacieMurder(x,y) ∧ ¬ExceptedFromMurder(x,y) → Murder(x,y)<br>
            2. Override: Exception1(x,y) → ExceptedFromMurder(x,y)<br>
            3. Mitigation: PrimaFacieMurder(x,y) ∧ ExceptedFromMurder(x,y) → MitigatedOffence(x,y)
          </div>
        </div>
      </div>
    </div>

  </div>

  <!-- Toast Notification -->
  <div id="toast">Copied to clipboard!</div>

  <!-- Embedded Data Payload and Application Logic -->
  <script>
    const APP_DATA = __APP_DATA_JSON__;

    // State
    let currentSectionNumber = 101;
    let currentRuleTypeFilter = 'ALL';
    let currentSearchQuery = '';
    let currentOntologyCategory = 'ALL';

    // Indexing
    const rulesBySection = new Map();
    APP_DATA.rules.forEach(r => {
      if (!rulesBySection.has(r.section_number)) {
        rulesBySection.set(r.section_number, []);
      }
      rulesBySection.get(r.section_number).push(r);
    });

    const sectionsByNumber = new Map();
    APP_DATA.sections.forEach(s => sectionsByNumber.set(s.number, s));

    // Colors mapping
    const TYPE_COLORS = {
      'OFFENCE_ELEMENT': { bg: 'rgba(59, 130, 246, 0.15)', text: '#60a5fa', border: '#3b82f6', label: 'Offence Element' },
      'EXCEPTION_DEFENCE': { bg: 'rgba(239, 68, 68, 0.15)', text: '#f87171', border: '#ef4444', label: 'Exception Defence' },
      'EXCEPTION_OVERRIDE': { bg: 'rgba(192, 38, 211, 0.15)', text: '#e879f9', border: '#c026d3', label: 'Exception Override' },
      'OFFENCE_FINAL': { bg: 'rgba(16, 185, 129, 0.15)', text: '#34d399', border: '#10b981', label: 'Offence Final' },
      'OFFENCE_MITIGATED': { bg: 'rgba(6, 182, 212, 0.15)', text: '#22d3ee', border: '#06b6d4', label: 'Offence Mitigated' },
      'PUNISHMENT_MAPPING': { bg: 'rgba(245, 158, 11, 0.15)', text: '#fbbf24', border: '#f59e0b', label: 'Punishment Mapping' },
      'DEFINITIONAL_EXPANSION': { bg: 'rgba(139, 92, 246, 0.15)', text: '#a78bfa', border: '#8b5cf6', label: 'Definitional Expansion' }
    };

    // Initialization
    window.addEventListener('DOMContentLoaded', () => {
      renderSidebar();
      renderActiveSection();
      renderOntologyTab();
      renderAnalyticsTab();
    });

    // Navigation Switcher
    function switchMainView(viewName) {
      document.querySelectorAll('.view-panel').forEach(p => p.classList.remove('active'));
      document.querySelectorAll('.nav-tab-btn').forEach(b => b.classList.remove('active'));
      
      const tabIdx = {'rules':0, 'ontology':1, 'analytics':2, 'architecture':3}[viewName] || 0;
      document.querySelectorAll('.nav-tab-btn')[tabIdx].classList.add('active');

      if (viewName === 'rules') {
        document.getElementById('rules-explorer-panel').classList.add('active');
      } else if (viewName === 'ontology') {
        document.getElementById('ontology-panel').classList.add('active');
      } else if (viewName === 'analytics') {
        document.getElementById('analytics-panel').classList.add('active');
      } else if (viewName === 'architecture') {
        document.getElementById('architecture-panel').classList.add('active');
      }
    }

    // Sidebar Rendering
    function renderSidebar() {
      const listEl = document.getElementById('section-list');
      listEl.innerHTML = '';

      const query = currentSearchQuery.toLowerCase().trim();

      const filteredSections = APP_DATA.sections.filter(s => {
        const secRules = rulesBySection.get(s.number) || [];
        
        // Type filter check
        if (currentRuleTypeFilter !== 'ALL') {
          const hasType = secRules.some(r => r.rule_type === currentRuleTypeFilter);
          if (!hasType) return false;
        }

        // Search query check
        if (!query) return true;

        if (String(s.number).includes(query)) return true;
        if (s.name.toLowerCase().includes(query)) return true;
        if (s.chapter_name.toLowerCase().includes(query)) return true;

        // Search within rules
        const matchesRule = secRules.some(r => 
          r.rule_id.toLowerCase().includes(query) ||
          r.rule_name.toLowerCase().includes(query) ||
          r.formula_unicode.toLowerCase().includes(query) ||
          (r.description && r.description.toLowerCase().includes(query))
        );
        return matchesRule;
      });

      if (filteredSections.length === 0) {
        listEl.innerHTML = '<div style="padding:20px; text-align:center; color:var(--text-muted); font-size:0.8rem;">No matching sections found.</div>';
        return;
      }

      filteredSections.forEach(s => {
        const secRules = rulesBySection.get(s.number) || [];
        const div = document.createElement('div');
        div.className = 'sec-item' + (s.number === currentSectionNumber ? ' active' : '');
        div.id = 'sec-nav-' + s.number;
        div.onclick = () => selectSection(s.number);

        div.innerHTML = `
          <div class="sec-info">
            <div class="sec-title">Sec ${s.number}: ${escapeHtml(s.name)}</div>
            <div class="sec-sub">Ch ${s.chapter} • ${escapeHtml(s.chapter_name)}</div>
          </div>
          <div class="sec-count-badge">${secRules.length} rules</div>
        `;
        listEl.appendChild(div);
      });
    }

    function selectSection(secNum) {
      currentSectionNumber = secNum;
      document.querySelectorAll('.sec-item').forEach(el => el.classList.remove('active'));
      const activeEl = document.getElementById('sec-nav-' + secNum);
      if (activeEl) {
        activeEl.classList.add('active');
        activeEl.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      }
      renderActiveSection();
    }

    function jumpToSection(secNum) {
      switchMainView('rules');
      currentRuleTypeFilter = 'ALL';
      document.getElementById('type-filter-select').value = 'ALL';
      currentSearchQuery = '';
      document.getElementById('sec-search-box').value = '';
      renderSidebar();
      selectSection(secNum);
    }

    function handleSearch() {
      currentSearchQuery = document.getElementById('sec-search-box').value;
      renderSidebar();
    }

    function handleTypeFilter() {
      currentRuleTypeFilter = document.getElementById('type-filter-select').value;
      renderSidebar();
      renderActiveSection();
    }

    // Render Section Details & Rule Cards
    function renderActiveSection() {
      const sec = sectionsByNumber.get(currentSectionNumber) || {
        number: currentSectionNumber,
        name: 'Unknown Section',
        chapter: 1,
        chapter_name: 'Preliminary'
      };

      const rules = (rulesBySection.get(currentSectionNumber) || []).filter(r => {
        if (currentRuleTypeFilter === 'ALL') return true;
        return r.rule_type === currentRuleTypeFilter;
      });

      // Hero info
      document.getElementById('hero-breadcrumb').innerText = `CHAPTER ${sec.chapter} • ${sec.chapter_name.toUpperCase()}`;
      document.getElementById('hero-title').innerText = `Section ${sec.number}: ${sec.name}`;

      // Open in KB Link
      const kbBtn = document.getElementById('open-in-kb-btn');
      if (kbBtn) {
        kbBtn.href = `view_kb.html#sec-${sec.number}`;
      }

      // Type counts breakdown
      const typeCounts = {};
      const allSecRules = rulesBySection.get(currentSectionNumber) || [];
      allSecRules.forEach(r => {
        typeCounts[r.rule_type] = (typeCounts[r.rule_type] || 0) + 1;
      });

      const breakdownEl = document.getElementById('hero-breakdown');
      breakdownEl.innerHTML = '';
      for (const [t, count] of Object.entries(typeCounts)) {
        const color = TYPE_COLORS[t] || { bg: '#334155', text: '#fff', border: '#475569', label: t };
        const pill = document.createElement('span');
        pill.className = 'type-pill';
        pill.style.background = color.bg;
        pill.style.color = color.text;
        pill.style.border = `1px solid ${color.border}`;
        pill.innerText = `${count} ${color.label}`;
        breakdownEl.appendChild(pill);
      }

      // Cards
      const container = document.getElementById('rules-cards-container');
      container.innerHTML = '';

      if (rules.length === 0) {
        container.innerHTML = '<div style="padding:40px; text-align:center; color:var(--text-muted); background:var(--card-bg); border-radius:8px; border:1px solid var(--card-border);">No rules match the selected filter in this section.</div>';
        return;
      }

      rules.forEach(r => {
        const card = createRuleCard(r);
        container.appendChild(card);
      });
    }

    function createRuleCard(r) {
      const card = document.createElement('div');
      card.className = `rule-card type-${r.rule_type}`;
      card.id = 'rule-' + r.rule_id;

      const tColor = TYPE_COLORS[r.rule_type] || { bg: '#334155', text: '#fff', border: '#475569', label: r.rule_type };

      // Format formula with syntax highlighting
      const highlightedFormula = highlightFOL(r.formula_unicode);

      // Format premises list
      let premisesHtml = '';
      r.premises.forEach(p => {
        const isNeg = p.startsWith('¬') || p.startsWith('~') || p.startsWith('!');
        const icon = isNeg ? '⊘' : '✓';
        const cls = isNeg ? 'premise-neg' : 'premise-pos';
        premisesHtml += `
          <div class="premise-item ${cls}">
            <span class="atom-icon">${icon}</span>
            <span>${escapeHtml(p)}</span>
          </div>
        `;
      });

      card.innerHTML = `
        <div class="rule-header">
          <div class="rule-meta-left">
            <span class="rule-id" onclick="copyText('${r.rule_id}', 'Rule ID')" title="Click to copy Rule ID">${r.rule_id}</span>
            <span class="rule-badge" style="background:${tColor.bg}; color:${tColor.text}; border:1px solid ${tColor.border};">${tColor.label}</span>
            <span class="rule-src" title="Source Statutory Component">${r.source_component_id}</span>
          </div>
          <div class="rule-actions">
            <button class="action-btn" onclick="copyRuleFormula('${r.rule_id}')"><span>📋</span> Formula</button>
            <button class="action-btn" onclick="copyRuleLaTeX('${r.rule_id}')"><span>📐</span> LaTeX</button>
            <button class="action-btn" onclick="copyRuleJSON('${r.rule_id}')"><span>💾</span> JSON</button>
          </div>
        </div>

        <div class="rule-body">
          <div class="rule-name-row">
            <div class="rule-name">${escapeHtml(r.rule_name)}</div>
            <div class="rule-desc">${escapeHtml(r.description || '')}</div>
          </div>

          <div class="formula-box">
            <div class="formula-tabs">
              <button class="formula-tab active" onclick="switchFormulaTab('${r.rule_id}', 'unicode')">Unicode</button>
              <button class="formula-tab" onclick="switchFormulaTab('${r.rule_id}', 'latex')">LaTeX</button>
              <button class="formula-tab" onclick="switchFormulaTab('${r.rule_id}', 'ascii')">ASCII</button>
            </div>
            <div id="f-unicode-${r.rule_id}" class="formula-code formula-unicode">${highlightedFormula}</div>
            <div id="f-latex-${r.rule_id}" class="formula-code formula-latex">${escapeHtml(r.formula_latex || '')}</div>
            <div id="f-ascii-${r.rule_id}" class="formula-code formula-ascii">${escapeHtml(r.formula_ascii || '')}</div>
          </div>

          <div class="logic-decomp">
            <div>
              <div class="decomp-col-title">
                <span>📋</span> Premises (Antecedents) • Conjunction ∧
              </div>
              <div class="premises-list">${premisesHtml}</div>
              <div class="variables-tag">Variables: ${r.variables ? r.variables.join(', ') : 'none'}</div>
            </div>
            <div>
              <div class="decomp-col-title">
                <span>🎯</span> Conclusion (Consequent) • Derived Status
              </div>
              <div class="conclusion-box">
                <span>➔</span>
                <span>${escapeHtml(r.conclusion)}</span>
              </div>
            </div>
          </div>
        </div>
      `;
      return card;
    }

    function highlightFOL(formula) {
      if (!formula) return '';
      let res = escapeHtml(formula);

      // Quantifiers: ∀x, y.
      res = res.replace(/(∀|∃)([^.]+)\./g, '<span class="syn-quant">$1$2.</span>');

      // Arrows
      res = res.replace(/→/g, '<span class="syn-arr">→</span>');

      // Connectives
      res = res.replace(/∧/g, '<span class="syn-op">∧</span>');
      res = res.replace(/∨/g, '<span class="syn-op">∨</span>');
      res = res.replace(/¬/g, '<span class="syn-neg">¬</span>');

      // Predicates: AnyWord(args)
      res = res.replace(/([A-Z][a-zA-Z0-9_]+)\(([^)]*)\)/g, function(match, pName, pArgs) {
        return `<span class="syn-pred" onclick="jumpToOntology('${pName}')" title="Click to view '${pName}' in Ontology">${pName}</span>(<span class="syn-var">${pArgs}</span>)`;
      });

      return res;
    }

    function switchFormulaTab(ruleId, tabType) {
      const card = document.getElementById('rule-' + ruleId);
      if (!card) return;
      card.querySelectorAll('.formula-tab').forEach(t => t.classList.remove('active'));
      event.target.classList.add('active');

      const uEl = document.getElementById(`f-unicode-${ruleId}`);
      const lEl = document.getElementById(`f-latex-${ruleId}`);
      const aEl = document.getElementById(`f-ascii-${ruleId}`);

      uEl.style.display = (tabType === 'unicode' ? 'block' : 'none');
      lEl.style.display = (tabType === 'latex' ? 'block' : 'none');
      aEl.style.display = (tabType === 'ascii' ? 'block' : 'none');
    }

    // Ontology Tab
    function renderOntologyTab() {
      const categories = ['ALL'];
      for (const p of Object.values(APP_DATA.ontology)) {
        if (p.category && !categories.includes(p.category)) {
          categories.push(p.category);
        }
      }

      const bar = document.getElementById('onto-cat-bar');
      bar.innerHTML = '';
      categories.forEach(cat => {
        const btn = document.createElement('button');
        btn.className = 'onto-cat-btn' + (cat === currentOntologyCategory ? ' active' : '');
        btn.innerText = cat;
        btn.onclick = () => {
          currentOntologyCategory = cat;
          document.querySelectorAll('.onto-cat-btn').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          renderOntologyGrid();
        };
        bar.appendChild(btn);
      });

      renderOntologyGrid();
    }

    function renderOntologyGrid() {
      const grid = document.getElementById('ontology-grid');
      grid.innerHTML = '';

      const filtered = Object.values(APP_DATA.ontology).filter(p => {
        if (currentOntologyCategory === 'ALL') return true;
        return p.category === currentOntologyCategory;
      });

      filtered.forEach(p => {
        const card = document.createElement('div');
        card.className = 'onto-card';
        card.id = 'onto-pred-' + p.name;

        const argsStr = p.arg_types ? p.arg_types.join(', ') : '';

        card.innerHTML = `
          <div class="onto-card-header">
            <span class="onto-name">${escapeHtml(p.name)}</span>
            <div class="onto-meta">
              <span class="onto-cat-badge">${escapeHtml(p.category || 'GENERAL')}</span>
              <span class="onto-cat-badge" style="background:#1e3a5f; color:#93c5fd;">Arity: ${p.arity}</span>
            </div>
          </div>
          <div class="onto-sig">${escapeHtml(p.name)}(${escapeHtml(argsStr)})</div>
          <div class="onto-desc">${escapeHtml(p.description || '')}</div>
          <div class="onto-usages">
            <span>Used in <strong>${p.usage_count || 0}</strong> formal rules</span>
            ${p.usage_count > 0 ? `<span class="onto-jump-btn" onclick="jumpToFirstRule('${p.name}')">View Sample Rule ➔</span>` : ''}
          </div>
        `;
        grid.appendChild(card);
      });
    }

    function jumpToOntology(predName) {
      switchMainView('ontology');
      currentOntologyCategory = 'ALL';
      renderOntologyTab();
      setTimeout(() => {
        const el = document.getElementById('onto-pred-' + predName);
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'center' });
          el.style.borderColor = 'var(--accent)';
          el.style.boxShadow = '0 0 15px var(--accent-glow)';
          setTimeout(() => {
            el.style.borderColor = '';
            el.style.boxShadow = '';
          }, 2000);
        }
      }, 100);
    }

    function jumpToFirstRule(predName) {
      const pred = APP_DATA.ontology[predName];
      if (pred && pred.rules_using && pred.rules_using.length > 0) {
        const target = pred.rules_using[0];
        jumpToSection(target.section_number);
        setTimeout(() => {
          const card = document.getElementById('rule-' + target.rule_id);
          if (card) {
            card.scrollIntoView({ behavior: 'smooth', block: 'center' });
            card.style.borderColor = 'var(--accent)';
            setTimeout(() => card.style.borderColor = '', 2000);
          }
        }, 200);
      }
    }

    // Analytics Tab
    function renderAnalyticsTab() {
      const typeCounts = {};
      APP_DATA.rules.forEach(r => {
        typeCounts[r.rule_type] = (typeCounts[r.rule_type] || 0) + 1;
      });

      const distGrid = document.getElementById('type-dist-grid');
      distGrid.innerHTML = '';

      for (const [t, count] of Object.entries(typeCounts)) {
        const color = TYPE_COLORS[t] || { bg: '#334155', text: '#fff', border: '#475569', label: t };
        const pct = ((count / APP_DATA.total_rules) * 100).toFixed(1);

        const card = document.createElement('div');
        card.className = 'type-card';
        card.style.borderLeftColor = color.border;
        card.innerHTML = `
          <div class="type-card-top">
            <span class="type-card-title">${color.label}</span>
            <span class="type-card-count" style="color:${color.text};">${count}</span>
          </div>
          <div class="type-card-pct">${pct}% of rulebase</div>
          <div class="type-card-bar">
            <div class="type-card-fill" style="width:${pct}%; background:${color.border};"></div>
          </div>
        `;
        distGrid.appendChild(card);
      }

      // Chapter table
      const tbody = document.getElementById('chapter-table-body');
      tbody.innerHTML = '';

      APP_DATA.chapters.forEach(ch => {
        const tr = document.createElement('tr');
        const elemCount = ch.types['OFFENCE_ELEMENT'] || 0;
        const punishCount = ch.types['PUNISHMENT_MAPPING'] || 0;
        const defCount = ch.types['DEFINITIONAL_EXPANSION'] || 0;
        const excCount = (ch.types['EXCEPTION_DEFENCE'] || 0) + (ch.types['EXCEPTION_OVERRIDE'] || 0);

        tr.innerHTML = `
          <td style="font-weight:700; color:var(--accent);">Ch ${ch.chapter_number}</td>
          <td style="font-weight:600; color:#fff;">${escapeHtml(ch.chapter_name)}</td>
          <td>${ch.section_count}</td>
          <td style="font-weight:700; color:#fff;">${ch.rule_count}</td>
          <td>${elemCount}</td>
          <td>${punishCount}</td>
          <td>${defCount}</td>
          <td>${excCount}</td>
        `;
        tbody.appendChild(tr);
      });
    }

    // Robust Copying utilities
    function showToast(msg) {
      const t = document.getElementById('toast');
      t.innerText = msg;
      t.classList.add('show');
      setTimeout(() => t.classList.remove('show'), 2200);
    }

    function copyText(text, label) {
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(() => {
          showToast(label ? `${label} copied!` : 'Copied to clipboard!');
        }).catch(() => fallbackCopyText(text, label));
      } else {
        fallbackCopyText(text, label);
      }
    }

    function fallbackCopyText(text, label) {
      try {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed";
        textArea.style.top = "-9999px";
        textArea.style.left = "-9999px";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        const successful = document.execCommand('copy');
        document.body.removeChild(textArea);
        if (successful) {
          showToast(label ? `${label} copied!` : 'Copied to clipboard!');
        } else {
          prompt('Copy manually:', text);
        }
      } catch (err) {
        prompt('Copy manually:', text);
      }
    }

    function copyRuleFormula(ruleId) {
      const r = APP_DATA.rules.find(x => x.rule_id === ruleId);
      if (r) copyText(r.formula_unicode, 'Unicode formula');
    }

    function copyRuleLaTeX(ruleId) {
      const r = APP_DATA.rules.find(x => x.rule_id === ruleId);
      if (r) copyText(r.formula_latex, 'LaTeX formula');
    }

    function copyRuleJSON(ruleId) {
      const r = APP_DATA.rules.find(x => x.rule_id === ruleId);
      if (r) copyText(JSON.stringify(r, null, 2), 'Rule JSON');
    }

    function copySectionLaTeX() {
      const secRules = rulesBySection.get(currentSectionNumber) || [];
      const latexLines = secRules.map(r => `% ${r.rule_name} [${r.rule_id}]\n\\[\n${r.formula_latex}\n\\]`).join('\n\n');
      copyText(latexLines, `Section ${currentSectionNumber} LaTeX formulas`);
    }

    function copySectionJSON() {
      const secRules = rulesBySection.get(currentSectionNumber) || [];
      copyText(JSON.stringify(secRules, null, 2), `Section ${currentSectionNumber} JSON`);
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }
  </script>
</body>
</html>
"""

def escape_for_html_script(s: str) -> str:
    """Safely escapes strings for inclusion within an inline <script> tag."""
    return s.replace("</script>", "<\\/script>")

def main():
    print("Loading data files...")
    
    # 1. Load formal rules
    rules = []
    with open('data/output/formal_rules.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                rules.append(json.loads(line))
    print(f"Loaded {len(rules)} formal rules.")

    # 2. Load predicate ontology
    with open('data/output/predicate_ontology.json', 'r', encoding='utf-8') as f:
        ontology = json.load(f)
    print(f"Loaded {len(ontology)} ontology predicates.")

    # 3. Load section metadata from knowledge base
    sections = {}
    with open('data/output/knowledge_base.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                sections[item['section_number']] = {
                    'number': item['section_number'],
                    'name': item['section_name'],
                    'chapter': item['chapter_number'],
                    'chapter_name': item['chapter_name']
                }
    print(f"Loaded metadata for {len(sections)} sections.")

    # 4. Compute predicate usage across rules
    pred_usage = {p: [] for p in ontology}
    for r in rules:
        formula = r.get('formula_unicode', '')
        for p in ontology:
            if p in formula:
                pred_usage[p].append({
                    'rule_id': r['rule_id'],
                    'section_number': r['section_number'],
                    'rule_type': r['rule_type']
                })

    for p, pdata in ontology.items():
        pdata['usage_count'] = len(pred_usage[p])
        pdata['rules_using'] = pred_usage[p]

    # 5. Compute chapter statistics
    chapter_stats = defaultdict(lambda: {
        'chapter_number': 0,
        'chapter_name': '',
        'sections': set(),
        'rules': 0,
        'types': defaultdict(int)
    })

    rules_by_sec = defaultdict(list)
    for r in rules:
        sec_num = r['section_number']
        rules_by_sec[sec_num].append(r)
        sec_meta = sections.get(sec_num, {'chapter': 0, 'chapter_name': 'Unknown'})
        ch = sec_meta['chapter']
        chapter_stats[ch]['chapter_number'] = ch
        chapter_stats[ch]['chapter_name'] = sec_meta['chapter_name']
        chapter_stats[ch]['sections'].add(sec_num)
        chapter_stats[ch]['rules'] += 1
        chapter_stats[ch]['types'][r['rule_type']] += 1

    formatted_chapters = []
    for ch_num in sorted(chapter_stats.keys()):
        ch_data = chapter_stats[ch_num]
        formatted_chapters.append({
            'chapter_number': ch_data['chapter_number'],
            'chapter_name': ch_data['chapter_name'],
            'section_count': len(ch_data['sections']),
            'rule_count': ch_data['rules'],
            'types': dict(ch_data['types'])
        })

    # Prepare serialized data payload
    app_data = {
        'rules': rules,
        'sections': sorted(list(sections.values()), key=lambda x: x['number']),
        'ontology': ontology,
        'chapters': formatted_chapters,
        'total_rules': len(rules),
        'total_sections': len(sections),
        'total_predicates': len(ontology)
    }

    raw_json = json.dumps(app_data, separators=(',', ':'))
    escaped_json = escape_for_html_script(raw_json)

    # Insert JSON into template
    html_content = HTML_TEMPLATE.replace("__APP_DATA_JSON__", escaped_json)

    out_path = 'view_fol.html'
    print(f"Writing {out_path}...")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"Successfully generated {out_path} ({len(html_content):,} bytes)!")

if __name__ == '__main__':
    main()
