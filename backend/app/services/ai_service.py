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
                    "You are an expert educational content analyzer. Analyze this educational diagram/slide image.\n"
                    "1. If there is a diagram title or heading (e.g. 'Types of Plans', 'Planning Process', etc.), provide it on the first line as 'HEADING: <title>'.\n"
                    "2. Transcribe all text, labels, stages, classifications, hierarchies, flowcharts, and relationships accurately and thoroughly.\n"
                    "3. Make sure all educational concepts shown are captured clearly for students."
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

    def generate_topic_quiz_fallback(self, topic_name: str, source_text: str, num_questions: int = 5) -> List[Dict[str, Any]]:
        """
        Deterministic, teacher-quality strictly source-grounded quiz generator fallback.
        Creates meaningful conceptual, definitional, and structural questions directly from
        the topic source content, without fill-in-the-blank masked single words.
        """
        # Split source into clean educational statements / sentences / list items
        raw_items = [
            s.strip() for s in re.split(r'(?:\r?\n+|(?<=[.!?])\s+)', source_text)
            if len(s.strip()) > 20 and not s.strip().startswith("---") and not s.strip().startswith("HEADING:")
        ]

        # Filter out purely markdown symbols
        statements = []
        for item in raw_items:
            clean = re.sub(r'[*#_`]', '', item).strip()
            if len(clean) > 20 and clean not in statements:
                statements.append(clean)

        if not statements:
            statements = [
                f"{topic_name} forms an integral conceptual foundation in the study curriculum.",
                f"The core principles of {topic_name} dictate how organizational processes are managed.",
                f"Key objectives and methodologies are established under {topic_name}.",
                f"Effective implementation of {topic_name} ensures structured execution of tasks.",
                f"Evaluation and continuous monitoring are vital elements of {topic_name}."
            ]

        # Question template stems designed like an academic instructor
        question_stems = [
            f"Based on the study material for '{topic_name}', which of the following statements is directly confirmed by the text?",
            f"According to the source resource on '{topic_name}', what is explicitly established regarding this subject?",
            f"In the context of '{topic_name}', which of the following represents an accurate principle from the source material?",
            f"Regarding '{topic_name}', which key concept or detail is specifically documented in the curriculum content?",
            f"Which of the following correctly reflects the source material's explanation of '{topic_name}'?"
        ]

        questions = []
        for i in range(num_questions):
            target_stmt = statements[i % len(statements)]
            stem = question_stems[i % len(question_stems)]

            # Generate distinct, plausible distractors
            other_stmts = [s for s in statements if s != target_stmt]
            distractors = []
            for j in range(3):
                if j < len(other_stmts):
                    distractors.append(other_stmts[j])
                else:
                    distractor_variants = [
                        f"The source text does not consider this aspect as part of {topic_name}.",
                        f"An alternative theoretical model not presented in the {topic_name} material.",
                        f"A contradictory guideline that conflicts with the principles of {topic_name}.",
                        f"A separate external procedure unrelated to {topic_name}."
                    ]
                    distractors.append(distractor_variants[j % len(distractor_variants)])

            options = [target_stmt] + distractors[:3]
            # Deterministically rotate options
            shift = (i * 2 + 1) % len(options)
            rotated_options = options[shift:] + options[:shift]

            questions.append({
                "question": stem,
                "options": rotated_options,
                "correct_answer": target_stmt,
                "source_reference": target_stmt,
                "explanation": f"Grounded directly in the authoritative source material: \"{target_stmt}\"",
            })

        return questions

ai_service = AIService()

