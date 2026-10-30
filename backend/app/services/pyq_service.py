import re
import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import Subject, Topic
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)

class PYQService:
    def analyze_pyq_text(self, db: Session, subject: Subject, pyq_text: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyzes Previous Year Question (PYQ) text:
        - Extracts individual questions and sub-questions
        - Maps them against the subject's topics
        - Identifies topic frequency and repeated concepts
        - Annotates topics with PYQ frequency and exam notes
        - Strictly adheres to Rule: Never claims exam guarantees, only historical frequency.
        """
        all_topics: List[Topic] = []
        for unit in subject.units:
            if unit.document:
                all_topics.extend(unit.document.topics)

        if not all_topics:
            return {
                "message": "Subject has no processed topics yet. Please upload study resources first.",
                "total_questions_detected": 0,
                "topic_frequencies": {},
            }

        # 1. Split raw text into individual questions
        questions = self._extract_questions_from_text(pyq_text)
        if not questions:
            # Fallback split by lines with question marks or keywords
            questions = [
                line.strip() for line in pyq_text.splitlines()
                if len(line.strip()) > 15 and any(kw in line.lower() for kw in ("explain", "what is", "discuss", "describe", "define", "compare", "differentiate", "?"))
            ]

        topic_matches: Dict[str, List[str]] = {t.id: [] for t in all_topics}

        # 2. Map questions to topics
        for q in questions:
            best_topic = self._match_question_to_topic(q, all_topics)
            if best_topic:
                topic_matches[best_topic.id].append(q)

        # 3. Update topics in database
        results_summary = []
        for t in all_topics:
            matched_qs = topic_matches[t.id]
            if matched_qs:
                t.pyq_frequency = (t.pyq_frequency or 0) + len(matched_qs)
                existing_notes = t.pyq_notes or ""
                new_notes = f"Appeared in {len(matched_qs)} question(s) in {filename or 'PYQ'}:\n" + "\n".join(f"- {q[:100]}..." for q in matched_qs[:3])
                t.pyq_notes = f"{existing_notes}\n{new_notes}".strip()
                results_summary.append({
                    "topic_id": t.id,
                    "topic_name": t.name,
                    "frequency": t.pyq_frequency,
                    "sample_questions": matched_qs[:2],
                })

        # 4. Save metadata in subject
        summary_payload = {
            "last_analyzed_file": filename or "Uploaded PYQ",
            "total_questions": len(questions),
            "frequent_topics": sorted(results_summary, key=lambda x: x["frequency"], reverse=True),
        }
        subject.pyq_data = summary_payload
        db.commit()

        return summary_payload

    def _extract_questions_from_text(self, text: str) -> List[str]:
        # Matches Q1, 1., (a), Question 1, etc.
        pattern = re.compile(r'(?:^|\n)(?:Q(?:uestion)?\s*\d+[\.\:]?|\d+[\.\)]|\([a-z]\))\s*(.+?)(?=(?:\n(?:Q(?:uestion)?\s*\d+[\.\:]?|\d+[\.\)]|\([a-z]\))|\Z))', re.DOTALL | re.IGNORECASE)
        matches = pattern.findall(text)
        cleaned = []
        for m in matches:
            c = " ".join(m.split()).strip()
            if len(c) > 15:
                cleaned.append(c)
        return cleaned

    def _match_question_to_topic(self, question: str, topics: List[Topic]) -> Optional[Topic]:
        q_lower = question.lower()
        q_words = set(re.findall(r'[a-z0-9]{4,}', q_lower))

        best_topic = None
        best_score = 0

        for t in topics:
            t_name_lower = t.name.lower()
            # Exact or phrase match
            if t_name_lower in q_lower:
                return t

            t_words = set(re.findall(r'[a-z0-9]{4,}', t_name_lower))
            overlap = len(t_words.intersection(q_words))
            if overlap > best_score and overlap >= 1:
                best_score = overlap
                best_topic = t

        return best_topic if best_score >= 1 else None

pyq_service = PYQService()
