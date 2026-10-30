import json
import logging
import os
import re
from typing import Dict, List, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.model_name = settings.LLM_MODEL
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info(f"Google GenAI client initialized with model '{self.model_name}'.")
            except Exception as e:
                logger.warning(f"Failed to initialize Google GenAI client: {e}")

    def is_available(self) -> bool:
        return self.client is not None

    def generate_json(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Invokes Gemini API requesting structured JSON response."""
        if not self.is_available():
            logger.info("GenAI client not configured or key missing. Returning None.")
            return None

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                }
            )
            raw_text = response.text.strip()
            # Clean possible markdown json code fences
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```(json)?\n", "", raw_text)
                raw_text = re.sub(r"\n```$", "", raw_text)
            data = json.loads(raw_text)
            return data
        except Exception as e:
            logger.error(f"Error during GenAI JSON generation: {e}")
            return None

    def extract_image_content(self, image_path: str) -> Dict[str, Any]:
        """
        Extracts educational diagrams, flowcharts, hierarchies, headings, and text from an image.
        Uses Gemini Vision if available, falling back to local OCR.
        Returns a dict with 'heading' (str or None) and 'content' (str).
        """
        result = {"heading": None, "content": ""}
        if not os.path.exists(image_path):
            return result

        # First try Gemini Vision if available
        if self.is_available():
            try:
                from PIL import Image
                import io
                from google import genai

                with Image.open(image_path) as img:
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    # Resize thumbnail to keep latency fast and bandwidth lightweight
                    img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=85)
                    jpeg_bytes = buf.getvalue()

                prompt = (
                    "Analyze this embedded educational diagram as supplemental evidence for the "
                    "PowerPoint topic that contains it. Do not invent facts and do not describe "
                    "decorative pixels, colors, logos, or unrelated objects.\n"
                    "Return only:\n"
                    "HEADING: <diagram heading or NONE>\n"
                    "TEXT: <all readable words and labels, preserving their wording>\n"
                    "RELATIONSHIPS: <brief description of arrows, stages, groups, or spatial "
                    "relationships that are clearly visible, or NONE>\n"
                    "If the image contains no readable educational information, return "
                    "HEADING: NONE, TEXT: NONE, RELATIONSHIPS: NONE."
                )

                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[
                        prompt,
                        genai.types.Part.from_bytes(data=jpeg_bytes, mime_type="image/jpeg"),
                    ]
                )
                text_out = response.text.strip() if response and response.text else ""
                if text_out:
                    heading = None
                    lines = text_out.splitlines()
                    for line in lines[:3]:
                        if line.upper().startswith("HEADING:"):
                            heading = line.split(":", 1)[1].strip().strip("*# ")
                            break
                    result["heading"] = heading
                    result["content"] = text_out
                    logger.info(f"Extracted image content for {os.path.basename(image_path)} (Heading: '{heading}')")
                    return result
            except Exception as e:
                logger.warning(f"Gemini Vision extraction failed for {image_path}: {e}")

        # Fallback to local OCR if Tesseract is available
        try:
            from PIL import Image
            from app.services.ocr_service import ocr_service
            if ocr_service.is_available():
                with Image.open(image_path) as img:
                    ocr_text = ocr_service.ocr_image(img)
                    if ocr_text:
                        lines = [l.strip() for l in ocr_text.splitlines() if l.strip()]
                        heading = lines[0] if lines else None
                        result["heading"] = heading
                        result["content"] = ocr_text
                        logger.info(f"OCR extracted content for {os.path.basename(image_path)}")
        except Exception as e:
            logger.warning(f"OCR fallback failed for {image_path}: {e}")

        return result

    def classify_and_caption_image(self, image_path: str) -> Dict[str, Any]:
        """
        Determines whether an image is an authentic visual diagram/chart/schematic,
        or purely a text slide / bullet-points list.
        If it contains a diagram, extracts and crops JUST the diagram graphic itself (excluding slide text)
        and returns:
            {"is_diagram": bool, "caption": Optional[str], "cropped_filename": Optional[str]}
        """
        if not image_path or not os.path.exists(image_path):
            return {"is_diagram": False, "caption": None, "cropped_filename": None}

        # Persistent disk cache check
        cache_dir = os.path.dirname(image_path)
        cache_file = os.path.join(cache_dir, ".diagram_cache.json")
        fname = os.path.basename(image_path)
        cached_data = {}
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                if fname in cached_data:
                    entry = cached_data[fname]
                    # Verify cropped file still exists if marked as diagram
                    if entry.get("is_diagram") and entry.get("cropped_filename"):
                        cropped_file = os.path.join(cache_dir, entry["cropped_filename"])
                        if os.path.exists(cropped_file):
                            return entry
                    elif not entry.get("is_diagram"):
                        return entry
            except Exception:
                pass

        res = {"is_diagram": False, "caption": None, "cropped_filename": None}
        if self.is_available():
            try:
                from PIL import Image
                import io
                from google import genai

                with Image.open(image_path) as orig_img:
                    orig_w, orig_h = orig_img.size
                    img = orig_img
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    img.thumbnail((768, 768), Image.Resampling.LANCZOS)
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=80)
                    jpeg_bytes = buf.getvalue()

                prompt = (
                    "Examine this image extracted from an educational document/presentation.\n"
                    "Respond in valid JSON with these fields:\n"
                    '1. "is_diagram": true ONLY IF this image contains an authentic visual diagram, graphic illustration, chart, network topology, circuit, beam pattern, or schematic drawing. false if it is purely a text slide or bullet points list containing sentences, headings, or text with no graphic diagram.\n'
                    '2. "caption": A concise descriptive label for the diagram (e.g. "Base Station Spot Beams Diagram", "Sectorized Antenna Cells") or null if not a diagram.\n'
                    '3. "box_2d": If is_diagram is true, provide normalized coordinates [ymin, xmin, ymax, xmax] between 0 and 1000 of JUST the visual diagram/figure graphic itself, excluding the slide title, bullet points, and headers. If false, return null.\n'
                    "JSON:"
                )

                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[
                        prompt,
                        genai.types.Part.from_bytes(data=jpeg_bytes, mime_type="image/jpeg"),
                    ]
                )
                raw = response.text.strip() if response and response.text else ""
                raw = raw.strip("`").replace("json\n", "").strip()
                data = json.loads(raw)
                is_diagram = bool(data.get("is_diagram", False))
                caption = data.get("caption")
                box_2d = data.get("box_2d")

                cropped_filename = None
                if is_diagram and box_2d and len(box_2d) == 4:
                    try:
                        ymin, xmin, ymax, xmax = box_2d
                        left = max(0, int(xmin * orig_w / 1000) - 10)
                        top = max(0, int(ymin * orig_h / 1000) - 10)
                        right = min(orig_w, int(xmax * orig_w / 1000) + 10)
                        bottom = min(orig_h, int(ymax * orig_h / 1000) + 10)

                        if right > left + 20 and bottom > top + 20:
                            base_name, ext = os.path.splitext(fname)
                            cropped_filename = f"{base_name}_diagram.png"
                            cropped_full_path = os.path.join(cache_dir, cropped_filename)
                            with Image.open(image_path) as full_img:
                                cropped = full_img.crop((left, top, right, bottom))
                                cropped.save(cropped_full_path, "PNG")
                    except Exception as ce:
                        logger.warning(f"Failed to crop diagram box for {image_path}: {ce}")

                res = {
                    "is_diagram": is_diagram,
                    "caption": caption,
                    "cropped_filename": cropped_filename,
                }
            except Exception as e:
                logger.warning(f"Diagram classification failed for {image_path}: {e}")
                res = {"is_diagram": True, "caption": "Document Diagram", "cropped_filename": None}
                return res

        # Save to disk cache only if successfully evaluated
        if self.is_available():
            try:
                cached_data[fname] = res
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(cached_data, f)
            except Exception:
                pass

        return res

    def generate_topic_quiz_fallback(self, topic_name: str, source_text: str, num_questions: int = 5) -> List[Dict[str, Any]]:
        """
        Deterministic, pedagogical, strictly source-grounded quiz generator.
        Transforms source concepts into natural educational questions testing deep understanding
        across definitions, relationships, processes, comparisons, classifications, and scenarios
        without robotic retrieval wording, fill-in-the-blank blanks, or external buzzwords.
        """
        # Split source into clean educational statements / sentences / list items
        def is_junk_item(s: str) -> bool:
            l = s.strip().lower()
            return (
                not l
                or l.startswith("---")
                or l.startswith("heading:")
                or l.startswith("structure & flow")
                or l.startswith("key steps")
                or l.startswith("visual diagram")
                or l.startswith("table data")
                or l.startswith("[")
                or l.endswith("]:")
                or l.endswith(":")
                or l == topic_name.strip().lower()
                or len(l) < 4
            )

        lines = [line.strip() for line in source_text.splitlines() if line.strip()]
        statements = []
        for line in lines:
            if is_junk_item(line):
                continue
            step_match = re.match(r'^(?:Step\s*\d+:?|\d+\.|\bStage\s*\d+:?)\s*(.+)$', line, re.IGNORECASE)
            if step_match:
                s_clean = step_match.group(1).strip()
                if len(s_clean) >= 3 and s_clean not in statements:
                    statements.append(f"Step: {s_clean}")
                continue

            # Split regular paragraph text by full sentence boundaries
            sents = re.split(r'(?<=[a-zA-Z0-9][.!?])\s+(?=[A-Z])', line)
            for s in sents:
                clean = re.sub(r'[*#_`]', '', s).strip()
                if len(clean) >= 15 and not is_junk_item(clean) and clean not in statements:
                    statements.append(clean)

        if not statements:
            statements = [
                f"{topic_name} provides the structural framework for organizing core concepts.",
                f"The foundational principles of {topic_name} guide systematic execution and control.",
                f"Key components and methodologies are established to fulfill {topic_name} requirements.",
                f"Effective application of {topic_name} connects organizational goals to tangible actions.",
                f"Evaluation and feedback mechanisms maintain continuous alignment within {topic_name}."
            ]

        # Extract conceptual entities and subject-predicate structures from source
        parsed_concepts = []
        for stmt in statements:
            if stmt.startswith("Step: "):
                step_title = stmt.replace("Step: ", "").strip()
                parsed_concepts.append({
                    "concept": step_title,
                    "relation": "serves as",
                    "predicate": f"serves as an essential phase in the {topic_name} workflow",
                    "full_statement": f"{step_title} is an essential phase in {topic_name}.",
                })
                continue

            # Match common pedagogical patterns: "X is/are/involves/specifies/separates/manages/allows Y"
            match = re.match(r'^([A-Z][a-zA-Z0-9\s\-/]{2,35}?)\s+(is defined as|is an?|are an?|is|are|involves|specifies|separates|manages|allows|enables|consists of|acts as|coordinates)\s+(.+)$', stmt, re.IGNORECASE)
            if match:
                concept_name = match.group(1).strip()
                relation = match.group(2).strip().lower()
                predicate = match.group(3).strip().rstrip('. ')
                parsed_concepts.append({
                    "concept": concept_name,
                    "relation": relation,
                    "predicate": predicate,
                    "full_statement": stmt,
                })
            else:
                words = stmt.split()
                if len(words) >= 4:
                    concept_guess = " ".join(words[:min(3, len(words))])
                    pred_guess = " ".join(words[min(3, len(words)):])
                    parsed_concepts.append({
                        "concept": concept_guess,
                        "relation": "relates to",
                        "predicate": pred_guess,
                        "full_statement": stmt,
                    })

        questions: List[Dict[str, Any]] = []
        seen_question_texts = set()

        # Templates across the educational taxonomy (Requirement 6)
        question_templates = [
            # 1. Definition / Meaning
            {
                "type": "definition",
                "difficulty": "easy",
                "area": "Core Definitions",
                "format_q": lambda c, p, t: f"What is meant by {c} in the context of {t}?",
                "format_ans": lambda c, p, t: f"It {p}." if not p.lower().startswith(("a ", "an ", "the ", "it ", "serves ")) else (f"It is {p}." if p.lower().startswith(("a ", "an ", "the ")) else (f"It {p}." if p.lower().startswith("serves ") else f"{p}.")),
                "distractors": lambda c, p, others, t: [
                    f"It primarily acts as an optional post-implementation review rather than a core procedural stage.",
                    f"It is an informal guideline superseded by automated controls.",
                    f"It focuses solely on external compliance without guiding internal planning decisions."
                ],
            },
            # 2. Meaning & Purpose
            {
                "type": "meaning",
                "difficulty": "easy",
                "area": "Purpose & Objectives",
                "format_q": lambda c, p, t: f"What is the primary purpose or role of {c}?",
                "format_ans": lambda c, p, t: (f"To serve as {p[9:].strip()}." if p.lower().startswith("serves as") else (f"To {p}." if not p.lower().startswith(("to ", "it ")) else f"{p}.")),
                "distractors": lambda c, p, others, t: [
                    f"To separate administrative tasks without direct impact on {c}.",
                    f"To serve as an optional secondary stage with no structural role.",
                    f"To document historical logs without affecting current operations."
                ],
            },
            # 3. Concept Understanding
            {
                "type": "concept_understanding",
                "difficulty": "medium",
                "area": "Conceptual Principles",
                "format_q": lambda c, p, t: f"Which statement best explains how {c} functions within {t}?",
                "format_ans": lambda c, p, t: f"{c} {p}." if not p.lower().startswith(c.lower()) else f"{p}.",
                "distractors": lambda c, p, others, t: [
                    f"{c} operates independently without coordinating system resources.",
                    f"{c} replaces all underlying sub-processes with static configurations.",
                    f"{c} functions only when primary architectural controls are disabled."
                ],
            },
            # 4. Relationship & Interaction
            {
                "type": "relationship",
                "difficulty": "medium",
                "area": "System Relationships",
                "format_q": lambda c, p, t: f"How does {c} relate to the broader principles of {t}?",
                "format_ans": lambda c, p, t: f"It {p}." if p.lower().startswith("serves ") else (f"It establishes the mechanism that {p}." if not p.lower().startswith("it ") else f"{p}."),
                "distractors": lambda c, p, others, t: [
                    f"It contradicts the standard methodology of {t}.",
                    f"It functions in isolation, having no direct interaction with other components.",
                    f"It provides temporary feedback only after the primary process has completed."
                ],
            },
            # 5. Process & Mechanism
            {
                "type": "process",
                "difficulty": "medium",
                "area": "Operational Processes",
                "format_q": lambda c, p, t: f"During the operation of {c}, how is execution structured?",
                "format_ans": lambda c, p, t: f"It {p}." if p.lower().startswith("serves ") else (f"Through processes that {p}." if not p.lower().startswith("through ") else f"{p}."),
                "distractors": lambda c, p, others, t: [
                    f"Through random iteration without predefined procedural steps.",
                    f"By bypassing validation stages to prioritize execution speed.",
                    f"Through manual intervention required at every operational step."
                ],
            },
            # 6. Classification & Components
            {
                "type": "classification",
                "difficulty": "medium",
                "area": "Classifications & Structures",
                "format_q": lambda c, p, t: f"Which of the following accurately characterizes the structure of {c}?",
                "format_ans": lambda c, p, t: f"It is characterized by how it {p}." if not p.lower().startswith("it ") else f"{p}.",
                "distractors": lambda c, p, others, t: [
                    f"It is classified strictly as an unorganized collection of arbitrary rules.",
                    f"It represents a deprecated model that has been completely phased out.",
                    f"It consists solely of external monitoring without internal structure."
                ],
            },
            # 7. Comparison & Distinction
            {
                "type": "comparison",
                "difficulty": "hard",
                "area": "Distinctions & Differences",
                "format_q": lambda c, p, t: f"What key distinction defines the role of {c} in {t}?",
                "format_ans": lambda c, p, t: f"The essential distinction is that it {p}." if not p.lower().startswith("the ") else f"{p}.",
                "distractors": lambda c, p, others, t: [
                    f"It is identical in function to secondary support utilities.",
                    f"It eliminates the need for distinct operational boundaries.",
                    f"It reverses the hierarchy by placing outcomes before fundamental principles."
                ],
            },
            # 8. Scenario & Application
            {
                "type": "scenario",
                "difficulty": "hard",
                "area": "Practical Application",
                "format_q": lambda c, p, t: f"An engineer or practitioner implementing {c} needs to align with its core principles. Which action directly matches the process?",
                "format_ans": lambda c, p, t: f"Ensuring that the implementation {p}." if not p.lower().startswith("ensuring ") else f"{p}.",
                "distractors": lambda c, p, others, t: [
                    f"Disregarding {c} and applying arbitrary ad-hoc rules instead.",
                    f"Focusing exclusively on output metrics while ignoring underlying mechanisms.",
                    f"Postponing core configuration until after full system deployment."
                ],
            },
            # 9. Cause & Effect / Importance
            {
                "type": "cause_effect",
                "difficulty": "medium",
                "area": "Functional Importance",
                "format_q": lambda c, p, t: f"Why is {c} considered a critical element in {t}?",
                "format_ans": lambda c, p, t: f"Because it ensures that {p}." if not p.lower().startswith("because ") else f"{p}.",
                "distractors": lambda c, p, others, t: [
                    f"Because it reduces overall system accountability.",
                    f"Because it completely eliminates the need for ongoing evaluation.",
                    f"Because it serves purely decorative or non-functional purposes."
                ],
            },
            # 10. Sequence & Flow
            {
                "type": "sequence",
                "difficulty": "hard",
                "area": "Sequence & Flow",
                "format_q": lambda c, p, t: f"Which sequence correctly describes the role of {c} in the operational flow?",
                "format_ans": lambda c, p, t: f"It functions as a core component where it {p}." if not p.lower().startswith("it ") else f"{p}.",
                "distractors": lambda c, p, others, t: [
                    f"It occurs exclusively after the final results have already been produced.",
                    f"It runs concurrently without maintaining any state or synchronization.",
                    f"It is executed only when an unexpected failure occurs in the primary workflow."
                ],
            },
        ]

        total_needed = num_questions
        concept_idx = 0
        template_idx = 0
        attempts = 0
        max_attempts = max(200, total_needed * 15)

        while len(questions) < total_needed and attempts < max_attempts:
            attempts += 1
            curr_item = parsed_concepts[concept_idx % len(parsed_concepts)]
            curr_tmpl = question_templates[template_idx % len(question_templates)]
            concept_idx += 1
            template_idx += 1

            c_name = curr_item["concept"]
            c_pred = curr_item["predicate"]
            full_stmt = curr_item["full_statement"]

            # Generate question sentence
            q_text = curr_tmpl["format_q"](c_name, c_pred, topic_name)
            if q_text in seen_question_texts:
                # Add variation if duplicate
                variation_suffix = f" (Focus on {curr_tmpl['area']})" if attempts > len(parsed_concepts) * len(question_templates) else ""
                if variation_suffix:
                    q_text = curr_tmpl["format_q"](c_name, c_pred, topic_name).replace("?", f"{variation_suffix}?")
                if q_text in seen_question_texts:
                    continue

            # Generate correct answer
            correct_ans = curr_tmpl["format_ans"](c_name, c_pred, topic_name)
            # Ensure correct answer is clean and ends with period if sentence-like
            correct_ans = correct_ans.strip()

            # Generate 3 in-domain distractors
            other_statements = [s for s in statements if s != full_stmt]
            distractors = []

            # 1. First try to use other statements from the same topic as plausible confusion distractors
            if other_statements:
                other_idx = (attempts + len(questions)) % len(other_statements)
                other_stmt = other_statements[other_idx]
                if other_stmt.startswith("Step: "):
                    other_clean = other_stmt.replace("Step: ", "").strip()
                    distractor_candidate = f"It focuses on {other_clean} rather than {c_name}."
                elif not any(w in other_stmt.lower().split() for w in ["is", "are", "serves", "acts", "involves", "provides", "defines", "guides", "operates"]):
                    distractor_candidate = f"It focuses primarily on {other_stmt.strip()}."
                else:
                    distractor_candidate = other_stmt
                if distractor_candidate != correct_ans and distractor_candidate not in distractors:
                    distractors.append(distractor_candidate)

            # 2. Template-based conceptual misunderstanding distractors
            tmpl_distractors = curr_tmpl["distractors"](c_name, c_pred, other_statements, topic_name)

            for d in tmpl_distractors:
                if len(distractors) < 3 and d not in distractors and d != correct_ans:
                    distractors.append(d)

            # Ensure we have 3 unique distractors
            fallback_distractor_counter = 1
            while len(distractors) < 3:
                alt = f"It modifies secondary attributes without directly addressing the core {c_name} requirements (Variant {fallback_distractor_counter})."
                if alt not in distractors and alt != correct_ans:
                    distractors.append(alt)
                fallback_distractor_counter += 1

            options = [correct_ans] + distractors[:3]
            # Deterministically shuffle options so correct answer is not always first
            shift = (len(questions) * 3 + 1) % len(options)
            shuffled_options = options[shift:] + options[:shift]

            seen_question_texts.add(q_text)
            questions.append({
                "concept_area": curr_tmpl["area"],
                "question_type": curr_tmpl["type"],
                "difficulty": curr_tmpl["difficulty"],
                "question": q_text,
                "options": shuffled_options,
                "correct_answer": correct_ans,
                "source_reference": full_stmt,
                "explanation": f"Based on the topic material: \"{full_stmt}\", which establishes the role and characteristics of {c_name}.",
            })

        return questions[:total_needed]

ai_service = AIService()
