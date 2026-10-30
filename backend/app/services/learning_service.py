import os
import re
import json
import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import Topic, SourceRegion
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)

def is_presenter_or_admin_line(line: str) -> bool:
    l = line.strip().lower()
    if not l or len(l) < 3:
        return True
    patterns = [
        r'\b(?:dr\.|prof\.|professor|associate\s+professor|assistant\s+professor|lecturer|faculty|dean|hod)\b',
        r'\b(?:department\s+of|dept\.|college\s+of|school\s+of|university|institute|campus)\b',
        r'\b(?:presented\s+by|prepared\s+by|guided\s+by|submitted\s+by|authored\s+by|instructor|tutor)\b',
        r'\b(?:academic\s+year|semester|roll\s+no|reg\s+no|register\s+number)\b',
        r'(?:[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+|\b(?:ph|phone|mobile|tel|contact)\s*[:#.-]?\s*\+?\d[\d\s\-]{6,}\d\b|\b(?:www\.[a-zA-Z0-9-]+\.[a-z]{2,}|https?://[^\s]+|\.edu\b|\.ac\.in\b))',
    ]
    return any(re.search(pat, l) for pat in patterns)


def format_diagram_content_text(text: str) -> str:
    """Format OCR/vision diagram output (HEADING, TEXT, RELATIONSHIPS) into clean study notes."""
    if not text or not ("HEADING:" in text or "TEXT:" in text or "RELATIONSHIPS:" in text):
        return text

    heading = ""
    steps_or_text = ""
    relationships = ""
    other_lines = []
    for part in text.splitlines():
        part_clean = part.strip()
        if part_clean.startswith("HEADING:"):
            heading = part_clean.replace("HEADING:", "").strip()
        elif part_clean.startswith("TEXT:"):
            steps_or_text = part_clean.replace("TEXT:", "").strip()
        elif part_clean.startswith("RELATIONSHIPS:"):
            relationships = part_clean.replace("RELATIONSHIPS:", "").strip()
        elif part_clean:
            other_lines.append(part_clean)

    res_lines = []
    if heading:
        res_lines.append(f"{heading}:")
    if steps_or_text:
        items = [i.strip() for i in re.split(r'[,;]|\s+->\s+', steps_or_text) if i.strip()]
        if len(items) >= 2:
            res_lines.append("Key Steps / Components:")
            for idx, item in enumerate(items, 1):
                res_lines.append(f"{idx}. {item}")
        else:
            res_lines.append(steps_or_text)
    if other_lines:
        res_lines.extend(other_lines)
    if relationships:
        res_lines.append(f"Structure & Flow: {relationships}")
    return "\n".join(res_lines) if res_lines else text


def clean_source_lines(text: str) -> List[str]:
    """Keep educational text while removing parser-only slide metadata."""
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip()
        and not is_presenter_or_admin_line(line)
        and not re.match(r'^title\s*:', line.strip(), re.IGNORECASE)
    ]


