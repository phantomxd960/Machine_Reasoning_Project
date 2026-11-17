"""
Deterministic Rule-Based Legal Grammar Parser for BNS 2023.
Extracts components with exact substring spans and establishes relational topology.
"""
import re
from typing import List, Dict, Tuple, Optional, Any, Set
from bns_kb.schemas.components import Component, ComponentType
from bns_kb.schemas.relationships import Relationship, RelationType

class RuleBasedBNSParser:
    """
    Deconstructs statutory sections into typed legal components and directed relationships.
    """
    def __init__(self, section_name_mapping: Optional[Dict[str, int]] = None):
        """
        Optional section_name_mapping maps lowercase offence keywords (e.g. 'murder', 'cheating')
        to their defining section number (e.g. 101, 318) for cross-section punishment mapping.
        """
        self.section_name_mapping = section_name_mapping or {}

    def parse(
        self,
        section_number: int,
        section_name: str,
        raw_text: str
    ) -> Tuple[List[Component], List[Relationship]]:
        components: List[Component] = []
        relationships: List[Relationship] = []
        seen_ids: Set[str] = set()

        def get_unique_id(base_id: str) -> str:
            if base_id not in seen_ids:
                seen_ids.add(base_id)
                return base_id
            idx = 2
            while f"{base_id}-{idx}" in seen_ids:
                idx += 1
            uniq = f"{base_id}-{idx}"
            seen_ids.add(uniq)
            return uniq

        # 1. Structural boundary regex
        marker_regex = re.compile(
            r'(?P<boundary>(?:^|\n|(?<=[.;—–]))\s*)'
            r'(?:'
            r'(?P<exception>Exception\s+\d+\s*[.—–-]+|Exception\s*[.—–-]+)|'
            r'(?P<explanation>Explanation\s+\d+\s*[.—–-]+|Explanation\s*[.—–-]+)|'
            r'(?P<proviso>Provided\s+further\s+that\b|Provided\s+that\b)|'
            r'(?P<illustrations_hdr>Illustrations?\s*[.:—–-]+)|'
            r'(?P<subsection>\((?P<ss_num>\d+)\)\s+)|'
            r'(?P<clause>\((?P<cl_letter>[a-z])\)\s+)|'
            r'(?P<subclause>\((?P<scl_roman>[ivxlcdm]+)\)\s+)'
            r')',
            re.IGNORECASE
        )

        raw_markers = []
        for m in marker_regex.finditer(raw_text):
            gd = m.groupdict()
            matched_kind = None
            for k in ['exception', 'explanation', 'proviso', 'illustrations_hdr', 'subsection', 'clause', 'subclause']:
                if gd.get(k):
                    matched_kind = k
                    break
            boundary_len = len(gd.get('boundary') or '')
            start_idx = m.start() + boundary_len
            end_idx = m.end()
            raw_markers.append({
                'kind': matched_kind,
                'start': start_idx,
                'end': end_idx,
                'text': raw_text[start_idx:end_idx],
                'details': {k: v for k, v in gd.items() if v and k != 'boundary'}
            })

        # If no internal markers exist, treat entire section as MAIN_PROVISION
        if not raw_markers:
            is_punish = bool(re.search(r'\b(?:punished with|punishable with|imprisonment|liable to fine)\b', raw_text, re.I))
            is_def = bool(re.search(r'\b(?:is said to|means|includes|denotes)\b', raw_text, re.I))
            if is_punish and not is_def:
                c_type = ComponentType.PUNISHMENT
            elif is_def and not is_punish:
                c_type = ComponentType.DEFINITION
            else:
                c_type = ComponentType.MAIN_PROVISION
            comp_id = get_unique_id(f"BNS-SEC-{section_number}-MAIN")
            clean_str = raw_text.strip()
            c_start = raw_text.find(clean_str)
            c_end = c_start + len(clean_str)
            components.append(Component(
                id=comp_id,
                section_number=section_number,
                component_type=c_type,
                statutory_label=None,
                parent_id=None,
                verbatim_text=raw_text[c_start:c_end],
                char_start=c_start,
                char_end=c_end,
                is_punishment=is_punish,
                is_definition=is_def
            ))
            return components, relationships

        # Segment raw_text into blocks
        blocks = []
        if raw_markers[0]['start'] > 0:
            preamble = raw_text[:raw_markers[0]['start']].strip()
            if preamble:
                p_start = raw_text.find(preamble)
                p_end = p_start + len(preamble)
                blocks.append({
                    'kind': 'preamble',
                    'marker': None,
                    'char_start': p_start,
                    'char_end': p_end,
                    'verbatim_text': raw_text[p_start:p_end]
                })

        for i, m in enumerate(raw_markers):
            m_start = m['start']
            next_start = raw_markers[i+1]['start'] if i + 1 < len(raw_markers) else len(raw_text)
            block_text = raw_text[m_start:next_start].strip()
            if not block_text:
                continue
            b_start = raw_text.find(block_text, m_start)
            b_end = b_start + len(block_text)
            blocks.append({
                'kind': m['kind'],
                'marker': m,
                'char_start': b_start,
                'char_end': b_end,
                'verbatim_text': raw_text[b_start:b_end]
            })

        # State machine across blocks
        main_id = f"BNS-SEC-{section_number}-MAIN"
        current_subsection_id: Optional[str] = None
        current_exception_id: Optional[str] = None
        current_proviso_id: Optional[str] = None
        current_explanation_id: Optional[str] = None
        current_clause_id: Optional[str] = None
        in_illustrations_target: Optional[str] = None

        # Sequence state used to tell a lettered item "(i)"/"(v)"/"(x)" from a roman sub-clause
        last_letter: Optional[str] = None      # last lettered clause/illustration in the open container
        last_roman: Optional[str] = None       # last roman sub-clause under the open clause

        expl_count = 0
        prov_count = 0
        exc_count = 0
        ill_count = 0
        has_main_provision = False

        for b_idx, b in enumerate(blocks):
            kind = b['kind']
            text = b['verbatim_text']
            m_info = b.get('marker')

            is_punish = bool(re.search(r'\b(?:shall be punished|punished with|punishable with|imprisonment|liable to fine)\b', text, re.I))
            is_def = bool(re.search(r'\b(?:is said to|means|includes|denotes)\b', text, re.I))

            if kind == 'preamble':
                has_main_provision = True
                comp_id = get_unique_id(main_id)
                components.append(Component(
                    id=comp_id,
                    section_number=section_number,
                    component_type=ComponentType.DEFINITION if (is_def and not is_punish) else ComponentType.MAIN_PROVISION,
                    statutory_label=None,
                    parent_id=None,
                    verbatim_text=text,
                    char_start=b['char_start'],
                    char_end=b['char_end'],
                    is_punishment=is_punish,
                    is_definition=is_def
                ))
                continue

            if kind == 'subsection':
                ss_num = m_info['details'].get('ss_num', '1') if m_info else '1'
                comp_id = get_unique_id(f"BNS-SEC-{section_number}-SS-{ss_num}")
                current_subsection_id = comp_id
                current_exception_id = None
                current_proviso_id = None
                current_explanation_id = None
                current_clause_id = None
                last_letter = None
                last_roman = None
                in_illustrations_target = None

                parent = main_id if has_main_provision else None
                c_type = ComponentType.PUNISHMENT if (is_punish and not is_def and 'whoever' in text.lower() and 'shall be punished' in text.lower()) else ComponentType.SUBSECTION

                components.append(Component(
                    id=comp_id,
                    section_number=section_number,
                    component_type=c_type,
                    statutory_label=f"({ss_num})",
                    parent_id=parent,
                    verbatim_text=text,
                    char_start=b['char_start'],
                    char_end=b['char_end'],
                    is_punishment=is_punish,
                    is_definition=is_def
                ))
                continue

            if kind == 'exception':
                exc_count += 1
                exc_match = re.search(r'Exception\s+(\d+)', text, re.I)
                num_str = exc_match.group(1) if exc_match else str(exc_count)
                parent = current_subsection_id or (main_id if has_main_provision else None)
                comp_id = get_unique_id(f"BNS-SEC-{section_number}-EXC-{num_str}")
                current_exception_id = comp_id
                current_proviso_id = None
                current_explanation_id = None
                current_clause_id = None
                last_letter = None
                last_roman = None
                in_illustrations_target = None

                components.append(Component(
                    id=comp_id,
                    section_number=section_number,
                    component_type=ComponentType.EXCEPTION,
                    statutory_label=f"Exception {num_str}",
                    parent_id=parent,
                    verbatim_text=text,
                    char_start=b['char_start'],
                    char_end=b['char_end'],
                    is_punishment=is_punish,
                    is_definition=is_def
                ))
                continue

            if kind == 'proviso':
                prov_count += 1
                parent = current_explanation_id or current_exception_id or current_subsection_id or (main_id if has_main_provision else None)
                base = f"{parent}-PROV-{prov_count}" if parent else f"BNS-SEC-{section_number}-PROV-{prov_count}"
                comp_id = get_unique_id(base)
                current_proviso_id = comp_id
                last_letter = None
                last_roman = None
                current_clause_id = None
                in_illustrations_target = None

                components.append(Component(
                    id=comp_id,
                    section_number=section_number,
                    component_type=ComponentType.PROVISO,
                    statutory_label="Provided that",
                    parent_id=parent,
                    verbatim_text=text,
                    char_start=b['char_start'],
                    char_end=b['char_end'],
                    is_punishment=is_punish,
                    is_definition=is_def
                ))
                continue

            if kind == 'explanation':
                expl_count += 1
                expl_match = re.search(r'Explanation\s+(\d+)', text, re.I)
                expl_num_str = expl_match.group(1) if expl_match else str(expl_count)
                parent = current_exception_id or current_subsection_id or (main_id if has_main_provision else None)
                base = f"{parent}-EXPL-{expl_num_str}" if parent else f"BNS-SEC-{section_number}-EXPL-{expl_num_str}"
                comp_id = get_unique_id(base)
                current_explanation_id = comp_id
                last_letter = None
                last_roman = None
                current_proviso_id = None
                current_clause_id = None
                in_illustrations_target = None

                components.append(Component(
                    id=comp_id,
                    section_number=section_number,
                    component_type=ComponentType.EXPLANATION,
                    statutory_label=f"Explanation {expl_num_str}",
                    parent_id=parent,
                    verbatim_text=text,
                    char_start=b['char_start'],
                    char_end=b['char_end'],
                    is_punishment=is_punish,
                    is_definition=is_def
                ))
                continue

            if kind == 'illustrations_hdr':
                last_letter = None
                in_illustrations_target = current_explanation_id or current_exception_id or current_subsection_id or (main_id if has_main_provision else None)
                header_stripped = re.sub(r'^Illustrations?\s*[.:—–-]*\s*', '', text, flags=re.I).strip()
                if header_stripped and not re.match(r'^\([a-z]\)', header_stripped, re.I):
                    ill_count += 1
                    base = f"{in_illustrations_target}-ILL-{ill_count}" if in_illustrations_target else f"BNS-SEC-{section_number}-ILL-{ill_count}"
                    comp_id = get_unique_id(base)
                    components.append(Component(
                        id=comp_id,
                        section_number=section_number,
                        component_type=ComponentType.ILLUSTRATION,
                        statutory_label="Illustration",
                        parent_id=in_illustrations_target,
                        verbatim_text=text,
                        char_start=b['char_start'],
                        char_end=b['char_end'],
                        is_punishment=False,
                        is_definition=False
                    ))
                    in_illustrations_target = None
                continue

            if kind == 'clause':
                cl_letter = m_info['details'].get('cl_letter', 'a').lower() if m_info else 'a'
                # "(i)", "(v)" and "(x)" are both letters and roman numerals. Continue the lettered
                # sequence when they are its next letter; otherwise read them as roman sub-clauses
                # when a roman list is plausible at this point.
                if cl_letter in ('i', 'v', 'x'):
                    next_letter = chr(ord(last_letter) + 1) if last_letter else 'a'
                    roman_prev = {'i': None, 'v': 'iv', 'x': 'ix'}[cl_letter]
                    nb = blocks[b_idx + 1] if b_idx + 1 < len(blocks) else None
                    next_is_ii = bool(nb and nb['kind'] == 'subclause' and nb['marker']
                                      and nb['marker']['details'].get('scl_roman', '').lower() == 'ii')
                    if cl_letter != next_letter and (
                        (cl_letter == 'i' and next_is_ii)
                        # source quirk: "(ii)" glued to other text (e.g. "span@(ii)") stays inside this block
                        or (cl_letter == 'i' and '(ii)' in text)
                        or (cl_letter == 'i' and last_letter is not None and not in_illustrations_target)
                        or (roman_prev is not None and last_roman == roman_prev)
                    ):
                        kind = 'subclause'
                        m_info = {'details': {'scl_roman': cl_letter}}

            if kind == 'clause':
                last_letter = cl_letter
                last_roman = None
                if in_illustrations_target:
                    base = f"{in_illustrations_target}-ILL-{cl_letter.upper()}"
                    comp_id = get_unique_id(base)
                    components.append(Component(
                        id=comp_id,
                        section_number=section_number,
                        component_type=ComponentType.ILLUSTRATION,
                        statutory_label=f"Illustration ({cl_letter})",
                        parent_id=in_illustrations_target,
                        verbatim_text=text,
                        char_start=b['char_start'],
                        char_end=b['char_end'],
                        is_punishment=False,
                        is_definition=False
                    ))
                else:
                    parent = current_proviso_id or current_explanation_id or current_subsection_id or (main_id if has_main_provision else None)
                    base = f"{parent}-CL-{cl_letter.upper()}" if parent else f"BNS-SEC-{section_number}-CL-{cl_letter.upper()}"
                    comp_id = get_unique_id(base)
                    current_clause_id = comp_id
                    components.append(Component(
                        id=comp_id,
                        section_number=section_number,
                        component_type=ComponentType.CLAUSE,
                        statutory_label=f"({cl_letter})",
                        parent_id=parent,
                        verbatim_text=text,
                        char_start=b['char_start'],
                        char_end=b['char_end'],
                        is_punishment=is_punish,
                        is_definition=is_def
                    ))
                continue

            if kind == 'subclause':
                scl_roman = m_info['details'].get('scl_roman', 'i').lower() if m_info else 'i'
                last_roman = scl_roman
                parent = current_clause_id or current_proviso_id or current_explanation_id or current_subsection_id or (main_id if has_main_provision else None)
                base = f"{parent}-SCL-{scl_roman.upper()}" if parent else f"BNS-SEC-{section_number}-SCL-{scl_roman.upper()}"
                comp_id = get_unique_id(base)
                components.append(Component(
                    id=comp_id,
                    section_number=section_number,
                    component_type=ComponentType.SUBCLAUSE,
                    statutory_label=f"({scl_roman})",
                    parent_id=parent,
                    verbatim_text=text,
                    char_start=b['char_start'],
                    char_end=b['char_end'],
                    is_punishment=is_punish,
                    is_definition=is_def
                ))
                continue

        # If only one component was extracted without an explicit parent, ensure clean main ID
        if not components:
            clean_str = raw_text.strip()
            c_start = raw_text.find(clean_str)
            c_end = c_start + len(clean_str)
            comp_id = get_unique_id(main_id)
            components.append(Component(
                id=comp_id,
                section_number=section_number,
                component_type=ComponentType.MAIN_PROVISION,
                statutory_label=None,
                parent_id=None,
                verbatim_text=raw_text[c_start:c_end],
                char_start=c_start,
                char_end=c_end,
                is_punishment=False,
                is_definition=False
            ))

        # Generate relationships
        rel_idx = 1
        for c in components:
            # 1. Structural HAS_CHILD
            if c.parent_id:
                relationships.append(Relationship(
                    id=f"BNS-REL-{section_number}-{rel_idx:03d}",
                    section_number=section_number,
                    source_id=c.parent_id,
                    relation_type=RelationType.HAS_CHILD,
                    target_id=c.id,
                    evidence_quote=c.verbatim_text[:80] + "..." if len(c.verbatim_text) > 80 else c.verbatim_text,
                    confidence=1.0
                ))
                rel_idx += 1

            # 2. QUALIFIES for Explanations and Provisos
            if c.component_type in (ComponentType.EXPLANATION, ComponentType.PROVISO) and c.parent_id:
                relationships.append(Relationship(
                    id=f"BNS-REL-{section_number}-{rel_idx:03d}",
                    section_number=section_number,
                    source_id=c.id,
                    relation_type=RelationType.QUALIFIES,
                    target_id=c.parent_id,
                    evidence_quote=c.verbatim_text[:80] + "..." if len(c.verbatim_text) > 80 else c.verbatim_text,
                    confidence=1.0
                ))
                rel_idx += 1

            # 3. EXCEPTION_TO for Exceptions
            if c.component_type == ComponentType.EXCEPTION:
                target = main_id if any(x.id == main_id for x in components) else (c.parent_id or components[0].id)
                relationships.append(Relationship(
                    id=f"BNS-REL-{section_number}-{rel_idx:03d}",
                    section_number=section_number,
                    source_id=c.id,
                    relation_type=RelationType.EXCEPTION_TO,
                    target_id=target,
                    evidence_quote=c.verbatim_text[:80] + "..." if len(c.verbatim_text) > 80 else c.verbatim_text,
                    confidence=1.0
                ))
                rel_idx += 1

            # 4. PROVIDES_ILLUSTRATION_FOR
            if c.component_type == ComponentType.ILLUSTRATION and c.parent_id:
                relationships.append(Relationship(
                    id=f"BNS-REL-{section_number}-{rel_idx:03d}",
                    section_number=section_number,
                    source_id=c.id,
                    relation_type=RelationType.PROVIDES_ILLUSTRATION_FOR,
                    target_id=c.parent_id,
                    evidence_quote=c.verbatim_text[:80] + "..." if len(c.verbatim_text) > 80 else c.verbatim_text,
                    confidence=1.0
                ))
                rel_idx += 1

            # 5. Intra-section PUNISHES
            if c.is_punishment and c.component_type in (ComponentType.SUBSECTION, ComponentType.PUNISHMENT):
                offence_comps = [x.id for x in components if x.is_definition or x.component_type in (ComponentType.MAIN_PROVISION, ComponentType.DEFINITION)]
                for off_id in offence_comps:
                    if off_id != c.id:
                        relationships.append(Relationship(
                            id=f"BNS-REL-{section_number}-{rel_idx:03d}",
                            section_number=section_number,
                            source_id=c.id,
                            relation_type=RelationType.PUNISHES,
                            target_id=off_id,
                            evidence_quote=c.verbatim_text[:80] + "..." if len(c.verbatim_text) > 80 else c.verbatim_text,
                            confidence=1.0
                        ))
                        rel_idx += 1

            # 6. Cross-Section statutory references (e.g. 'section 100')
            cross_ref_matches = re.finditer(r'\bsection\s+(\d+)\b', c.verbatim_text, re.IGNORECASE)
            for cm in cross_ref_matches:
                ref_sec = int(cm.group(1))
                if ref_sec != section_number and 1 <= ref_sec <= 358:
                    target_ref = f"BNS-SEC-{ref_sec}-MAIN"
                    relationships.append(Relationship(
                        id=f"BNS-REL-{section_number}-{rel_idx:03d}",
                        section_number=section_number,
                        source_id=c.id,
                        relation_type=RelationType.CROSS_REFERENCES,
                        target_id=target_ref,
                        evidence_quote=cm.group(0),
                        confidence=1.0
                    ))
                    rel_idx += 1

        # 7. Cross-section punishment detection from Section Name
        if "punishment for" in section_name.lower():
            offence_kw = section_name.lower().replace("punishment for", "").strip(" .—–-")
            target_sec = self.section_name_mapping.get(offence_kw)
            if target_sec and target_sec != section_number:
                for c in components:
                    if c.is_punishment or c.component_type in (ComponentType.SUBSECTION, ComponentType.PUNISHMENT):
                        relationships.append(Relationship(
                            id=f"BNS-REL-{section_number}-{rel_idx:03d}",
                            section_number=section_number,
                            source_id=c.id,
                            relation_type=RelationType.PUNISHES,
                            target_id=f"BNS-SEC-{target_sec}-MAIN",
                            evidence_quote=f"Section {section_number} ({section_name}) provides penalty for Section {target_sec}",
                            confidence=0.95
                        ))
                        rel_idx += 1

        return components, relationships
