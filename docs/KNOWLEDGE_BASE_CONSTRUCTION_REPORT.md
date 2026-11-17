# Research Report: Knowledge Base Construction and Multi-Level Verification for the Bharatiya Nyaya Sanhita (BNS), 2023

**Project**: Legal Reasoning Verification System  
**Stage**: Stage 1 — Legal Knowledge Base Construction  
**Statutory Domain**: Bharatiya Nyaya Sanhita, 2023 (Act No. 45 of 2023, Gazette of India)  
**Deliverable**: Machine-Readable Knowledge Base (`knowledge_base.jsonl`), Human Review CSVs (`review_components.csv`, `review_relationships.csv`), and Deterministic Verification Engine  

---

## 1. Executive Summary & Research Motivation

Contemporary Large Language Models (LLMs) frequently generate persuasive, fluent legal text. However, in criminal jurisprudence, plausible-sounding natural language is unacceptable when it suffers from:
1. **Statutory Hallucination**: Paraphrasing statutory text in ways that alter legal thresholds (e.g., confusing "intention" with "knowledge").
2. **Structural Flattening**: Treating a section as an undifferentiated block of text, thereby losing the crucial relationships between main definitions, exceptions, qualifying provisos, and explanations.
3. **Unwarranted Legal Conclusions**: Asserting guilt or liability without verifying whether every prerequisite condition in the statutory definition is satisfied by the facts.
4. **Neglect of Exceptions and Provisos**: Failing to notice that an exception (such as grave and sudden provocation under Section 101) negates the primary offence.

To solve this, our project investigates whether **neuro-symbolic machine reasoning**—combining structured statutory knowledge bases, formal logic, and deterministic verification—can rigorously determine whether legal conclusions follow from facts and applicable statutory provisions.

**Stage 1** establishes the foundation of this system: extracting, structuring, and verifying all **358 enacted sections** of the **Bharatiya Nyaya Sanhita (BNS), 2023** into a high-fidelity, machine-readable knowledge base.

---

## 2. Statutory Source and Data Ingestion

### 2.1 Legal Source of Truth
The knowledge base is built from the enacted **Bharatiya Nyaya Sanhita, 2023 (Act No. 45 of 2023)**, as published in the official Gazette of India and archived in the India Code legislative repository (`indiacode.nic.in/handle/123456789/20062`).

The dataset contains:
- **Total Sections**: 358 unique enacted sections.
- **Total Chapters**: 20 chapters (from Chapter I: *Preliminary* to Chapter XX: *Repeal and Savings*).
- **Data Integrity**: 0 duplicate section numbers, 0 missing rows.

### 2.2 Cryptographic Provenance Tracking
To ensure total auditability, every statutory section ingested into the pipeline is hashed using SHA-256:
$$\text{Hash} = \text{SHA256}(\text{RawStatutoryText})$$
This cryptographic hash is stored in each record's metadata (`raw_text_sha256`), ensuring that any amendment, re-enactment, or formatting variation in the source dataset is immediately detectable.

---

## 3. Two-Pass Knowledge Base Architecture

Statutory drafting follows strict legislative architecture. Instead of monolithic parsing, the pipeline employs a **Two-Pass Extraction Architecture**:

```
+-------------------------------------------------------------------------+
|                  Enacted BNS Statutory Dataset (CSV)                    |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                     1. INGESTION & PROVENANCE                           |
|       - Standardizes schema ('section_number', 'section_name', etc.)    |
|       - Computes SHA-256 hash of raw verbatim statutory text            |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                2. PASS 1: COMPONENT DECOMPOSITION                       |
|   Deconstructs sections into typed components with verbatim spans:      |
|   - MAIN_PROVISION, SUBSECTION, CLAUSE, SUBCLAUSE                       |
|   - EXCEPTION, PROVISO, EXPLANATION, ILLUSTRATION, PUNISHMENT           |
|   - Exact character offsets [char_start : char_end]                     |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                3. PASS 1 DETERMINISTIC VALIDATION GATE                  |
|   - Substring Check: raw_text[char_start:char_end] == verbatim_text     |
|   - Coverage Metric: Non-whitespace character coverage >= 95%           |
|   - DAG Integrity: No duplicate IDs, no cycles                          |
+-------------------+--------------------------------+--------------------+
                    | Passed                         | Failed
                    v                                v
+------------------------------------+   +--------------------------------+
|  4. PASS 2: RELATIONAL TOPOLOGY    |   |  HALT SECTION EXTRACTION       |
|  Discovers typed directed edges:   |   |  - Flag error in report        |
|  - HAS_CHILD (Structural containment)| +--------------------------------+
|  - QUALIFIES (Explanations/Provisos)|
|  - EXCEPTION_TO (Statutory exceptions)
|  - PROVIDES_ILLUSTRATION_FOR        |
|  - PUNISHES (Intra & Cross-section)|
|  - CROSS_REFERENCES (Statute cites) |
+-------------------+----------------+
                    |
                    v
+-------------------------------------------------------------------------+
|                5. PASS 2 DETERMINISTIC VALIDATION GATE                  |
|   - Endpoint Existence: Source and Target IDs must exist in KB          |
|   - Cycle and Self-Loop Detection: source_id != target_id               |
+-------------------+-----------------------------------------------------+
                    |
                    v
+-------------------------------------------------------------------------+
|                6. STORAGE & AUDIT EXPORTS                               |
|   - Primary Storage: 'data/output/knowledge_base.jsonl'                 |
|   - Review Components: 'data/output/review_components.csv'              |
|   - Review Relationships: 'data/output/review_relationships.csv'        |
|   - Validation Summary: 'data/output/validation_summary.json'           |
+-------------------------------------------------------------------------+
```