LEARNING_CONTENT_PROMPT = """You are an expert pedagogical educator. Extract and organize structured learning content from the provided source material for the topic: "{topic_name}".

CRITICAL INSTRUCTIONS:
1. STRICT SOURCE GROUNDING: Extract ONLY facts, definitions, characteristics, types/classifications, processes, comparisons, advantages, disadvantages, examples, and important points directly present in the source text. Never invent external facts.
2. NO HALLUCINATION OR FILLER: If a category (e.g. processes, classifications, comparisons, advantages) is NOT present in the source text, provide an empty list `[]` for that field. DO NOT invent or assume external details.
3. NO PRESENTER / METADATA EXTRACTION: Ignore presenter names, professors, faculty titles, department headers, and course admin notices. Never treat author names as concepts.
4. ORDERED PROCESSES: If a step-by-step process or sequence is present, outline the ordered steps clearly.
5. NO MIND MAPS OR FLOWCHARTS: Do NOT generate mind maps or flowcharts. Only extract educational content.

Return a valid JSON object matching this schema:
{{
  "summary": "Clear, grounded 2-3 sentence overview of what the topic teaches.",
  "definitions": [
    {{"term": "Term Name", "definition": "Source grounded definition", "source_ref": "Slide/Page reference"}}
  ],
  "core_concepts": [
    {{"concept": "Concept Title", "explanation": "Key conceptual explanation from source", "source_ref": "Slide/Page reference"}}
  ],
  "characteristics": [
    "Key feature or characteristic directly mentioned in the source"
  ],
  "types_and_classifications": [
    {{"category": "Category Name", "items": ["Item A", "Item B"], "description": "Classification criteria from source"}}
  ],
  "processes": [
    {{"process_name": "Process Name", "steps": [{{"step_number": 1, "title": "Step Title", "description": "What occurs in this step"}}]}}
  ],
  "comparisons": [
    {{"aspect": "Comparison Aspect", "item_a": "Item A details", "item_b": "Item B details"}}
  ],
  "advantages": [
    "Advantage or benefit stated in the source"
  ],
  "disadvantages": [
    "Disadvantage or limitation stated in the source"
  ],
  "examples": [
    "Concrete example or application mentioned in the source"
  ],
  "important_points": [
    "Crucial point or takeaway for exam preparation"
  ],
  "keywords": [
    {{"keyword": "Key Term", "explanation": "Brief meaning based strictly on source context"}}
  ]
}}

SOURCE MATERIAL FOR {topic_name}:
\"\"\"
{source_text}
\"\"\"
"""

