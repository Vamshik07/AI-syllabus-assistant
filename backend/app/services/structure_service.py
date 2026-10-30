import re
import logging
from typing import Dict, List, Any, Tuple, Optional
from app.services.ai_service import ai_service
from app.services.validation_service import validation_service
from app.services.prompts.structure_prompt import STRUCTURE_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)

def clean_subtopic_name(name: Optional[str], parent_topic_name: Optional[str] = None) -> Optional[str]:
    """Cleans a candidate subtopic name, rejecting equation fragments, OCR junk, single letters, and noise."""
    if not name:
        return None
    # Strip leading/trailing bullets, punctuation, spaces, math symbols
    cleaned = re.sub(r'^[•\-\*~_|=.\s\d\)\(]+|[•\-\*~_|=.\s\d\)\(]+$', '', name).strip()
    # Strip leading OCR artifact letters e.g. "E The Decision" -> "The Decision"
    cleaned = re.sub(r'^[A-Z]\s+(?=[A-Z][a-z])', '', cleaned)
    # Strip trailing OCR artifacts e.g. "Process gy" -> "Process"
    cleaned = re.sub(r'\s+[a-z]{1,2}$', '', cleaned)
    if len(cleaned) < 4 or len(cleaned) > 65:
        return None
    # Must have at least one alphabetic word with >= 3 characters
    if not re.search(r'[A-Za-z]{3,}', cleaned):
        return None
    # Must not be pure symbol noise or equation fragment like "_Plan | ="
    if re.search(r'[_|=~]{2,}', cleaned) or re.match(r'^[_\W\d]+$', cleaned):
        return None
    # Reject presenter / admin boilerplate lines
    from app.services.learning_service import is_presenter_or_admin_line
    if is_presenter_or_admin_line(cleaned):
        return None
    # Reject generic "Slide N"
    if cleaned.lower().startswith("slide "):
        return None
    if parent_topic_name:
        p_norm = re.sub(r'[^a-z0-9]', '', parent_topic_name.lower())
        c_norm = re.sub(r'[^a-z0-9]', '', cleaned.lower())
        # If identical or single word duplicate of parent topic
        if c_norm == p_norm or (len(cleaned.split()) == 1 and (c_norm in p_norm or p_norm in c_norm)):
            return None
    return cleaned

