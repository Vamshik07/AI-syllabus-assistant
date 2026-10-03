import re
import logging
from typing import Dict, List, Any, Tuple
from app.services.ai_service import ai_service
from app.services.validation_service import validation_service
from app.services.prompts.structure_prompt import STRUCTURE_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)

class StructureService:
    def extract_structure(self, file_type: str, parsed_doc: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str]:
        """
        Extracts topics and subtopics following strict deterministic priority:
        1. Native/explicit headings
        2. Numbered headings
        3. Table of contents
        4. Typography & layout information
        5. AI assistance only if needed
        Returns (topics_list, status) where status is 'EXTRACTED', 'VERIFIED', or 'REVIEW_REQUIRED'.
        """
        topics = []
        file_type = file_type.upper()
        source_text = parsed_doc.get("full_text", "")

        if file_type == "DOCX":
            topics = self._extract_docx_structure(parsed_doc)
        elif file_type == "PPTX":
            topics = self._extract_pptx_structure(parsed_doc)
        elif file_type == "PDF":
            topics = self._extract_pdf_structure(parsed_doc)

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

        # Run programmatic source validation
        is_valid, errors = validation_service.validate_structure(topics, source_text)
        if not is_valid:
            logger.warning(f"Structure validation failed: {errors}. Setting status to REVIEW_REQUIRED.")
            return topics, "REVIEW_REQUIRED"

        return topics, "VERIFIED"

    def _extract_docx_structure(self, parsed_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extracts topics from DOCX using native Heading 1 and Heading 2 styles."""
        elements = parsed_doc.get("elements", [])
        topics = []
        current_topic = None
        topic_order = 1
        subtopic_order = 1

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

                subtopic = {
                    "name": text,
                    "order_index": subtopic_order,
                    "source_start": f"Element {el.get('element_order')}",
                    "source_end": f"Element {el.get('element_order')}",
                    "confidence": 1.0,
                }
                current_topic["subtopics"].append(subtopic)
                subtopic_order += 1

        return topics

    def _extract_pptx_structure(self, parsed_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extracts topics and subtopics from PPTX preserving slide order and pedagogical hierarchy:
        1. Detects an index/agenda slide at the beginning and records it separately from topics.
        2. If an index is present, aligns subsequent slides to its entries.
        3. Groups continuation slides without titles into the active topic (expanding source_start/source_end).
        4. Never names a topic 'Slide N'.
        """
        slides = parsed_doc.get("slides", [])
        if not slides:
            return []

        def normalize(t: str) -> str:
            return re.sub(r'[^a-z0-9]', '', t.lower())

        def slide_lines(slide: Dict[str, Any]) -> List[str]:
            return [
                line.strip()
                for line in slide.get("text", "").splitlines()
                if len(line.strip()) > 3 and not line.strip().startswith("---")
            ]

        def clean_index_entry(value: str) -> str:
            return re.sub(
                r'^(?:\d+[\.\)]|[ivxlcdm]+[\.\)]|\*|-|\u2022)\s*',
                '',
                value,
                flags=re.IGNORECASE,
            ).strip()

        def is_index_slide(slide: Dict[str, Any]) -> bool:
            title = slide.get("title", "").strip().lower()
            lines = slide_lines(slide)
            title_is_index = any(
                keyword in title
                for keyword in (
                    "index",
                    "contents",
                    "table of contents",
                    "syllabus",
                    "agenda",
                    "overview",
                )
            )
            entries = [clean_index_entry(line) for line in lines[1:]]
            entries = [entry for entry in entries if 3 < len(entry) < 100]
            # Some teaching decks use the unit title as the heading for an index.
            # A dense list of short lines is the reliable signal in that layout.
            dense_list = len(entries) >= 4 and len(entries) / max(len(lines) - 1, 1) >= 0.7
            return title_is_index or dense_list

        # Check if slide 1 or 2 is an index / agenda / syllabus slide.
        agenda_topics = []
        agenda_slide_idx = -1

        for idx, slide in enumerate(slides[:2]):
            lines = slide_lines(slide)
            if len(lines) >= 4:
                first_line = lines[0].lower()
                is_agenda = is_index_slide(slide) or any(
                    kw in first_line
                    for kw in ["syllabus", "agenda", "content", "overview", "unit", "planning"]
                )
                candidates = lines[1:] if is_agenda else lines
                cleaned_cands = []
                for c in candidates:
                    clean = clean_index_entry(c)
                    if clean and len(clean) > 3 and len(clean) < 100:
                        cleaned_cands.append(clean)
                if len(cleaned_cands) >= 3:
                    agenda_topics = cleaned_cands
                    agenda_slide_idx = idx
                    break

        if agenda_slide_idx >= 0:
            index_slide = slides[agenda_slide_idx]
            parsed_doc["index"] = {
                "slide_number": index_slide.get("slide_number", agenda_slide_idx + 1),
                "title": index_slide.get("title", "").strip() or "Index",
                "entries": agenda_topics,
            }

        topics = []

        if agenda_topics:
            curr_syl_idx = 0
            subtopic_order = 1
            for slide in slides[agenda_slide_idx + 1:]:
                s_num = slide.get("slide_number", 1)
                s_title = slide.get("title", "").strip()
                norm_s = normalize(s_title) if s_title else ""

                matched_idx = None
                if norm_s:
                    best_match_score = 0
                    for k in range(curr_syl_idx, len(agenda_topics)):
                        syl_words = [w for w in re.findall(r'[a-z0-9]{4,}', agenda_topics[k].lower())]
                        matches = sum(1 for w in syl_words if w in norm_s) if syl_words else 0
                        normalized_syllabus = normalize(agenda_topics[k])
                        if normalized_syllabus == norm_s:
                            matched_idx = k
                            best_match_score = len(syl_words) + 100
                            break
                        if normalized_syllabus in norm_s or norm_s in normalized_syllabus:
                            matches += 2
                        if matches > best_match_score:
                            matched_idx = k
                            best_match_score = matches

                if matched_idx is not None and (not topics or topics[-1]["name"] != agenda_topics[matched_idx]):
                    curr_syl_idx = matched_idx
                    subtopic_order = 1
                    t = {
                        "name": agenda_topics[matched_idx],
                        "order_index": len(topics) + 1,
                        "source_start": str(s_num),
                        "source_end": str(s_num),
                        "confidence": 1.0,
                        "subtopics": [],
                    }
                    if s_title and normalize(s_title) != normalize(agenda_topics[matched_idx]):
                        t["subtopics"].append({
                            "name": s_title,
                            "order_index": subtopic_order,
                            "source_start": str(s_num),
                            "source_end": str(s_num),
                            "confidence": 1.0,
                        })
                        subtopic_order += 1
                    topics.append(t)
                else:
                    if topics:
                        topics[-1]["source_end"] = str(s_num)
                        if s_title and s_title != topics[-1]["name"]:
                            existing_sub_names = [normalize(st["name"]) for st in topics[-1]["subtopics"]]
                            if normalize(s_title) not in existing_sub_names:
                                topics[-1]["subtopics"].append({
                                    "name": s_title,
                                    "order_index": subtopic_order,
                                    "source_start": str(s_num),
                                    "source_end": str(s_num),
                                    "confidence": 1.0,
                                })
                                subtopic_order += 1
                    else:
                        title_fallback = s_title or "Introduction"
                        topics.append({
                            "name": title_fallback,
                            "order_index": 1,
                            "source_start": str(s_num),
                            "source_end": str(s_num),
                            "confidence": 1.0,
                            "subtopics": [],
                        })
            return topics

        # General PPTX fallback (when no agenda slide is present)
        topic_order = 1
        for slide in slides:
            if is_index_slide(slide):
                parsed_doc.setdefault("index", {
                    "slide_number": slide.get("slide_number", topic_order),
                    "title": slide.get("title", "").strip() or "Index",
                    "entries": [
                        clean_index_entry(line)
                        for line in slide_lines(slide)[1:]
                        if 3 < len(clean_index_entry(line)) < 100
                    ],
                })
                continue

            title = slide.get("title", "").strip()
            slide_num = slide.get("slide_number", topic_order)

            if not title:
                if topics:
                    topics[-1]["source_end"] = str(slide_num)
                    continue
                else:
                    title = "Unit Overview"

            if topics and normalize(topics[-1]["name"]) == normalize(title):
                topics[-1]["source_end"] = str(slide_num)
                continue

            topics.append({
                "name": title,
                "order_index": topic_order,
                "source_start": str(slide_num),
                "source_end": str(slide_num),
                "confidence": 1.0,
                "subtopics": [],
            })
            topic_order += 1

        return topics

    def _extract_pdf_structure(self, parsed_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extracts structure from PDF:
        First checks native TOC, then typography/layout (large bold headings), then numbered headings.
        """
        toc = parsed_doc.get("toc", [])
        topics = []

        # 1. Native TOC
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
                    current_topic["subtopics"].append({
                        "name": title,
                        "order_index": subtopic_order,
                        "source_start": str(page),
                        "source_end": str(page),
                        "confidence": 1.0,
                    })
                    subtopic_order += 1

            if topics:
                return topics

        # 2. Typography & Layout: Check line-by-line typography and numbering
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
                                if not any(s["name"].lower() == line_text.lower() for s in current_topic["subtopics"]):
                                    current_topic["subtopics"].append({
                                        "name": line_text,
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