---

## 4. Formal Taxonomy and Ontology

### 4.1 Component Types (`ComponentType`)
Every extracted item is assigned an explicit statutory role:
- **`MAIN_PROVISION`**: The primary rule, definition, or charging clause of a section.
- **`SUBSECTION`**: Formally numbered statutory subdivisions (`(1)`, `(2)`, `(3)`).
- **`CLAUSE`**: Lettered sub-parts within a subsection or main provision (`(a)`, `(b)`, `(c)`).
- **`SUBCLAUSE`**: Roman numeral sub-items (`(i)`, `(ii)`, `(iii)`).
- **`EXPLANATION`**: Statutory clarifications that define terms or clarify ambiguities (e.g., `Explanation 1`, `Explanation 2`).
- **`PROVISO`**: Qualifying conditions, typically beginning with *"Provided that..."* or *"Provided further that..."*.
- **`EXCEPTION`**: Statutory defences or conditions that negate/mitigate criminal liability (e.g., the 5 Exceptions to Murder in Section 101).
- **`ILLUSTRATION`**: Concrete factual scenarios enacted by Parliament to demonstrate statutory application (e.g., `Illustration (a)`, `Illustration (b)`).
- **`PUNISHMENT`**: Explicit penal provisions prescribing imprisonment, fine, death, or community service.
- **`DEFINITION`**: Embedded definitions of terms (e.g., in Section 2, Section 101, Section 318).

### 4.2 Legal Relationship Types (`RelationType`)
Legal meaning depends on the connections between statutory elements:
- **`HAS_CHILD`**: Structural tree hierarchy (e.g., Section $\to$ Subsection $\to$ Clause).
- **`QUALIFIES`**: Directs an Explanation or Proviso to the specific provision it clarifies or limits.
- **`EXCEPTION_TO`**: Connects an Exception to the offence it negates.
- **`PROVIDES_ILLUSTRATION_FOR`**: Connects an enacted Illustration to the specific legal rule or explanation it exemplifies.
- **`PUNISHES`**: Links a penalty provision to the corresponding substantive offence (both intra-section, such as Section 318(2) punishing 318(1), and cross-section, such as Section 103 punishing Section 101).
- **`CROSS_REFERENCES`**: Captures explicit legislative citations to other sections (e.g., *"within the meaning of section 100"*).

---

## 5. Multi-Level Deterministic Verification Framework

The system enforces four levels of deterministic validation before saving any record:

### Level 1: Structural Hierarchy and DAG Validation
- **ID Uniqueness**: Every component ID (e.g., `BNS-SEC-101-EXC-1`) must be globally and locally unique.
- **Parent Referential Integrity**: If a component has `parent_id`, that parent ID must exist within the knowledge base.
- **Acyclicity**: Traversal from any component to its root must terminate without infinite loops.

### Level 2: Exact Substring and Source Integrity
To prevent LLM hallucination and paraphrasing:
$$\text{Slice} = \text{RawText}[\text{char\_start} : \text{char\_end}]$$
$$\text{Assert}(\text{Slice} == \text{verbatim\_text})$$
Every character of every component is verified against the original Gazette text.

### Level 3: Non-Whitespace Character Coverage Metric
To guarantee that no statutory clauses, exceptions, or illustrations were silently omitted:
$$\text{Coverage} = \frac{\sum_{c \in \text{Components}} \text{len}(\text{StripWhitespace}(c.\text{verbatim\_text}))}{\text{len}(\text{StripWhitespace}(\text{RawText}))}$$
If $\text{Coverage} < 95\%$, the validation engine triggers a warning report detailing the missing character spans.

### Level 4: Relational Integrity Validation
- **Endpoint Validity**: For every relationship $(u, r, v)$, both $u$ and $v$ must exist.
- **No Self-Loops**: $u \neq v$ is strictly enforced.
- **Evidence Verification**: Every edge must cite a verbatim text quote or statutory reference.