class StructureService:
    def extract_structure(
        self,
        file_type: str,
        parsed_doc: Dict[str, Any],
        syllabus_topics: Optional[List[str]] = None,
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Extracts topics and subtopics following strict deterministic priority:
        1. Syllabus mapping (canonical names) if syllabus is provided
        2. Native/explicit headings & Agenda/Index
        3. Semantic Topic Boundary Detection & Multi-slide/page merging
        4. Typography & layout information
        5. AI assistance only if needed
        Returns (topics_list, status) where status is 'EXTRACTED', 'VERIFIED', or 'REVIEW_REQUIRED'.
        """
        topics = []
        file_type = file_type.upper()
        source_text = parsed_doc.get("full_text", "")

        if file_type == "DOCX":
            topics = self._extract_docx_structure(parsed_doc, syllabus_topics)
        elif file_type == "PPTX":
            topics = self._extract_pptx_structure(parsed_doc, syllabus_topics)
        elif file_type == "PDF":
            topics = self._extract_pdf_structure(parsed_doc, syllabus_topics)

        # If deterministic extraction yielded no topics, try numbered headings from source text
        if not topics and source_text:
            topics = self._extract_numbered_headings(source_text)

        # If still no topics and AI is available, use AI assistance
        if not topics and ai_service.is_available() and source_text:
            topics = self._extract_with_ai(source_text)

        # If still no topics, generate fallback topic from document title or first page
        if not topics:
            topics = [{
                "name": "Unit Overview",
                "order_index": 1,
                "source_start": "1",
                "source_end": "1",
                "confidence": 0.8,
                "subtopics": []
            }]

        # Visual headings are source-derived semantic metadata, but are
        # intentionally not copied into the authoritative native slide text.
        validation_source = source_text
        if file_type == "PPTX":
            visual_titles = [
                slide.get("title", "").strip()
                for slide in parsed_doc.get("slides", [])
                if slide.get("visual_title") and slide.get("title")
            ]
            validation_source = "\n".join([source_text, *visual_titles])

        # Run programmatic source validation
        is_valid, errors = validation_service.validate_structure(topics, validation_source)
        if not is_valid:
            logger.warning(f"Structure validation failed: {errors}. Setting status to REVIEW_REQUIRED.")
            return topics, "REVIEW_REQUIRED"

        return topics, "VERIFIED"

    def _extract_docx_structure(
        self, parsed_doc: Dict[str, Any], syllabus_topics: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Extracts topics from DOCX using syllabus mapping or native Heading 1 and Heading 2 styles."""
        elements = parsed_doc.get("elements", [])
        topics = []
        topic_order = 1
        subtopic_order = 1

        if syllabus_topics and len(syllabus_topics) > 0:
            # Map DOCX elements to canonical syllabus topics
            curr_syl_idx = 0
            for syl_name in syllabus_topics:
                topics.append({
                    "name": syl_name,
                    "order_index": len(topics) + 1,
                    "source_start": "Element 0",
                    "source_end": "Element 0",
                    "confidence": 1.0,
                    "subtopics": [],
                })
            # Map elements into syllabus topics based on heading matches
            for el in elements:
                text = el.get("text", "").strip()
                if not text:
                    continue
                norm_text = re.sub(r'[^a-z0-9]', '', text.lower())
                for idx, t in enumerate(topics):
                    norm_t = re.sub(r'[^a-z0-9]', '', t["name"].lower())
                    if norm_t and (norm_t in norm_text or norm_text in norm_t):
                        curr_syl_idx = idx
                        t["source_end"] = f"Element {el.get('element_order')}"
                        break
                topics[curr_syl_idx]["source_end"] = f"Element {el.get('element_order')}"
            return topics

        current_topic = None
        for el in elements:
            heading_level = el.get("heading_level", 0)
            text = el.get("text", "").strip()
            if not text:
                continue

            if heading_level == 1:
                current_topic = {
                    "name": text,
                    "order_index": topic_order,
                    "source_start": f"Element {el.get('element_order')}",
                    "source_end": f"Element {el.get('element_order')}",
                    "confidence": 1.0,
                    "subtopics": [],
                }
                topics.append(current_topic)
                topic_order += 1
                subtopic_order = 1
            elif heading_level == 2:
                if current_topic is None:
                    current_topic = {
                        "name": "Introduction",
                        "order_index": topic_order,
                        "source_start": f"Element {el.get('element_order')}",
                        "source_end": f"Element {el.get('element_order')}",
                        "confidence": 0.9,
                        "subtopics": [],
                    }
                    topics.append(current_topic)
                    topic_order += 1
                    subtopic_order = 1

                clean_text = clean_subtopic_name(text)
                if clean_text:
                    subtopic = {
                        "name": clean_text,
                        "order_index": subtopic_order,
                        "source_start": f"Element {el.get('element_order')}",
                        "source_end": f"Element {el.get('element_order')}",
                        "confidence": 1.0,
                    }
                    current_topic["subtopics"].append(subtopic)
                    subtopic_order += 1

        return topics

    def _is_continuation_slide(
        self, prev_topic: Dict[str, Any], title: str, slide: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Determines whether a slide continues the active learning topic:
        - Exact or normalized title match
        - Acronym matching (e.g. 'Space Division Multiple Access' <-> 'SDMA', 'SDMA Features', 'Working of SDMA')
        - Aspect continuation (features, characteristics, types, architecture, working, advantages, disadvantages, examples, etc.)
        - Substring / normalized inclusion ('SDMA' in 'SDMA Features')
        - Explicit continuation markers ('continued', 'cont.', 'part 2', etc.)
        - Explanatory/sentence-like titles ('Planning is a process...', 'Why Planning is Important?')
        - Process step continuation ('Steps in Planning' when active is 'Planning Process')
        - Minimal text / image-only / diagram slides
        """
        if not prev_topic:
            return False, None

        prev_name = prev_topic["name"].strip()
        norm_prev = re.sub(r'[^a-z0-9]', '', prev_name.lower())
        norm_title = re.sub(r'[^a-z0-9]', '', title.lower())
        lower_title = title.lower()

        if not norm_title or norm_title == norm_prev:
            return True, None

        # 1. Explicit continuation words in title
        cont_keywords = ["continue", "contd", "cont.", "(cont", "part 2", "part ii", "part 3", "part iii", "(2)", "(ii)"]
        if any(ck in lower_title for ck in cont_keywords):
            return True, None

        # Major topic starters - these begin new topics rather than continuing a broad topic
        major_starters = ["characteristics of", "types of", "classification of", "principles of", "elements of", "process of"]
        is_major_starter = any(lower_title.startswith(ms) for ms in major_starters)

        # 2. Acronym matching: e.g. 'Space Division Multiple Access (SDMA)' <-> 'SDMA Features'
        # Extract meaningful acronyms (>= 3 chars)
        def get_acronyms(text: str) -> List[str]:
            acros = []
            paren_matches = re.findall(r'\(([A-Z0-9]{3,8})\)', text)
            acros.extend(paren_matches)
            words = [w for w in re.split(r'[\s\-_/]+', text) if w and w[0].isupper()]
            if len(words) >= 3:
                initials = "".join(w[0] for w in words).upper()
                if len(initials) >= 3:
                    acros.append(initials)
            caps = re.findall(r'\b[A-Z0-9]{3,8}\b', text)
            acros.extend([c for c in caps if c not in ["AND", "FOR", "THE", "UNIT", "PART"]])
            return list(set(acros))

        prev_acros = get_acronyms(prev_name)
        for pa in prev_acros:
            if re.search(r'\b' + re.escape(pa) + r'\b', title, re.IGNORECASE):
                # An acronym aspect like "SDMA Features" or "Working of SDMA" continues the acronym topic
                if any(ak in lower_title for ak in ["feature", "working", "operation", "architecture", "diagram", "advantage", "disadvantage", "example", "application", "overview", "principle"]):
                    subtopic = title if len(title) <= 50 else None
                    return True, subtopic

        # 3. Sentence-like or explanatory title (e.g. "Planning is a process...", "Why Planning is Important?")
        words = title.split()
        is_sentence = (
            len(words) >= 5
            or any(verb in lower_title for verb in [" is ", " are ", " involves ", " refers to ", " defined as "])
            or any(aspect in lower_title for aspect in ["importance of", "need for", "significance of", "scope of", "objectives of", "definition of", "why "])
            or title.endswith("?")
        )
        if is_sentence and not is_major_starter:
            prev_core_words = [
                w for w in re.findall(r'[a-z0-9]{4,}', prev_name.lower())
                if w not in ["unit", "chapter", "topic", "overview", "introduction"]
            ]
            if any(pw in lower_title for pw in prev_core_words):
                return True, (title if len(title) <= 50 else None)

        # 4. Process continuation: e.g. Prev="Planning Process", Current="Steps in Planning"
        prev_is_process = any(k in prev_name.lower() for k in ["process", "steps", "cycle", "workflow", "method", "procedure", "stages"])
        curr_is_steps = any(k in lower_title for k in ["step", "steps", "stage", "stages", "phase", "phases", "procedure", "how to"])
        prev_core = [w for w in re.findall(r'[a-z0-9]{4,}', prev_name.lower()) if w not in ["process", "system", "overview", "introduction", "unit", "chapter"]]
        curr_core = [w for w in re.findall(r'[a-z0-9]{4,}', lower_title) if w not in ["steps", "step", "stages", "phase", "overview", "part"]]

        if prev_is_process and curr_is_steps:
            if not prev_core or any(pc in curr_core for pc in prev_core):
                subtopic = title if len(title) <= 50 else None
                return True, subtopic

        # 5. Classifications / Features continuation
        prev_is_classification = any(k in prev_name.lower() for k in ["characteristics", "features", "types", "classification", "principles", "elements", "components"])
        if prev_is_classification:
            if any(k in lower_title for k in ["characteristic", "feature", "continued", "cont", "part", "aspect"]):
                subtopic = title if len(title) <= 50 else None
                return True, subtopic
            if len(words) <= 4 and not any(k in lower_title for k in ["types of", "process", "framework", "decision", "management", "concept of"]):
                subtopic = title if len(title) <= 45 else None
                return True, subtopic

        # 6. Visual / Diagram slide with image or table:
        # User requirement: "if images related to any particular topic just add it to the topic dont consider image as separate topic"
        elements = slide.get("elements", [])
        has_image_or_table = any(el.get("type") in ("IMAGE", "TABLE") for el in elements)
        is_full_slide_image = slide.get("is_image_slide", False)
        if has_image_or_table and not is_full_slide_image:
            # Check if this slide has an explicit major unit/chapter transition (e.g. "Unit 3", "Chapter 4")
            is_new_unit_transition = bool(re.match(r'^(?:unit|chapter|module|part)\s+[ivxlcdm\d]+', lower_title))
            if not is_new_unit_transition and not is_major_starter:
                clean_sub = clean_subtopic_name(title)
                # Only use title as subtopic if it doesn't match or duplicate previous topic
                if clean_sub and norm_prev not in re.sub(r'[^a-z0-9]', '', clean_sub.lower()):
                    return True, clean_sub
                return True, None

        return False, None

    def _extract_pptx_structure(
        self, parsed_doc: Dict[str, Any], syllabus_topics: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extracts topics and subtopics from PPTX preserving slide order and pedagogical hierarchy:
        1. If syllabus is provided, maps slides into canonical syllabus topics.
        2. Detects an index/agenda slide at the beginning and aligns subsequent slides.
        3. If no agenda/index exists, uses Semantic Boundary Detection and Multi-Slide Merging.
        4. Never names a topic 'Slide N'.
        """
        slides = parsed_doc.get("slides", [])
        if not slides:
            return []

        def normalize(t: str) -> str:
            return re.sub(r'[^a-z0-9]', '', t.lower())

        def is_generic_slide_title(title: str) -> bool:
            return bool(re.fullmatch(r"slide\s+\d+", title.strip(), re.IGNORECASE))

        def slide_lines(slide: Dict[str, Any]) -> List[str]:
            raw_text = slide.get("text", "")
            lines = []
            for piece in re.split(r'[\r\n]+', raw_text):
                piece = piece.strip()
                if not piece or piece.startswith("---"):
                    continue
                parts = [p.strip() for p in re.split(r'[,;]\s+', piece) if p.strip()]
                if len(parts) >= 3 and all(len(p) > 2 for p in parts):
                    lines.extend(parts)
                else:
                    lines.append(piece)
            return [l for l in lines if len(l) > 2]

        def clean_index_entry(value: str) -> str:
            val = re.sub(r'^title\s*:\s*', '', value, flags=re.IGNORECASE).strip()
            return re.sub(
                r'^(?:\d+[\.\)]|[ivxlcdm]+[\.\)]|\*|-|\u2022)\s*',
                '',
                val,
                flags=re.IGNORECASE,
            ).strip()

        def get_acronym(text: str) -> str:
            return "".join(w[0] for w in re.split(r'[\s\-_/]+', text) if w and w[0].isupper()).lower()

        def is_cover_or_presenter_lines(lines: List[str]) -> bool:
            presenter_indicators = [
                "dr.", "prof.", "professor", "associate professor", "assistant professor",
                "department of", "college of", "university", "faculty of", "school of",
                "presented by", "prepared by", "guided by", "submitted by", "instructor",
            ]
            return any(any(ind in line.lower() for ind in presenter_indicators) for line in lines)

        def is_index_slide(slide: Dict[str, Any]) -> bool:
            title = slide.get("title", "").strip().lower()
            lines = slide_lines(slide)
            if is_cover_or_presenter_lines(lines):
                return False

            title_is_index = any(
                keyword in title
                for keyword in (
                    "index",
                    "contents",
                    "table of contents",
                    "syllabus",
                    "agenda",
                    "course overview",
                )
            )
            slide_num = slide.get("slide_number", 1)
            entries = [clean_index_entry(line) for line in lines]
            entries = [entry for entry in entries if 3 < len(entry) < 100 and normalize(entry) != normalize(title)]
            dense_list = (
                slide_num <= 3
                and len(entries) >= 4
                and not any(step_kw in title for step_kw in ["step", "stage", "process", "rule", "feature", "characteristic", "type", "method"])
            )
            return title_is_index or dense_list

        agenda_topics = syllabus_topics[:] if (syllabus_topics and len(syllabus_topics) > 0) else []
        agenda_slide_idx = -1

        # Check if slide 1, 2, or 3 is an index / agenda / syllabus slide (if no explicit syllabus given)
        if not agenda_topics:
            for idx, slide in enumerate(slides[:3]):
                lines = slide_lines(slide)
                if is_cover_or_presenter_lines(lines):
                    continue
                is_agenda = is_index_slide(slide)
                if not is_agenda and lines:
                    first_line = lines[0].lower()
                    is_agenda = any(
                        kw in first_line
                        for kw in ["syllabus", "agenda", "contents", "table of contents", "overview", "index"]
                    )
                if is_agenda and lines:
                    title_norm = normalize(slide.get("title", ""))
                    candidates = [
                        line for line in lines
                        if normalize(re.sub(r'^title\s*:\s*', '', line, flags=re.IGNORECASE)) != title_norm
                    ]
                    cleaned_cands = []
                    for c in candidates:
                        clean = clean_index_entry(c)
                        if clean and 3 < len(clean) < 100:
                            cleaned_cands.append(clean)
                    if len(cleaned_cands) >= 3:
                        agenda_topics = cleaned_cands
                        agenda_slide_idx = idx
                        break

        if agenda_slide_idx >= 0 and agenda_topics:
            index_slide = slides[agenda_slide_idx]
            parsed_doc["index"] = {
                "slide_number": index_slide.get("slide_number", agenda_slide_idx + 1),
                "title": index_slide.get("title", "").strip() or "Index",
                "entries": agenda_topics,
            }

        topics = []

        if agenda_topics:
            start_slides = slides[agenda_slide_idx + 1:] if agenda_slide_idx >= 0 else slides
            if not start_slides:
                start_slides = slides

            # Step 1: Match each slide to best agenda candidate
            slide_assignments = []
            for slide in start_slides:
                s_num = slide.get("slide_number", 1)
                s_title = slide.get("title", "").strip()
                norm_s = normalize(s_title) if s_title else ""
                s_text = slide.get("text", "").lower()

                best_k = None
                best_score = 0
                for k, ag in enumerate(agenda_topics):
                    norm_ag = normalize(ag)
                    acro_ag = get_acronym(ag)
                    syl_words = [w for w in re.findall(r'[a-z0-9]{4,}', ag.lower()) if w not in ["with", "from"]]

                    if norm_s == norm_ag:
                        best_k = k
                        best_score = 100
                        break
                    elif acro_ag and len(acro_ag) >= 2 and norm_s == acro_ag:
                        if 60 > best_score:
                            best_k = k
                            best_score = 60
                    else:
                        title_matches = sum(2 for w in syl_words if w in norm_s)
                        text_matches = sum(1 for w in syl_words if w in s_text)
                        total = title_matches + text_matches
                        if total > best_score:
                            best_k = k
                            best_score = total

                slide_assignments.append({
                    "slide": slide,
                    "slide_number": s_num,
                    "title": s_title,
                    "agenda_idx": best_k,
                    "score": best_score,
                })

            # Step 2: Gap resolution for intermediate unassigned/repeated slides
            assigned_indices = [sa["agenda_idx"] for sa in slide_assignments]
            for i in range(len(slide_assignments)):
                prev_ag = assigned_indices[i - 1] if i > 0 else 0
                next_ag = assigned_indices[i + 1] if i + 1 < len(assigned_indices) else len(agenda_topics) - 1
                curr_ag = assigned_indices[i]

                if prev_ag is not None and next_ag is not None and next_ag > prev_ag + 1:
                    gap_ag = prev_ag + 1
                    if curr_ag == prev_ag or curr_ag is None:
                        assigned_indices[i] = gap_ag
                        slide_assignments[i]["agenda_idx"] = gap_ag

            # Step 3: Construct topics in agenda sequence
            topics = []
            curr_topic = None
            for sa in slide_assignments:
                ag_idx = sa["agenda_idx"]
                s_num = sa["slide_number"]
                s_title = sa["title"]

                topic_name = agenda_topics[ag_idx] if (ag_idx is not None and ag_idx < len(agenda_topics)) else (s_title or "Introduction")

                if not curr_topic or curr_topic["name"] != topic_name:
                    curr_topic = {
                        "name": topic_name,
                        "order_index": len(topics) + 1,
                        "source_start": str(s_num),
                        "source_end": str(s_num),
                        "confidence": 1.0,
                        "subtopics": [],
                    }
                    clean_s_title = clean_subtopic_name(s_title)
                    if clean_s_title and normalize(clean_s_title) != normalize(topic_name):
                        curr_topic["subtopics"].append({
                            "name": clean_s_title,
                            "order_index": 1,
                            "source_start": str(s_num),
                            "source_end": str(s_num),
                            "confidence": 1.0,
                        })
                    topics.append(curr_topic)
                else:
                    curr_topic["source_end"] = str(s_num)
                    clean_s_title = clean_subtopic_name(s_title)
                    if clean_s_title and normalize(clean_s_title) != normalize(curr_topic["name"]):
                        existing_sub_names = [normalize(st["name"]) for st in curr_topic["subtopics"]]
                        if normalize(clean_s_title) not in existing_sub_names:
                            curr_topic["subtopics"].append({
                                "name": clean_s_title,
                                "order_index": len(curr_topic["subtopics"]) + 1,
                                "source_start": str(s_num),
                                "source_end": str(s_num),
                                "confidence": 1.0,
                            })

            return topics

        def is_cover_or_presenter_slide(s: Dict[str, Any]) -> bool:
            s_num = s.get("slide_number", 1)
            if s_num > 2:
                return False
            lines = slide_lines(s)
            presenter_indicators = [
                "dr.", "prof.", "professor", "associate professor", "assistant professor",
                "department of", "college of", "university", "faculty of", "school of",
                "presented by", "prepared by", "guided by", "submitted by", "instructor",
            ]
            has_presenter = any(any(ind in line.lower() for ind in presenter_indicators) for line in lines)
            return has_presenter and len(lines) <= 7

        # General PPTX fallback (when no agenda/index is present)
        # Applies Semantic Topic Boundary Detection & Multi-Slide Merging
        for slide in slides:
            if is_index_slide(slide):
                parsed_doc.setdefault("index", {
                    "slide_number": slide.get("slide_number", len(topics) + 1),
                    "title": slide.get("title", "").strip() or "Index",
                    "entries": [
                        clean_index_entry(line)
                        for line in slide_lines(slide)[1:]
                        if 3 < len(clean_index_entry(line)) < 100
                    ],
                })
                continue

            title = slide.get("title", "").strip()
            slide_num = slide.get("slide_number", len(topics) + 1)

            if not title or is_generic_slide_title(title):
                if topics:
                    topics[-1]["source_end"] = str(slide_num)
                    continue
                else:
                    # An image-only opening slide is source material, not a
                    # meaningful topic name. Wait for the first real heading.
                    continue

            if topics:
                # If slide 1 was a cover/presenter slide and this is slide 2, merge into topic 1
                if len(topics) == 1 and topics[0]["source_start"] == "1" and topics[0]["source_end"] == "1" and is_cover_or_presenter_slide(slides[0]):
                    topics[0]["name"] = title
                    topics[0]["source_end"] = str(slide_num)
                    continue

                # Image-only slides have no native heading to use for
                # structure. A validated visual heading is therefore a real
                # semantic boundary, not a continuation of the cover topic.
                if slide.get("visual_title") and normalize(title) != normalize(topics[-1]["name"]):
                    topics.append({
                        "name": title,
                        "order_index": len(topics) + 1,
                        "source_start": str(slide_num),
                        "source_end": str(slide_num),
                        "confidence": 0.85,
                        "subtopics": [],
                    })
                    continue

                is_cont, subtopic_name = self._is_continuation_slide(topics[-1], title, slide)
                if is_cont:
                    topics[-1]["source_end"] = str(slide_num)
                    clean_sub = clean_subtopic_name(subtopic_name)
                    if clean_sub and normalize(clean_sub) != normalize(topics[-1]["name"]):
                        existing_sub_names = [normalize(st["name"]) for st in topics[-1]["subtopics"]]
                        if normalize(clean_sub) not in existing_sub_names:
                            topics[-1]["subtopics"].append({
                                "name": clean_sub,
                                "order_index": len(topics[-1]["subtopics"]) + 1,
                                "source_start": str(slide_num),
                                "source_end": str(slide_num),
                                "confidence": 1.0,
                            })
                    continue

            topics.append({
                "name": title,
                "order_index": len(topics) + 1,
                "source_start": str(slide_num),
                "source_end": str(slide_num),
                "confidence": 1.0,
                "subtopics": [],
            })

        return topics

    def _extract_pdf_structure(
        self, parsed_doc: Dict[str, Any], syllabus_topics: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extracts structure from PDF:
        First checks syllabus mapping if provided, then native TOC, then typography/layout (large bold headings), then numbered headings.
        """
        pages = parsed_doc.get("pages", [])
        topics = []

        # 0. Syllabus mapping
        if syllabus_topics and len(syllabus_topics) > 0:
            for s_idx, s_name in enumerate(syllabus_topics):
                topics.append({
                    "name": s_name,
                    "order_index": s_idx + 1,
                    "source_start": None,
                    "source_end": None,
                    "confidence": 1.0,
                    "subtopics": [],
                })

            # Use the first page containing each canonical syllabus name as its
            # boundary, then let each topic own the pages until the next boundary.
            matched_starts = []
            for page in pages:
                p_num = page.get("page_number", 1)
                p_text = page.get("text", "").lower()
                norm_p = re.sub(r'[^a-z0-9]', '', p_text)
                for idx, t in enumerate(topics):
                    norm_t = re.sub(r'[^a-z0-9]', '', t["name"].lower())
                    if norm_t and norm_t in norm_p and not t["source_start"]:
                        t["source_start"] = str(p_num)
                        matched_starts.append((idx, p_num))
                        break

            next_start = 1
            for idx, topic in enumerate(topics):
                starts = [page for topic_idx, page in matched_starts if topic_idx == idx]
                start = starts[0] if starts else next_start
                following = [page for topic_idx, page in matched_starts if topic_idx > idx]
                end = min(following) - 1 if following else (len(pages) or start)
                topic["source_start"] = str(start)
                topic["source_end"] = str(max(start, end))
                next_start = max(start, end) + 1
            return topics

        # 1. Check for Index / Contents / Agenda page in the first 3 pages
        index_topics = []
        index_page_idx = -1
        for p_idx, page in enumerate(pages[:3]):
            lines = [l.strip() for l in page.get("text", "").splitlines() if l.strip()]
            for l_idx, line in enumerate(lines):
                clean_l = line.lower().strip()
                if clean_l in ("contents", "table of contents", "index", "agenda", "syllabus", "course contents") or \
                   re.match(r'^(?:table of contents|contents|index|agenda)\s*$', clean_l):
                    candidates = lines[l_idx + 1:]
                    cands = []
                    for cand in candidates:
                        cand_clean = cand.strip()
                        if len(cand_clean) < 3 or len(cand_clean) > 100:
                            continue
                        if re.match(r'^(?:page\s+\d+|\d+)$', cand_clean.lower()):
                            continue
                        if re.match(r'^(?:unit\s+[ivx\d]+|chapter\s+\d+|class\s+notes)\b', cand_clean.lower()):
                            continue
                        cands.append(cand_clean)
                    if len(cands) >= 3:
                        index_topics = cands
                        index_page_idx = p_idx
                        break
            if index_topics:
                break

        if index_topics:
            search_pages = pages[index_page_idx + 1:] if index_page_idx >= 0 else pages
            for idx, t_name in enumerate(index_topics):
                num_match = re.match(r'^(\d+(?:\.\d+)*)', t_name)
                num_prefix = num_match.group(1) if num_match else ""
                title_part = re.sub(r'^\d+(?:\.\d+)*\s*', '', t_name).strip()
                clean_title = re.sub(r'[^a-z0-9]', '', title_part.lower())
                
                found_page = None
                for sp in search_pages:
                    sp_text = sp.get("text", "")
                    norm_sp = re.sub(r'[^a-z0-9]', '', sp_text.lower())
                    if (num_prefix and num_prefix in sp_text and clean_title[:15] in norm_sp) or (clean_title[:20] in norm_sp):
                        found_page = sp.get("page_number", 1)
                        break
                
                start_p = found_page if found_page else (index_page_idx + 2 + idx)
                topics.append({
                    "name": t_name,
                    "order_index": idx + 1,
                    "source_start": str(start_p),
                    "source_end": str(start_p),
                    "confidence": 1.0,
                    "subtopics": [],
                })
                
            total_p = len(pages)
            for i in range(len(topics)):
                curr_s = int(topics[i]["source_start"])
                if i + 1 < len(topics):
                    next_s = int(topics[i + 1]["source_start"])
                    topics[i]["source_end"] = str(max(curr_s, next_s - 1 if next_s > curr_s else curr_s))
                else:
                    topics[i]["source_end"] = str(total_p)
            return topics

        toc = parsed_doc.get("toc", [])

        # 2. Native TOC (PDF bookmarks)
        if toc:
            current_topic = None
            topic_order = 1
            subtopic_order = 1

            for item in toc:
                lvl, title, page = item[0], item[1].strip(), item[2]
                if lvl == 1:
                    current_topic = {
                        "name": title,
                        "order_index": topic_order,
                        "source_start": str(page),
                        "source_end": str(page),
                        "confidence": 1.0,
                        "subtopics": [],
                    }
                    topics.append(current_topic)
                    topic_order += 1
                    subtopic_order = 1
                elif lvl == 2 and current_topic:
                    clean_t = clean_subtopic_name(title)
                    if clean_t:
                        current_topic["subtopics"].append({
                            "name": clean_t,
                            "order_index": subtopic_order,
                            "source_start": str(page),
                            "source_end": str(page),
                            "confidence": 1.0,
                        })
                        subtopic_order += 1

            if topics:
                return topics

        # 3. Typography & Layout: Check line-by-line typography and numbering
        pages = parsed_doc.get("pages", [])
        topics = []
        current_topic = None
        topic_order = 1
        subtopic_order = 1

        for page in pages:
            page_num = page.get("page_number", 1)
            blocks = page.get("blocks", [])
            for b in blocks:
                if b.get("type") == "TEXT":
                    lines = b.get("lines", [])
                    # If lines weren't parsed separately, fall back to block text
                    if not lines:
                        lines = [{"text": line.strip(), "font_size": b.get("max_font_size", 10), "is_bold": b.get("is_bold", False)} for line in b.get("text", "").split("\n") if line.strip()]

                    for l in lines:
                        line_text = l.get("text", "").strip()
                        if not line_text:
                            continue

                        # Filter out document-level headers like "Unit III", "Chapter 1", "Class Notes"
                        if re.match(r'^(?:unit\s+[ivx\d]+|chapter\s+\d+|class\s+notes|course\s+notes)\b', line_text, re.IGNORECASE):
                            continue

                        font_size = l.get("font_size", 10.0)
                        is_bold = l.get("is_bold", False)
                        is_short = 3 <= len(line_text) <= 80

                        if not is_short:
                            continue

                        # Check for subtopic pattern like "1.1 Computer Basics"
                        sub_match = re.match(r'^\d+\.\d+\s+([A-Z].*)', line_text)
                        
                        # Check for top-level topic pattern like "1. Introduction" or large font >= 16
                        top_match = re.match(r'^(?:\d+\.|\bChapter\s+\d+:?|\bUnit\s+\d+:?)\s+([A-Z].*)', line_text, re.IGNORECASE)
                        is_large_heading = (font_size >= 15.0)

                        if sub_match or (font_size >= 13.0 and font_size < 15.0 and is_bold):
                            # It's a subtopic
                            if current_topic:
                                clean_l = clean_subtopic_name(line_text)
                                if clean_l and not any(s["name"].lower() == clean_l.lower() for s in current_topic["subtopics"]):
                                    current_topic["subtopics"].append({
                                        "name": clean_l,
                                        "order_index": subtopic_order,
                                        "source_start": str(page_num),
                                        "source_end": str(page_num),
                                        "confidence": 0.95,
                                    })
                                    subtopic_order += 1
                            else:
                                current_topic = {
                                    "name": line_text,
                                    "order_index": topic_order,
                                    "source_start": str(page_num),
                                    "source_end": str(page_num),
                                    "confidence": 0.9,
                                    "subtopics": [],
                                }
                                topics.append(current_topic)
                                topic_order += 1
                                subtopic_order = 1

                        elif top_match or is_large_heading:
                            # It's a top-level topic
                            if not any(t["name"].lower() == line_text.lower() for t in topics):
                                current_topic = {
                                    "name": line_text,
                                    "order_index": topic_order,
                                    "source_start": str(page_num),
                                    "source_end": str(page_num),
                                    "confidence": 0.98,
                                    "subtopics": [],
                                }
                                topics.append(current_topic)
                                topic_order += 1
                                subtopic_order = 1

        return topics

    def _extract_numbered_headings(self, source_text: str) -> List[Dict[str, Any]]:
        """Extracts numbered sections like '1. Introduction', '1.1 Basics'."""
        pattern = re.compile(r'^(?:(?:\d+\.){1,2}\d*|\bChapter\s+\d+:?|\bUnit\s+\d+:?)\s+([A-Z][^\n]+)', re.MULTILINE)
        matches = pattern.findall(source_text)
        topics = []
        topic_order = 1
        for match in matches:
            name = match.strip()
            if 3 <= len(name) <= 80 and not any(t["name"].lower() == name.lower() for t in topics):
                topics.append({
                    "name": name,
                    "order_index": topic_order,
                    "source_start": "1",
                    "source_end": "1",
                    "confidence": 0.9,
                    "subtopics": []
                })
                topic_order += 1
        return topics

    def _extract_with_ai(self, source_text: str) -> List[Dict[str, Any]]:
        """Calls AI service with structured JSON prompt and strictly validates output."""
        prompt = STRUCTURE_EXTRACTION_PROMPT.format(source_text=source_text[:8000])
        result = ai_service.generate_json(prompt)
        if not result or "topics" not in result:
            return []

        ai_topics = result.get("topics", [])
        validated_topics = []
        topic_order = 1

        for t in ai_topics:
            name = t.get("name", "").strip()
            if name:
                subtopics = []
                sub_order = 1
                for s in t.get("subtopics", []):
                    s_name = s.get("name", "").strip()
                    if s_name:
                        subtopics.append({
                            "name": s_name,
                            "order_index": sub_order,
                            "source_start": str(s.get("source_reference", "1")),
                            "source_end": str(s.get("source_reference", "1")),
                            "confidence": 0.85,
                        })
                        sub_order += 1

                validated_topics.append({
                    "name": name,
                    "order_index": topic_order,
                    "source_start": str(t.get("source_reference", "1")),
                    "source_end": str(t.get("source_reference", "1")),
                    "confidence": 0.85,
                    "subtopics": subtopics,
                })
                topic_order += 1

        return validated_topics

structure_service = StructureService()