class LearningService:
    SOURCE_SCHEMA_VERSION = 10

    def get_or_create_learning_data(self, db: Session, topic: Topic) -> Dict[str, Any]:
        """
        Returns structured learning content for a topic:
        Definitions, Core Concepts, Characteristics, Classifications, Processes & Steps,
        Comparisons, Advantages, Disadvantages, Examples, Important Points, Keywords, Visuals, and Practice Cards.
        """
        self._hydrate_topic_image_regions(db, topic)
        cached_sections = (topic.learning_data or {}).get("source_sections", [])
        
        # Detect any duplicate paragraphs in cached sections
        seen_cached = set()
        has_cached_duplicates = False
        for s in cached_sections:
            k = re.sub(r'\s+', ' ', s.get("text", "").lower()).strip()
            if k in seen_cached:
                has_cached_duplicates = True
                break
            seen_cached.add(k)

        cache_is_clean = (
            (topic.learning_data or {}).get("source_schema_version") == self.SOURCE_SCHEMA_VERSION
            and not has_cached_duplicates
            and all(
                not re.match(r'^title\s*:', section.get("text", "").strip(), re.IGNORECASE)
                and not re.search(r'original slide', section.get("source_reference", ""), re.IGNORECASE)
                and not re.search(r'slide\s+\d+\s+element', section.get("source_reference", ""), re.IGNORECASE)
                and (section.get("region_type") != "IMAGE" or len(section.get("text", "").strip()) > 20)
                for section in cached_sections
            )
        )
        if topic.learning_data and "source_sections" in topic.learning_data and cache_is_clean:
            cached = topic.learning_data
            if "mind_map" in cached or "flowchart" in cached:
                cached.pop("mind_map", None)
                cached.pop("flowchart", None)
                try:
                    topic.learning_data = cached
                    db.commit()
                except Exception:
                    pass
            # Extra safety: deduplicate sections and visuals before returning
            deduped_secs = []
            s_set = set()
            for sec in cached.get("source_sections", []):
                sk = re.sub(r'\s+', ' ', sec.get("text", "").lower()).strip()
                if sk and sk not in s_set:
                    s_set.add(sk)
                    deduped_secs.append(sec)
            cached["source_sections"] = deduped_secs

            deduped_vis = []
            v_set = set()
            for v in cached.get("visuals", []):
                vk = v.get("media_path") or v.get("content_html") or v.get("caption")
                if vk and vk not in v_set:
                    v_set.add(vk)
                    deduped_vis.append(v)
            cached["visuals"] = deduped_vis
            return cached

        source_text = self._get_topic_full_text(db, topic)
        visuals = self._get_topic_visuals(db, topic)

        # Always build a deterministic, source-complete baseline. AI output may
        # improve organization, but it must never be allowed to discard facts.
        baseline = self._generate_deterministic_learning_data(topic, source_text, visuals)

        # 1. Try AI extraction if available
        data = None
        if ai_service.is_available() and len(source_text.strip()) > 30:
            try:
                prompt = LEARNING_CONTENT_PROMPT.format(
                    topic_name=topic.name,
                    source_text=source_text[:7000]
                )
                ai_result = ai_service.generate_json(prompt)
                if ai_result and isinstance(ai_result, dict) and ("definitions" in ai_result or "core_concepts" in ai_result):
                    data = self._merge_learning_data(baseline, ai_result)
                    # Ensure legacy fields are removed
                    data.pop("mind_map", None)
                    data.pop("flowchart", None)
            except Exception as e:
                logger.warning(f"AI learning content extraction failed for topic {topic.id}: {e}")

        # 2. Fall back to deterministic pedagogical extraction
        if not data:
            data = baseline

        # Ensure visuals and practice cards are attached
        data["visuals"] = visuals
        data["source_sections"] = self._get_topic_source_sections(db, topic)
        data["source_schema_version"] = self.SOURCE_SCHEMA_VERSION
        if "practice_cards" not in data or not data["practice_cards"]:
            data["practice_cards"] = self._generate_practice_cards(data, topic.name)

        # Cache in database
        try:
            topic.learning_data = data
            db.commit()
            db.refresh(topic)
        except Exception as e:
            logger.warning(f"Failed to persist learning_data for topic {topic.id}: {e}")

        return data

    def _hydrate_topic_image_regions(self, db: Session, topic: Topic) -> None:
        """Read diagram labels as supplemental evidence while keeping images as visuals."""
        if not topic.document:
            return
        from app.config import settings

        if not ai_service.is_available():
            return

        regions = db.query(SourceRegion).filter(
            SourceRegion.topic_id == topic.id,
            SourceRegion.region_type == "IMAGE",
        ).all()
        changed = False
        for region in regions:
            if region.content_text and region.content_text.strip():
                continue
            if not region.media_path:
                continue
            filename = region.media_path.rsplit("/", 1)[-1]
            image_path = os.path.join(settings.EXTRACTED_MEDIA_DIR, topic.document_id, filename)
            if not os.path.exists(image_path):
                continue
            extracted = ai_service.extract_image_content(image_path).get("content", "").strip()
            if extracted:
                region.content_text = extracted
                changed = True
        if changed:
            db.commit()

    def _merge_learning_data(self, baseline: Dict[str, Any], generated: Dict[str, Any]) -> Dict[str, Any]:
        """Keep every non-empty source-derived baseline field when AI omits it."""
        merged = dict(baseline)
        for key, value in generated.items():
            if value not in (None, "", []):
                merged[key] = value
        return merged

    def _get_topic_full_text(self, db: Session, topic: Topic) -> str:
        regions = db.query(SourceRegion).filter(
            SourceRegion.topic_id == topic.id
        ).order_by(SourceRegion.element_order).all()

        # Check if native slide or text regions contain substantial text
        primary_regions = [
            r for r in regions
            if r.region_type in ("SLIDE", "TEXT", "PARAGRAPH") and r.content_text and len(r.content_text.strip()) > 10
        ]
        slide_regions = [r for r in primary_regions if r.region_type == "SLIDE"]
        if slide_regions:
            selected_regions = slide_regions
        elif primary_regions:
            selected_regions = primary_regions
        else:
            # Fallback to IMAGE / DIAGRAM / TABLE regions with OCR/transcribed text
            selected_regions = [
                r for r in regions
                if r.region_type not in ("FULL_PAGE", "SLIDE") and r.content_text and r.content_text.strip()
            ]

        text_pieces = []
        seen_texts = set()
        for r in selected_regions:
            if r.content_text and r.content_text.strip():
                formatted_text = format_diagram_content_text(r.content_text)
                clean_lines = clean_source_lines(formatted_text)
                if clean_lines:
                    full_clean = "\n".join(clean_lines)
                    norm_key = re.sub(r'\s+', ' ', full_clean.lower()).strip()
                    if norm_key and norm_key not in seen_texts:
                        seen_texts.add(norm_key)
                        ref = r.source_reference or f"Section {r.element_order}"
                        text_pieces.append(f"[{ref}]\n" + full_clean)

        # If still empty, construct from visual diagrams
        if not text_pieces:
            visuals = self._get_topic_visuals(db, topic)
            for v in visuals:
                cap = v.get("caption") or f"{topic.name} Diagram"
                if cap and cap not in seen_texts:
                    seen_texts.add(cap)
                    text_pieces.append(f"[{topic.name} Diagram]\n{cap}\nThis topic is primarily illustrated through visual schematics and diagrams detailing its core concepts and workflows.")

        return "\n\n".join(text_pieces)

    def _get_topic_source_sections(self, db: Session, topic: Topic) -> List[Dict[str, Any]]:
        """Return the complete, traceable source text collected for this topic, deduplicated."""
        regions = db.query(SourceRegion).filter(
            SourceRegion.topic_id == topic.id
        ).order_by(SourceRegion.element_order).all()

        primary_regions = [
            r for r in regions
            if r.region_type in ("SLIDE", "TEXT", "PARAGRAPH") and r.content_text and len(r.content_text.strip()) > 10
        ]
        slide_regions = [r for r in primary_regions if r.region_type == "SLIDE"]
        if slide_regions:
            target_regions = slide_regions
        elif primary_regions:
            target_regions = primary_regions
        else:
            # Fallback to IMAGE / DIAGRAM / TABLE regions with transcribed text
            target_regions = [
                r for r in regions
                if r.region_type not in ("FULL_PAGE", "SLIDE") and r.content_text and r.content_text.strip()
            ]

        sections = []
        seen_texts = set()
        for region in target_regions:
            if not region.content_text or not region.content_text.strip():
                continue
            formatted_text = format_diagram_content_text(region.content_text)
            lines = clean_source_lines(formatted_text)
            if not lines:
                continue

            full_clean = "\n".join(lines)
            norm_key = re.sub(r'\s+', ' ', full_clean.lower()).strip()
            if not norm_key or norm_key in seen_texts:
                continue
            seen_texts.add(norm_key)

            clean_ref = re.sub(r'^slide\s+\d+\s+element\b', '', region.source_reference or "", flags=re.IGNORECASE).strip() or topic.name
            sections.append({
                "source_reference": clean_ref,
                "page_number": region.page_number,
                "slide_number": region.slide_number,
                "region_type": region.region_type,
                "text": full_clean,
            })

        # If sections is still empty, create placeholder sections from visuals so that
        # diagrams are inlined and students have study notes.
        if not sections:
            visuals = self._get_topic_visuals(db, topic)
            for v in visuals:
                cap = v.get("caption") or f"{topic.name} Diagram"
                sections.append({
                    "source_reference": cap,
                    "page_number": v.get("page_number"),
                    "slide_number": v.get("slide_number"),
                    "region_type": v.get("type", "IMAGE"),
                    "text": f"{topic.name}:\n{cap}\nRefer to the diagram for the visual framework, sequence, and key relationships.",
                })

        return sections

    def _get_topic_visuals(self, db: Session, topic: Topic) -> List[Dict[str, Any]]:
        regions = db.query(SourceRegion).filter(
            SourceRegion.topic_id == topic.id
        ).order_by(SourceRegion.element_order).all()

        visuals = []
        seen_visuals = set()
        for r in regions:
            if r.region_type in ("IMAGE", "TABLE", "DIAGRAM", "FLOWCHART") and (r.media_path or r.content_html):
                dedup_key = r.media_path or r.content_html
                image_path = None
                if r.media_path:
                    try:
                        from app.config import settings
                        import hashlib
                        filename = r.media_path.rsplit("/", 1)[-1]
                        image_path = os.path.join(settings.EXTRACTED_MEDIA_DIR, topic.document_id, filename)
                        if os.path.exists(image_path):
                            with open(image_path, "rb") as f:
                                dedup_key = hashlib.md5(f.read()).hexdigest()
                    except Exception:
                        dedup_key = r.media_path

                if dedup_key in seen_visuals:
                    continue
                seen_visuals.add(dedup_key)

                # DIAGRAM vs TEXT SLIDE check:
                # If region_type is IMAGE, verify whether it contains an authentic visual diagram,
                # chart, or schematic. If it is purely a text slide / bullet points list, skip it!
                caption = r.source_reference if (r.source_reference and not r.source_reference.startswith("Page ")) else f"{topic.name} Diagram"
                final_media_path = r.media_path
                if r.region_type == "IMAGE" and image_path and os.path.exists(image_path):
                    has_figure_caption = bool(re.search(r'Figure\s+\d', r.source_reference or "", re.IGNORECASE))
                    if has_figure_caption:
                        caption = r.source_reference
                    else:
                        classification = ai_service.classify_and_caption_image(image_path)
                        if not classification.get("is_diagram", False):
                            # Skip pure text slides so they are not shown as diagrams
                            continue
                        if classification.get("caption"):
                            caption = classification["caption"]
                        if classification.get("cropped_filename") and r.media_path:
                            prefix = r.media_path.rsplit("/", 1)[0]
                            final_media_path = f"{prefix}/{classification['cropped_filename']}"
                elif r.region_type != "IMAGE":
                    caption = f"{topic.name} {r.region_type.capitalize()}"

                visuals.append({
                    "id": r.id,
                    "type": r.region_type,
                    "media_path": final_media_path,
                    "content_html": r.content_html,
                    "caption": caption,
                    "source_reference": topic.name,
                    "slide_number": r.slide_number,
                    "page_number": r.page_number,
                })
        return visuals

    def _generate_deterministic_learning_data(
        self, topic: Topic, source_text: str, visuals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Pedagogical rule-based extractor strictly grounded in source text."""
        topic_name = topic.name
        raw_lines = [line.strip() for line in source_text.splitlines() if len(line.strip()) > 3]
        # Filter presenter / admin boilerplate completely
        lines = [l for l in raw_lines if not is_presenter_or_admin_line(l) and not (l.startswith("[") and l.endswith("]"))]

        definitions: List[Dict[str, Any]] = []
        core_concepts: List[Dict[str, Any]] = []
        characteristics: List[str] = []
        types_and_classifications: List[Dict[str, Any]] = []
        processes: List[Dict[str, Any]] = []
        comparisons: List[Dict[str, Any]] = []
        advantages: List[str] = []
        disadvantages: List[str] = []
        examples: List[str] = []
        important_points: List[str] = []
        keywords: List[Dict[str, Any]] = []

        # Find definitions (pattern: X is defined as... / X is a... / X refers to...)
        def_pattern = re.compile(
            r'^([A-Z][a-zA-Z0-9\s\-/]{2,40}?)\s+(is defined as|is an?|are an?|refers to|denotes|means)\s+(.+)$',
            re.IGNORECASE
        )
        # Term: Definition pattern
        term_colon_pattern = re.compile(
            r'^([A-Z][a-zA-Z0-9\s\-/]{2,35}):\s+(.+)$'
        )

        process_steps = []

        for line in lines:
            # Category labels such as "Advantage:" are educational fields,
            # not term definitions. Classify them before the generic colon rule.
            label_match = re.match(r'^([^:]{2,40}):\s*(.+)$', line)
            label = label_match.group(1).strip().lower() if label_match else ""
            label_value = label_match.group(2).strip() if label_match else ""
            if label_match and label in {"advantage", "benefit", "merit", "strength", "pros"}:
                if label_value and label_value not in advantages:
                    advantages.append(label_value)
                continue
            if label_match and label in {"disadvantage", "limitation", "demerit", "drawback", "cons"}:
                if label_value and label_value not in disadvantages:
                    disadvantages.append(label_value)
                continue
            if label_match and any(k in label for k in ("characteristic", "feature", "property", "attribute")):
                if label_value and label_value not in characteristics:
                    characteristics.append(label_value)
                continue

            # Check for definition pattern
            m_def = def_pattern.match(line)
            if m_def:
                term = m_def.group(1).strip()
                defi = f"{m_def.group(2).capitalize()} {m_def.group(3).strip()}"
                if not any(d["term"].lower() == term.lower() for d in definitions):
                    definitions.append({
                        "term": term,
                        "definition": defi,
                        "source_ref": topic.name
                    })
                    keywords.append({"keyword": term, "explanation": defi, "source_reference": topic.name})
                continue

            m_colon = term_colon_pattern.match(line)
            if m_colon:
                term = m_colon.group(1).strip()
                defi = m_colon.group(2).strip()
                if len(defi) >= 15 and not any(d["term"].lower() == term.lower() for d in definitions):
                    definitions.append({
                        "term": term,
                        "definition": defi,
                        "source_ref": topic.name
                    })
                    keywords.append({"keyword": term, "explanation": defi, "source_reference": topic.name})
                continue

            # Check for advantages / benefits
            if any(k in line.lower() for k in ("advantage", "benefit", "merit", "strength", "pros")):
                clean_adv = line.lstrip("•-* 1234567890.)").strip()
                if len(clean_adv) >= 10 and clean_adv not in advantages:
                    advantages.append(clean_adv)
                continue

            # Check for disadvantages / limitations
            if any(k in line.lower() for k in ("disadvantage", "limitation", "demerit", "drawback", "cons")):
                clean_dis = line.lstrip("•-* 1234567890.)").strip()
                if len(clean_dis) >= 10 and clean_dis not in disadvantages:
                    disadvantages.append(clean_dis)
                continue

            # Check for examples / applications
            if any(k in line.lower() for k in ("example", "e.g.", "such as", "for instance", "application")):
                clean_ex = line.lstrip("•-* 1234567890.)").strip()
                if len(clean_ex) >= 10 and clean_ex not in examples:
                    examples.append(clean_ex)
                continue

            # Check for steps/process
            step_match = re.match(r'^(?:Step\s*\d+:?|\d+\.|\bStage\s*\d+:?)\s*(.+)$', line, re.IGNORECASE)
            if step_match:
                process_steps.append(step_match.group(1).strip())
                continue

            # Check for characteristics / features
            if any(k in line.lower() for k in ("characteristic", "feature", "property", "attribute")):
                clean_char = line.lstrip("•-* 1234567890.)").strip()
                if 10 <= len(clean_char) <= 160 and clean_char not in characteristics:
                    characteristics.append(clean_char)
                continue

            # Check for classifications / types
            if any(k in line.lower() for k in ("types of", "classification of", "categories of", "modes of", "types:", "classification:")):
                types_and_classifications.append({
                    "category": line.lstrip("•-* ").strip(),
                    "items": [],
                    "description": f"Classification identified in {topic_name}"
                })
                continue

            # Ignore structural labels when collecting educational statements
            if line.lower().startswith("key steps") or line.lower().startswith("structure & flow"):
                if line.lower().startswith("structure & flow"):
                    structure_desc = line.split(":", 1)[-1].strip()
                    if structure_desc and structure_desc not in important_points:
                        important_points.append(structure_desc)
                continue

            # Core educational statements
            clean_stmt = re.sub(r'[*#_`]', '', line).strip()
            if 20 <= len(clean_stmt) <= 220:
                if len(core_concepts) < 5 and clean_stmt not in [c.get("explanation") for c in core_concepts]:
                    core_concepts.append({
                        "concept": clean_stmt.split(".")[0][:50],
                        "explanation": clean_stmt,
                        "source_ref": topic.name
                    })
                elif len(important_points) < 6 and clean_stmt not in important_points:
                    important_points.append(clean_stmt)

        # Assemble processes if steps were detected
        if len(process_steps) >= 2:
            formatted_steps = [
                {"step_number": idx + 1, "title": s[:50], "description": s}
                for idx, s in enumerate(process_steps)
            ]
            processes.append({
                "process_name": f"Steps in {topic_name}",
                "steps": formatted_steps
            })
            if not core_concepts:
                for s in formatted_steps[:5]:
                    core_concepts.append({
                        "concept": s["title"],
                        "explanation": f"Key phase in {topic_name}: {s['description']}",
                        "source_ref": topic.name
                    })

        # Summary derived from processes, core concepts, or visual diagrams
        summary = ""
        if processes:
            p = processes[0]
            step_names = [s.get("title", "") for s in p.get("steps", [])[:5]]
            summary = f"{topic_name} is a structured managerial workflow comprising {len(p.get('steps', []))} sequential phases: {', '.join(step_names)}."
        elif core_concepts:
            summary = " ".join([c["explanation"] for c in core_concepts[:2]])
        elif important_points:
            summary = " ".join(important_points[:2])
        elif definitions:
            summary = f"{definitions[0]['term']}: {definitions[0]['definition']}"
        elif visuals:
            summary = f"{topic_name} is illustrated by key visual schematics and diagrams detailing its core concepts and workflows."
        else:
            summary = ""

        # Prioritize process steps in keywords for diagram/workflow topics
        if processes:
            for p in processes:
                for s in p.get("steps", []):
                    if not any(k["keyword"].lower() == s["title"].lower() for k in keywords):
                        keywords.append({
                            "keyword": s["title"],
                            "explanation": f"Key operational step in {topic_name}: {s['description']}",
                            "source_reference": topic.name
                        })

        # Keywords if not populated from definitions or processes
        if not keywords:
            for c in core_concepts[:6]:
                keywords.append({
                    "keyword": c["concept"],
                    "explanation": c["explanation"],
                    "source_reference": topic.name
                })
        if not keywords and visuals:
            for v in visuals:
                cap = v.get("caption") or ""
                if cap and not any(k["keyword"].lower() == cap.lower() for k in keywords):
                    keywords.append({
                        "keyword": cap,
                        "explanation": f"Visual framework established for {topic_name}",
                        "source_reference": topic.name
                    })

        return {
            "summary": summary,
            "definitions": definitions,
            "core_concepts": core_concepts,
            "characteristics": characteristics,
            "types_and_classifications": types_and_classifications,
            "classifications": types_and_classifications,
            "processes": processes,
            "comparisons": comparisons,
            "advantages": advantages,
            "disadvantages": disadvantages,
            "examples": examples,
            "important_points": important_points,
            "keywords": keywords,
        }

    def _generate_practice_cards(self, data: Dict[str, Any], topic_name: str) -> List[Dict[str, str]]:
        cards = []
        for d in data.get("definitions", []):
            term = d.get("term", "")
            definition = d.get("definition", "")
            if term and definition:
                cards.append({
                    "front": f"What is the definition of '{term}'?",
                    "back": definition,
                    "question": f"What is the definition of '{term}'?",
                    "answer": definition,
                    "concept": term,
                    "concept_area": term,
                })
        for c in data.get("core_concepts", []):
            c_title = c.get("concept") or c.get("title") or "Core Principle"
            c_desc = c.get("explanation") or c.get("description") or ""
            if c_desc:
                cards.append({
                    "front": f"Explain the principle: '{c_title}'",
                    "back": c_desc,
                    "question": f"Explain the principle: '{c_title}'",
                    "answer": c_desc,
                    "concept": c_title,
                    "concept_area": c_title,
                })
        for p in data.get("processes", []):
            p_name = p.get("process_name") or p.get("name") or "Workflow"
            steps = p.get("steps")
            if steps:
                if isinstance(steps, list):
                    if len(steps) > 0 and isinstance(steps[0], dict):
                        steps_str = " → ".join([s.get("title") or s.get("description") or f"Step {i+1}" for i, s in enumerate(steps)])
                    else:
                        steps_str = " → ".join([str(s) for s in steps])
                else:
                    steps_str = str(steps)
                cards.append({
                    "front": f"What are the sequential steps in {p_name}?",
                    "back": steps_str,
                    "question": f"What are the sequential steps in {p_name}?",
                    "answer": steps_str,
                    "concept": p_name,
                    "concept_area": p_name,
                })
        for adv in data.get("advantages", []):
            adv_text = adv if isinstance(adv, str) else adv.get("point", "")
            if adv_text:
                cards.append({
                    "front": f"What is a key advantage of {topic_name}?",
                    "back": adv_text,
                    "question": f"What is a key advantage of {topic_name}?",
                    "answer": adv_text,
                    "concept": f"{topic_name} Advantages",
                    "concept_area": "Advantages",
                })
        if not cards and data.get("summary"):
            cards.append({
                "front": f"What is the core focus of {topic_name}?",
                "back": data["summary"],
                "question": f"What is the core focus of {topic_name}?",
                "answer": data["summary"],
                "concept": topic_name,
                "concept_area": topic_name,
            })
        return cards

learning_service = LearningService()
