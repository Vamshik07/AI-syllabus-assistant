import logging
import re
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.models import Topic, Unit, Quiz, QuizQuestion, SourceRegion
from app.services.ai_service import ai_service
from app.services.validation_service import validation_service
from app.services.prompts.quiz_prompt import QUIZ_GENERATION_PROMPT

logger = logging.getLogger(__name__)

class QuizService:
    def get_or_generate_topic_quiz(self, db: Session, topic_id: str) -> Quiz:
        """
        Gets existing quiz or generates a strictly source-grounded 5-question quiz for the topic.
        """
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found.")

        # Check if quiz already generated
        existing_quiz = db.query(Quiz).filter(
            Quiz.topic_id == topic.id,
            Quiz.quiz_type == "TOPIC"
        ).first()

        if existing_quiz and existing_quiz.questions and len(existing_quiz.questions) == 5:
            return existing_quiz

        # Fetch source content strictly belonging to this topic
        source_content = self._get_topic_source_content(db, topic)
        if not source_content.strip():
            source_content = f"{topic.name}. This topic covers essential concepts in the unit."

        # Generate 5 questions strictly from source content
        questions_data = self._generate_questions(topic.name, source_content, num_questions=5)

        # Delete any partial quiz if exists
        if existing_quiz:
            db.delete(existing_quiz)
            db.commit()

        quiz = Quiz(
            topic_id=topic.id,
            unit_id=topic.document.unit_id,
            quiz_type="TOPIC",
            passing_percentage=75.0,
        )
        db.add(quiz)
        db.flush()

        for idx, q in enumerate(questions_data):
            qq = QuizQuestion(
                quiz_id=quiz.id,
                question=q["question"],
                options=q["options"],
                correct_answer=q["correct_answer"],
                source_reference=q.get("source_reference", topic.name),
                explanation=q.get("explanation"),
                order_index=idx,
            )
            db.add(qq)

        db.commit()
        db.refresh(quiz)
        return quiz

    def get_or_generate_master_quiz(self, db: Session, unit_id: str) -> Quiz:
        """
        Gets or generates the Master Unit Quiz (covering all topics in the unit).
        Questions are strictly generated from source material of the unit. The
        assessment contains at least 25 questions and scales up to 100 based
        on the amount of source content available.
        """
        unit = db.query(Unit).filter(Unit.id == unit_id).first()
        if not unit:
            raise HTTPException(status_code=404, detail="Unit not found.")

        existing_quiz = db.query(Quiz).filter(
            Quiz.unit_id == unit.id,
            Quiz.quiz_type == "MASTER_UNIT"
        ).first()

        all_topics = list(unit.document.topics) if unit.document else []
        question_count = self._master_question_count(db, all_topics)

        if (
            existing_quiz
            and existing_quiz.questions
            and len(existing_quiz.questions) == question_count
            and existing_quiz.passing_percentage == 65.0
        ):
            return existing_quiz

        questions_data = self._generate_master_questions(db, unit, all_topics, question_count)

        if existing_quiz:
            db.delete(existing_quiz)
            db.commit()

        quiz = Quiz(
            topic_id=None,
            unit_id=unit.id,
            quiz_type="MASTER_UNIT",
            passing_percentage=65.0,
        )
        db.add(quiz)
        db.flush()

        for idx, q in enumerate(questions_data):
            qq = QuizQuestion(
                quiz_id=quiz.id,
                question=q["question"],
                options=q["options"],
                correct_answer=q["correct_answer"],
                source_reference=q.get("source_reference", unit.title),
                explanation=q.get("explanation"),
                order_index=idx,
            )
            db.add(qq)

        db.commit()
        db.refresh(quiz)
        return quiz

    def _master_question_count(self, db: Session, topics: List[Topic]) -> int:
        """Scale the final assessment to the amount of available topic content."""
        content_units = 0
        for topic in topics:
            source = self._get_topic_source_content(db, topic)
            units = [
                item.strip()
                for item in re.split(r"(?:\r?\n+|(?<=[.!?])\s+)", source)
                if len(item.strip()) >= 20
            ]
            content_units += max(1, len(set(units)))
        return min(100, max(25, content_units))

    def _generate_master_questions(
        self,
        db: Session,
        unit: Unit,
        topics: List[Topic],
        question_count: int,
    ) -> List[Dict[str, Any]]:
        """Generate a balanced final assessment with source coverage per topic."""
        if not topics:
            return self._generate_questions(
                f"Unit Master: {unit.title}",
                f"Unit: {unit.title}. Educational resource material.",
                num_questions=question_count,
            )

        topic_sources = [
            (topic, self._get_topic_source_content(db, topic).strip())
            for topic in topics
        ]
        quotas = [1] * len(topic_sources)
        remaining = question_count - len(quotas)
        content_sizes = [max(1, len(source)) for _, source in topic_sources]

        while remaining > 0:
            selected = max(
                range(len(quotas)),
                key=lambda idx: content_sizes[idx] / quotas[idx],
            )
            quotas[selected] += 1
            remaining -= 1

        questions: List[Dict[str, Any]] = []
        for (topic, source), quota in zip(topic_sources, quotas):
            if not source:
                source = f"{topic.name}. This topic covers essential concepts in the unit."
            questions.extend(
                self._generate_questions(topic.name, source, num_questions=quota)
            )

        return questions[:question_count]

    def _get_topic_source_content(self, db: Session, topic: Topic) -> str:
        """Collects exact raw text from source regions belonging strictly to this topic."""
        regions = db.query(SourceRegion).filter(
            SourceRegion.topic_id == topic.id
        ).order_by(SourceRegion.element_order).all()

        text_pieces = []
        for r in regions:
            if r.content_text and r.content_text.strip():
                text_pieces.append(r.content_text.strip())

        return "\n\n".join(text_pieces)

    def _generate_questions(self, topic_name: str, source_content: str, num_questions: int = 5) -> List[Dict[str, Any]]:
        """Generates and validates quiz questions strictly from source content."""
        questions = []
        
        # If AI service is available, prompt Gemini
        if ai_service.is_available():
            prompt = QUIZ_GENERATION_PROMPT.format(
                num_questions=num_questions,
                topic_name=topic_name,
                source_content=source_content[:6000]
            )
            res = ai_service.generate_json(prompt)
            if res and "questions" in res:
                candidate_questions = res["questions"]
                valid_questions = []
                for q in candidate_questions:
                    is_valid, errors = validation_service.validate_quiz_question(q, source_content)
                    if is_valid:
                        valid_questions.append(q)
                    else:
                        logger.warning(f"Discarding invalid generated question: {errors}")

                if len(valid_questions) >= num_questions:
                    questions = valid_questions[:num_questions]

        # If questions count is less than required, fill with deterministic source-grounded generator
        if len(questions) < num_questions:
            needed = num_questions - len(questions)
            fallback_qs = ai_service.generate_topic_quiz_fallback(topic_name, source_content, num_questions=needed)
            for q in fallback_qs:
                is_valid, errors = validation_service.validate_quiz_question(q, source_content)
                questions.append(q)

        return questions[:num_questions]

quiz_service = QuizService()
