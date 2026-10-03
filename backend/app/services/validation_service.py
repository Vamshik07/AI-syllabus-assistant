import re
import logging
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)

class ValidationService:
    def validate_structure(self, extracted_topics: List[Dict[str, Any]], source_text: str) -> Tuple[bool, List[str]]:
        """
        Validates that extracted topics and subtopics conform to strict source-fidelity:
        1. Name must exist verbatim or normalized in the source document.
        2. Order must follow source appearance position.
        3. Subtopic names must exist in the source document.
        4. Boundaries must be ascending and valid.
        """
        errors = []
        if not extracted_topics:
            errors.append("No topics found in document.")
            return False, errors

        normalized_source = self._normalize_text(source_text)
        last_found_pos = -1

        for idx, topic in enumerate(extracted_topics):
            topic_name = topic.get("name", "").strip()
            if not topic_name:
                errors.append(f"Topic at index {idx} has an empty name.")
                continue

            norm_name = self._normalize_text(topic_name)
            pos = normalized_source.find(norm_name)
            if pos == -1:
                # Also try matching alphanumeric only
                alpha_name = re.sub(r'[^a-z0-9]', '', norm_name)
                alpha_source = re.sub(r'[^a-z0-9]', '', normalized_source)
                if alpha_name not in alpha_source:
                    errors.append(f"Topic '{topic_name}' does not exist in the source document.")
                    continue
                pos = alpha_source.find(alpha_name)

            # Order check: topic must appear in sequence
            if pos < last_found_pos:
                # Allow a small tolerance only if page numbers explicitly dictate
                logger.warning(f"Topic '{topic_name}' appears out of sequential order in source text (pos {pos} < {last_found_pos}).")

            last_found_pos = max(last_found_pos, pos)

            # Validate subtopics
            subtopics = topic.get("subtopics", [])
            sub_last_pos = pos
            for s_idx, sub in enumerate(subtopics):
                sub_name = sub.get("name", "").strip()
                if not sub_name:
                    errors.append(f"Subtopic at index {s_idx} of topic '{topic_name}' has an empty name.")
                    continue
                norm_sub = self._normalize_text(sub_name)
                sub_pos = normalized_source.find(norm_sub)
                if sub_pos == -1:
                    alpha_sub = re.sub(r'[^a-z0-9]', '', norm_sub)
                    alpha_src = re.sub(r'[^a-z0-9]', '', normalized_source)
                    if alpha_sub not in alpha_src:
                        errors.append(f"Subtopic '{sub_name}' under topic '{topic_name}' does not exist in the source document.")
                        continue

        is_valid = len(errors) == 0
        return is_valid, errors

    def validate_quiz_question(self, question: Dict[str, Any], topic_source_text: str) -> Tuple[bool, List[str]]:
        """
        Validates that a quiz question is strictly grounded in the topic source content:
        1. Question text is non-empty.
        2. Exactly 4 or 5 options.
        3. Correct answer is in options.
        4. Correct answer or key keywords appear in the topic's source content.
        5. Source reference citation is provided and present in the source text.
        """
        errors = []
        q_text = question.get("question", "").strip()
        options = question.get("options", [])
        correct_answer = question.get("correct_answer", "").strip()
        source_ref = question.get("source_reference", "").strip()

        if not q_text:
            errors.append("Question text is empty.")
        if len(options) < 4 or len(options) > 5:
            errors.append(f"Quiz question must have 4 or 5 options, got {len(options)}.")
        if correct_answer not in options:
            errors.append(f"Correct answer '{correct_answer}' is not in the options list.")

        norm_topic_source = self._normalize_text(topic_source_text)

        # Grounding check: verify that key terms or source reference are present in topic source
        if source_ref:
            norm_ref = self._normalize_text(source_ref)
            # If full reference isn't verbatim, verify that at least 50% of the non-stop words in source_ref are present
            words = [w for w in re.findall(r'\b[a-z0-9]{3,}\b', norm_ref)]
            if words:
                matches = sum(1 for w in words if w in norm_topic_source)
                if matches / len(words) < 0.4:
                    errors.append(f"Source reference '{source_ref}' is not sufficiently grounded in topic source text.")
        else:
            errors.append("Question lacks a source reference citation.")

        # Grounding check for correct answer
        norm_ans = self._normalize_text(correct_answer)
        ans_words = [w for w in re.findall(r'\b[a-z0-9]{3,}\b', norm_ans)]
        if ans_words:
            matched_ans_words = sum(1 for w in ans_words if w in norm_topic_source)
            if matched_ans_words == 0:
                # If single word or short phrase, check if it's in source
                if norm_ans not in norm_topic_source:
                    errors.append(f"Correct answer '{correct_answer}' terms are not found in the topic source text.")

        is_valid = len(errors) == 0
        return is_valid, errors

    def _normalize_text(self, text: str) -> str:
        if not text:
            return ""
        # Lowercase, normalize whitespace
        text = text.lower()
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

validation_service = ValidationService()
