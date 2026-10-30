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
    def get_or_generate_topic_quiz(
        self,
        db: Session,
        topic_id: str,
        regenerate: bool = False,
        num_questions: Optional[int] = None
    ) -> Quiz:
        """
        Gets existing quiz or generates a natural educational quiz that tests the student's
        understanding of the COMPLETE topic, grounded strictly in uploaded resources.
        """
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found.")

        # Check if quiz already generated
        existing_quiz = db.query(Quiz).filter(
            Quiz.topic_id == topic.id,
            Quiz.quiz_type == "TOPIC"
        ).first()

        # If not regenerating and valid non-robotic quiz exists, return it
        if (
            not regenerate
            and existing_quiz
            and existing_quiz.questions
            and len(existing_quiz.questions) >= 5
            and not any(self._is_robotic_question(q.question) for q in existing_quiz.questions)
        ):
            return existing_quiz

        # Fetch complete source content strictly belonging to this topic (all slides, pages, visuals)
        source_content = self._get_topic_source_content(db, topic)
        if not source_content.strip():
            raise HTTPException(
                status_code=422,
                detail="This topic has no extracted source content; a grounded quiz cannot be generated.",
            )

        # Adapt quiz size to topic complexity if not explicitly provided
        if num_questions is None:
            num_questions = self._determine_topic_quiz_size(source_content)

        # Generate questions strictly from source content
        questions_data = self._generate_questions(topic.name, source_content, num_questions=num_questions)

        # Delete any existing quiz if regenerating or replacing
        if existing_quiz:
            db.delete(existing_quiz)
            db.commit()

        quiz = Quiz(
            topic_id=topic.id,
            unit_id=topic.document.unit_id if topic.document else None,
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
                concept_area=q.get("concept_area", "Core Concepts"),
                question_type=q.get("question_type", "concept_understanding"),
                difficulty=q.get("difficulty", "medium"),
                order_index=idx,
            )
            db.add(qq)

        db.commit()
        db.refresh(quiz)
        return quiz

    def _determine_topic_quiz_size(self, source_content: str) -> int:
        """Adapts quiz size to source material depth (small: 5, medium: 8, large: 10)."""
        content_length = len(source_content.strip())
        if content_length > 4000:
            return 10
        elif content_length > 2000:
            return 8
        return 5

    def get_or_generate_master_quiz(self, db: Session, unit_id: str, regenerate: bool = False) -> Quiz:
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
            not regenerate
            and existing_quiz
            and existing_quiz.questions
            and len(existing_quiz.questions) == question_count
            and existing_quiz.passing_percentage == 65.0
            and not any(self._is_robotic_question(q.question) for q in existing_quiz.questions)
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
                concept_area=q.get("concept_area", "Unit Master Concepts"),
                question_type=q.get("question_type", "concept_understanding"),
                difficulty=q.get("difficulty", "medium"),
                order_index=idx,
            )
            db.add(qq)

        db.commit()
        db.refresh(quiz)
        return quiz

    def _master_question_count(self, db: Session, topics: List[Topic]) -> int:
        """Scale the final assessment to the amount of available topic content (min 25)."""
        content_units = 0
        for topic in topics:
            source = self._get_topic_source_content(db, topic)
            units = [
                item.strip()
                for item in re.split(r"(?:\r?\n+|(?<=[.!?])\s+)", source)
                if len(item.strip()) >= 15
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
            return []

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
        seen_q_texts = set()

        for (topic, source), quota in zip(topic_sources, quotas):
            if not source:
                continue
            topic_qs = self._generate_questions(topic.name, source, num_questions=quota)
            for q in topic_qs:
                if q["question"] not in seen_q_texts:
                    seen_q_texts.add(q["question"])
                    questions.append(q)

        # Ensure we fulfill the exact question_count if duplicates were skipped
        if len(questions) < question_count:
            for topic, source in topic_sources:
                if len(questions) >= question_count:
                    break
                needed = question_count - len(questions)
                extra_qs = ai_service.generate_topic_quiz_fallback(topic.name, source, num_questions=needed + 5)
                for q in extra_qs:
                    if q["question"] not in seen_q_texts and len(questions) < question_count:
                        is_valid, _ = validation_service.validate_quiz_question(q, source)
                        if is_valid:
                            seen_q_texts.add(q["question"])
                            questions.append(q)

        return questions[:question_count]

    def _generate_subject_questions(
        self, topic_sources: List[Any], question_count: int
    ) -> List[Dict[str, Any]]:
        """Generate one balanced assessment from every source-backed subject topic."""
        available = [(topic, source.strip()) for topic, source in topic_sources if source.strip()]
        if not available:
            return []

        quotas = [1] * len(available)
        remaining = max(0, question_count - len(quotas))
        while remaining:
            selected = min(range(len(quotas)), key=lambda idx: quotas[idx])
            quotas[selected] += 1
            remaining -= 1

        questions = []
        seen = set()
        for (topic, source), quota in zip(available, quotas):
            for question in self._generate_questions(topic.name, source, num_questions=quota):
                if question["question"] not in seen:
                    seen.add(question["question"])
                    questions.append(question)
        return questions[:question_count]

    def _get_topic_source_content(self, db: Session, topic: Topic) -> str:
        """Collects complete raw text and visual transcription from source regions belonging to this topic."""
        from app.services.learning_service import is_presenter_or_admin_line, learning_service, format_diagram_content_text

        learning_service._hydrate_topic_image_regions(db, topic)

        regions = db.query(SourceRegion).filter(
            SourceRegion.topic_id == topic.id
        ).order_by(SourceRegion.element_order).all()

        text_pieces = []
        for r in regions:
            if r.content_text and r.content_text.strip():
                formatted = format_diagram_content_text(r.content_text)
                clean_lines = [
                    l.strip() for l in formatted.splitlines()
                    if l.strip() and not is_presenter_or_admin_line(l)
                ]
                if clean_lines:
                    content = "\n".join(clean_lines)
                    if r.region_type in ("DIAGRAM", "FLOWCHART", "IMAGE"):
                        content = f"Visual Diagram Structure:\n{content}"
                    elif r.region_type == "TABLE":
                        content = f"Table Data:\n{content}"
                    text_pieces.append(content)

        # If text_pieces is still empty, gather from visuals
        if not text_pieces and topic.learning_data:
            visuals = topic.learning_data.get("visuals", [])
            for v in visuals:
                cap = v.get("caption") or ""
                if cap:
                    text_pieces.append(f"[Visual Diagram]:\nTopic: {topic.name}\nDiagram: {cap}")

        return "\n\n".join(text_pieces)

    def _is_robotic_question(self, question: str) -> bool:
        """Identify quizzes generated by the old sentence-retrieval fallback."""
        normalized = re.sub(r"\s+", " ", question.lower())
        return any(
            phrase in normalized
            for phrase in (
                "according to the source",
                "according to the document",
                "according to the text",
                "what is explicitly established",
                "what is documented",
                "which detail is confirmed",
                "directly confirmed by the text",
                "which of the following is explicitly stated",
                "based on the uploaded resource",
                "in the source text",
                "stated in the document",
                # Additional patterns from old cached quizzes
                "based on the study material for",
                "according to the source resource on",
                "represents an accurate principle from the source",
                "accurate principle from the source material",
                "which of the following represents an accurate principle from",
                "from the source material",
                "from the provided text",
                "according to the provided text",
                "in the provided text",
                "within the context of the provided",
                "based on the material",
                "confirmed by the text",
                "as stated in the text",
            )
        )


    def _generate_questions(self, topic_name: str, source_content: str, num_questions: int = 5) -> List[Dict[str, Any]]:
        """Generates and validates quiz questions strictly from source content."""
        questions = []
        seen_questions = set()
        
        # If AI service is available, prompt Gemini
        if ai_service.is_available():
            prompt = QUIZ_GENERATION_PROMPT.format(
                num_questions=num_questions,
                topic_name=topic_name,
                source_content=source_content,
            )
            res = ai_service.generate_json(prompt)
            if res and "questions" in res:
                candidate_questions = res["questions"]
                for q in candidate_questions:
                    is_valid, errors = validation_service.validate_quiz_question(q, source_content)
                    if is_valid and q["question"] not in seen_questions:
                        seen_questions.add(q["question"])
                        questions.append(q)
                    else:
                        logger.warning(f"Discarding invalid generated question: {errors}")

                questions = questions[:num_questions]

        # If the model returns too few valid questions, fill missing questions using pedagogical fallback.
        if len(questions) < num_questions:
            needed = num_questions - len(questions)
            fallback_qs = ai_service.generate_topic_quiz_fallback(topic_name, source_content, num_questions=needed + 5)
            for q in fallback_qs:
                is_valid, errors = validation_service.validate_quiz_question(q, source_content)
                if is_valid and q["question"] not in seen_questions and len(questions) < num_questions:
                    seen_questions.add(q["question"])
                    questions.append(q)
                elif not is_valid:
                    logger.warning(f"Discarding invalid fallback question: {errors}")

        return questions[:num_questions]

    def generate_subject_assessment(
        self, db: Session, subject_id: str, question_count: int = 12, regenerate: bool = False
    ) -> Quiz:
        """
        Generates a balanced full-syllabus master assessment across all units and topics in the subject.
        Uses 65% passing percentage rule for syllabus completion.
        """
        from app.models.models import Subject
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found.")

        if not subject.units:
            raise HTTPException(status_code=400, detail="Subject has no units.")

        first_unit = subject.units[0]

        existing_quiz = db.query(Quiz).filter(
            Quiz.unit_id == first_unit.id,
            Quiz.quiz_type == "SUBJECT_ASSESSMENT"
        ).first()

        if existing_quiz and not regenerate:
            if existing_quiz.questions and not any(self._is_robotic_question(q.question) for q in existing_quiz.questions):
                return existing_quiz
            else:
                db.delete(existing_quiz)
                db.commit()

        # Collect topics and source content from all units
        topic_sources = []
        for u in subject.units:
            if u.document:
                for t in u.document.topics:
                    src = self._get_topic_source_content(db, t)
                    topic_sources.append((t, src))

        if not topic_sources:
            raise HTTPException(status_code=400, detail="No processed topics found across subject units.")

        questions_data = self._generate_subject_questions(topic_sources, question_count=question_count)
        if not questions_data:
            raise HTTPException(status_code=422, detail="No source-backed topic content is available for assessment generation.")

        quiz = Quiz(
            unit_id=first_unit.id,
            quiz_type="SUBJECT_ASSESSMENT",
            passing_percentage=65.0,
        )
        db.add(quiz)
        db.flush()

        for idx, q_data in enumerate(questions_data):
            qq = QuizQuestion(
                quiz_id=quiz.id,
                question=q_data["question"],
                options=q_data["options"],
                correct_answer=q_data["correct_answer"],
                source_reference=q_data.get("source_reference", "Subject Full Syllabus"),
                explanation=q_data.get("explanation"),
                concept_area=q_data.get("concept_area", "Full Syllabus"),
                question_type=q_data.get("question_type", "concept_understanding"),
                difficulty=q_data.get("difficulty", "medium"),
                order_index=idx + 1,
            )
            db.add(qq)

        db.commit()
        db.refresh(quiz)
        return quiz

quiz_service = QuizService()