### Legal Status Distinction: Machine-Validated $\neq$ Legally Verified
A crucial research and governance principle is preserved:
- Syntactic, structural, and substring validation marks records as `VALIDATED_SYNTAX`.
- Newly extracted provisions are initialized with `ReviewStatus.PENDING_REVIEW`.
- Only human legal reviewers may update status to `APPROVED`, `REJECTED`, or `NEEDS_CORRECTION`.

---

## 6. Empirical Validation Results Across All 358 Sections

The pipeline was executed across the entire Bharatiya Nyaya Sanhita, 2023.

### 6.1 Quantitative Summary
| Metric | Value |
| :--- | :--- |
| **Total Statutory Sections Processed** | **358 / 358 (100.0%)** |
| **Syntactically Validated Sections** | **358 / 358 (100.0%)** |
| **Sections with Zero Warnings/Errors** | **358 / 358 (100.0%)** |
| **Validation Pass Rate** | **100.0%** |
| **Mean Non-Whitespace Character Coverage** | **99.90%** |
| **Minimum Character Coverage** | **96.53%** |
| **Total Legal Components Extracted** | **1,301** |
| **Total Legal Relationships Established** | **1,355** |

### 6.2 Component Distribution
| Component Type | Total Extracted | Percentage |
| :--- | :--- | :--- |
| **`CLAUSE`** | 281 | 21.6% |
| **`PUNISHMENT`** | 265 | 20.4% |
| **`ILLUSTRATION`** | 219 | 16.8% |
| **`SUBSECTION`** | 179 | 13.8% |
| **`MAIN_PROVISION`** | 134 | 10.3% |
| **`EXPLANATION`** | 117 | 9.0% |
| **`SUBCLAUSE`** | 43 | 3.3% |
| **`PROVISO`** | 27 | 2.1% |
| **`EXCEPTION`** | 26 | 2.0% |
| **`DEFINITION`** | 10 | 0.8% |
| **Total** | **1,301** | **100.0%** |

### 6.3 Relationship Distribution
| Relationship Type | Total Edges | Description |
| :--- | :--- | :--- |
| **`HAS_CHILD`** | 764 | Structural parent-child containment |
| **`PROVIDES_ILLUSTRATION_FOR`** | 219 | Concrete illustrative scenarios |
| **`QUALIFIES`** | 144 | Clarifying explanations & qualifying provisos |
| **`PUNISHES`** | 122 | Penal consequences (intra & cross-section) |
| **`CROSS_REFERENCES`** | 80 | Explicit cross-section statutory citations |
| **`EXCEPTION_TO`** | 26 | Statutory defences and exceptions |
| **Total** | **1,355** | **100.0%** |

---

### 6.4 Parser Revision v1.1
- **Roman-numeral disambiguation.** `(i)`, `(v)` and `(x)` are both letters and roman numerals. The parser now continues a lettered sequence when the token is its next letter (e.g. `(i)` after `(h)` in Section 64(2)), and otherwise reads it as a roman sub-clause when a roman list is plausible: an open clause, a following `(ii)`, or a preceding `(iv)`/`(ix)`. 16 components moved from `CLAUSE` to `SUBCLAUSE` (e.g. Sections 63, 113, 335). Totals are unchanged.
- **`DEFINITION` type.** A main provision with definition language ("is said to", "means", …) and no punishment language is now typed `DEFINITION` (10 sections, e.g. 63, 335).
- **Checkpointing.** Unchanged sections are reused from the previous run when both the source SHA-256 and a fingerprint of the parser/validator code match; any code change forces re-extraction.

## 7. Deep-Dive Pilot Section Case Studies

### 7.1 Section 101: Murder
Section 101 represents one of the most complex statutory structures in criminal law:
- **Total Components**: 28 components extracted.
- **Total Relationships**: 47 directed relational edges.
- **Coverage**: 99.47% non-whitespace character coverage.
- **Structural Highlights**:
  - `BNS-SEC-101-MAIN`: Core definition *"Except in the cases hereinafter excepted, culpable homicide is murder,—"*.
  - Clauses `(a)` to `(d)` defining the mental elements (*mens rea*: intention vs imminent danger).
  - Illustrations `(a)` to `(d)` illustrating the main clauses.
  - **Exception 1**: Grave and sudden provocation, containing:
    - Proviso with sub-clauses `(a)`, `(b)`, `(c)`.
    - Subordinate Explanation on question of fact.
    - 6 subordinate Illustrations `(a)` to `(f)` (including inline items like `(f)` which the parser resolved).
  - **Exception 2**: Private defence exceeded in good faith, with its own illustration.
  - **Exception 3**: Public servant acting in good faith.
  - **Exception 4**: Sudden fight without premeditation, with its own explanation.
  - **Exception 5**: Death caused with consent of victim above 18, with its own illustration.

### 7.2 Section 103: Punishment for Murder
- **Components**: Subsection `(1)` (death or imprisonment for life and fine) and Subsection `(2)` (mob lynching: group of 5 or more committing murder on discriminatory grounds).
- **Cross-Section Links**: Both subsections are typed as `PUNISHMENT` and linked via `PUNISHES` to `BNS-SEC-101-MAIN` with confidence $0.95$.

### 7.3 Section 318: Cheating
- **Total Components**: 14 components.
- **Total Relationships**: 23 directed edges.
- **Structural Highlights**:
  - Subsection `(1)`: Substantive definition of cheating (*deception + fraudulent inducement*).
  - Explanation: Concealment of facts is deception (`QUALIFIES` Subsection 1).
  - Illustrations `(a)` to `(i)`: 9 distinct factual illustrations (`PROVIDES_ILLUSTRATION_FOR` Subsection 1).
  - Subsections `(2)`, `(3)`, `(4)`: Aggravated punishments (`PUNISHES` Subsection 1).

---

## 8. Deliverables & Project Artifacts

The Stage 1 deliverables are organized as a clean, modular Python repository:

```text
MR Project/
├── bns_kb/
│   ├── config.py                 # Paths, thresholds, schema & pipeline versions
│   ├── ingestion.py              # BNS dataset loader & SHA-256 provenance tracker
│   ├── schemas/
│   │   ├── components.py         # ComponentType & Component Pydantic models
│   │   ├── relationships.py      # RelationType & Relationship Pydantic models
│   │   └── provenance.py         # ProvenanceMetadata, ValidationReport, SectionStorageRecord
│   ├── extractors/
│   │   ├── rule_based_parser.py  # High-precision statutory state-machine parser
│   │   └── llm_client.py         # Optional OpenAI API (gpt-4o-mini) structured output interface
│   ├── validators/
│   │   ├── structural_validator.py # DAG, ID uniqueness, acyclicity checks
│   │   ├── source_validator.py     # Verbatim substring & coverage checks
│   │   └── relationship_validator.py# Endpoint & cycle integrity checks
│   ├── storage/
│   │   ├── checkpoint.py         # Run checkpoint manager
│   │   └── exporter.py           # Exports JSONL, review CSVs, and validation JSON
│   └── pipeline.py               # End-to-end pipeline runner
├── data/
│   ├── raw/
│   │   ├── bns_sections.csv      # Source BNS 2023 enacted dataset (358 sections)
│   │   └── BNS.md                # Dataset documentation & citation metadata
│   └── output/
│       ├── knowledge_base.jsonl      # Complete machine-readable statutory knowledge base
│       ├── review_components.csv     # 1,415 rows for human legal audit
│       ├── review_relationships.csv  # 1,482 rows for relational edge audit
│       ├── validation_summary.json   # Full validation metrics & distribution summary
│       └── checkpoint.json           # Execution checkpoint cache
├── tests/
│   ├── test_schemas.py           # Unit tests for Pydantic schemas
│   ├── test_validators.py        # Unit tests for DAG, substring, and edge validators
│   └── test_pipeline.py          # Unit tests for pipeline execution
├── run_kb_pipeline.py            # CLI entry point to run pilot or full Act
├── bns_kb_pipeline.ipynb         # Interactive Jupyter / Google Colab notebook
└── docs/
    └── KNOWLEDGE_BASE_CONSTRUCTION_REPORT.md  # Comprehensive research report
```

---

## 9. Readiness for Downstream Stages

With Stage 1 successfully constructed and verified, the project possesses the required formal foundation for subsequent stages:

1. **Stage 2 (Complex Legal Scenario Construction)**:
   - Scenarios can be systematically designed around the verified components (e.g., testing whether an agent correctly detects Exception 1 of Section 101 or falls into the provocation proviso limitation).
2. **Stage 3 (First-Order Logic Formalization)**:
   - Each verified component provides an exact semantic scope for predicate conversion:
     - Offence rule: $\text{Human}(x) \land \text{CausesDeath}(x, y) \land \text{IntentionToCauseDeath}(x) \to \text{PrimaFacieMurder}(x)$
     - Exception rule: $\text{GraveSuddenProvocation}(x, y) \land \neg \text{ProvocationVoluntarilyProvoked}(x) \to \text{Exception1Applies}(x)$
     - Negation rule: $\text{PrimaFacieMurder}(x) \land \text{Exception1Applies}(x) \to \text{CulpableHomicideNotMurder}(x)$
3. **Stage 5 (Verification & Explanation Engine)**:
   - Audit trail allows any derived conclusion to point back to the exact component ID (e.g., `BNS-SEC-101-EXC-1-PROV-1-CL-A`) and its statutory span.
