import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from app.models.models import (
    User,
    Subject,
    Unit,
    Topic,
    Quiz,
    QuizAttempt,
    TopicProgress,
    UnitProgress,
    SubjectProgress,
)

logger = logging.getLogger(__name__)

class ProgressService:
    def submit_quiz_attempt(
        self,
        db: Session,
        quiz_id: str,
        user_id: str,
        submitted_answers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Processes a quiz submission:
        - Calculates score and percentage
        - Applies 75% passing rule (e.g. 4/5 = 80% pass, 3/5 = 60% fail)
        - Records QuizAttempt
        - Unlocks next topic upon passing
        - Unlocks Master Quiz if all topics in unit are passed
        - Completes Unit upon passing Master Quiz
        - Updates Subject progress
        """
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found.")

        # Ensure user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        questions = quiz.questions
        total_questions = len(questions)
        if total_questions == 0:
            raise HTTPException(status_code=400, detail="Quiz has no questions.")

        score = 0
        results = []

        for q in questions:
            selected = submitted_answers.get(q.id)
            is_correct = (selected == q.correct_answer)
            if is_correct:
                score += 1

            results.append({
                "question_id": q.id,
                "question": q.question,
                "options": q.options,
                "selected_answer": selected,
                "correct_answer": q.correct_answer,
                "is_correct": is_correct,
                "source_reference": q.source_reference,
                "explanation": q.explanation,
            })

        percentage = round((score / total_questions) * 100.0, 1)
        passed = (percentage >= quiz.passing_percentage)

        # Record attempt
        attempt = QuizAttempt(
            user_id=user.id,
            quiz_id=quiz.id,
            score=score,
            total_questions=total_questions,
            percentage=percentage,
            passed=passed,
            answers=submitted_answers,
        )
        db.add(attempt)
        db.flush()

        unlocked_next_topic_id = None
        master_quiz_unlocked = False
        unit_completed = False

        if quiz.quiz_type == "TOPIC" and quiz.topic:
            topic = quiz.topic
            # Update topic progress
            t_prog = db.query(TopicProgress).filter(
                TopicProgress.user_id == user.id,
                TopicProgress.topic_id == topic.id
            ).first()

            if not t_prog:
                t_prog = TopicProgress(
                    user_id=user.id,
                    topic_id=topic.id,
                    status="PASSED" if passed else "IN_PROGRESS",
                    best_score=score,
                    attempt_count=1,
                    completed_at=datetime.now(timezone.utc) if passed else None,
                )
                db.add(t_prog)
            else:
                t_prog.attempt_count += 1
                if t_prog.best_score is None or score > t_prog.best_score:
                    t_prog.best_score = score
                if passed:
                    t_prog.status = "PASSED"
                    t_prog.completed_at = datetime.now(timezone.utc)
                elif t_prog.status != "PASSED":
                    t_prog.status = "IN_PROGRESS"

            # If passed, unlock next topic
            if passed:
                next_topic = db.query(Topic).filter(
                    Topic.document_id == topic.document_id,
                    Topic.order_index > topic.order_index
                ).order_by(Topic.order_index.asc()).first()

                if next_topic:
                    next_prog = db.query(TopicProgress).filter(
                        TopicProgress.user_id == user.id,
                        TopicProgress.topic_id == next_topic.id
                    ).first()
                    if not next_prog:
                        next_prog = TopicProgress(
                            user_id=user.id,
                            topic_id=next_topic.id,
                            status="UNLOCKED"
                        )
                        db.add(next_prog)
                    elif next_prog.status == "LOCKED":
                        next_prog.status = "UNLOCKED"
                    unlocked_next_topic_id = next_topic.id

            # Update unit progress
            unit_id = quiz.unit_id
            master_quiz_unlocked = self._refresh_unit_progress(db, user.id, unit_id)

        elif quiz.quiz_type == "MASTER_UNIT":
            unit_id = quiz.unit_id
            unit_prog = db.query(UnitProgress).filter(
                UnitProgress.user_id == user.id,
                UnitProgress.unit_id == unit_id
            ).first()

            if unit_prog:
                if unit_prog.master_quiz_score is None or score > unit_prog.master_quiz_score:
                    unit_prog.master_quiz_score = score
                if passed:
                    unit_prog.status = "COMPLETED"
                    unit_prog.completed_at = datetime.now(timezone.utc)
                    unit_completed = True

            # Update subject progress
            unit = db.query(Unit).filter(Unit.id == unit_id).first()
            if unit:
                self._refresh_subject_progress(db, user.id, unit.subject_id)

        db.commit()

        return {
            "attempt_id": attempt.id,
            "quiz_id": quiz.id,
            "score": score,
            "total_questions": total_questions,
            "percentage": percentage,
            "passed": passed,
            "passing_percentage": quiz.passing_percentage,
            "results": results,
            "unlocked_next_topic_id": unlocked_next_topic_id,
            "master_quiz_unlocked": master_quiz_unlocked,
            "unit_completed": unit_completed,
        }

    def _refresh_unit_progress(self, db: Session, user_id: str, unit_id: str) -> bool:
        """Updates UnitProgress topic counts and checks if master quiz is unlocked."""
        unit = db.query(Unit).filter(Unit.id == unit_id).first()
        if not unit:
            return False

        topics = []
        if unit.document:
            topics = unit.document.topics

        total_topics = len(topics)
        if total_topics == 0:
            return False

        topic_ids = [t.id for t in topics]
        passed_count = db.query(TopicProgress).filter(
            TopicProgress.user_id == user_id,
            TopicProgress.topic_id.in_(topic_ids),
            TopicProgress.status == "PASSED"
        ).count()

        unit_prog = db.query(UnitProgress).filter(
            UnitProgress.user_id == user_id,
            UnitProgress.unit_id == unit_id
        ).first()

        master_unlocked = (passed_count == total_topics and total_topics > 0)

        if not unit_prog:
            unit_prog = UnitProgress(
                user_id=user_id,
                unit_id=unit_id,
                total_topics=total_topics,
                topics_completed=passed_count,
                master_quiz_unlocked=master_unlocked,
                status="COMPLETED" if (master_unlocked and unit_prog and unit_prog.status == "COMPLETED") else ("IN_PROGRESS" if passed_count > 0 else "NOT_STARTED")
            )
            db.add(unit_prog)
        else:
            unit_prog.total_topics = total_topics
            unit_prog.topics_completed = passed_count
            unit_prog.master_quiz_unlocked = master_unlocked
            if unit_prog.status != "COMPLETED":
                unit_prog.status = "IN_PROGRESS" if passed_count > 0 else "NOT_STARTED"

        # Update subject progress as well
        self._refresh_subject_progress(db, user_id, unit.subject_id)
        return master_unlocked

    def _refresh_subject_progress(self, db: Session, user_id: str, subject_id: str):
        """Calculates SubjectProgress derived from units."""
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject:
            return

        total_units = len(subject.units)
        if total_units == 0:
            return

        unit_ids = [u.id for u in subject.units]
        unit_progs = db.query(UnitProgress).filter(
            UnitProgress.user_id == user_id,
            UnitProgress.unit_id.in_(unit_ids)
        ).all()
        unit_prog_map = {up.unit_id: up for up in unit_progs}

        total_unit_percentages = 0.0
        completed_units = 0
        has_any_progress = False

        for u in subject.units:
            up = unit_prog_map.get(u.id)
            if up:
                if up.status == "COMPLETED":
                    total_unit_percentages += 100.0
                    completed_units += 1
                    has_any_progress = True
                elif up.total_topics > 0:
                    u_pct = (up.topics_completed / up.total_topics) * 100.0
                    total_unit_percentages += u_pct
                    if up.topics_completed > 0:
                        has_any_progress = True
                    if up.topics_completed == up.total_topics:
                        completed_units += 1

        percentage = round(total_unit_percentages / max(1, total_units), 1)
        if completed_units == total_units and percentage >= 100.0:
            status = "COMPLETED"
        elif has_any_progress or percentage > 0.0:
            status = "IN_PROGRESS"
        else:
            status = "NOT_STARTED"

        subj_prog = db.query(SubjectProgress).filter(
            SubjectProgress.user_id == user_id,
            SubjectProgress.subject_id == subject_id
        ).first()

        if not subj_prog:
            subj_prog = SubjectProgress(
                user_id=user_id,
                subject_id=subject_id,
                total_units=total_units,
                units_completed=completed_units,
                completion_percentage=percentage,
                status=status
            )
            db.add(subj_prog)
        else:
            subj_prog.total_units = total_units
            subj_prog.units_completed = completed_units
            subj_prog.completion_percentage = percentage
            subj_prog.status = status

    def get_latest_quiz_attempt(
        self,
        db: Session,
        quiz_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            return None

        attempt = db.query(QuizAttempt).filter(
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.user_id == user_id
        ).order_by(QuizAttempt.created_at.desc()).first()

        if not attempt:
            return None

        questions = quiz.questions
        submitted_answers = attempt.answers or {}
        results = []
        for q in questions:
            selected = submitted_answers.get(q.id)
            is_correct = (selected == q.correct_answer)
            results.append({
                "question_id": q.id,
                "question": q.question,
                "options": q.options,
                "selected_answer": selected,
                "correct_answer": q.correct_answer,
                "is_correct": is_correct,
                "source_reference": q.source_reference,
                "explanation": q.explanation,
            })

        unlocked_next_topic_id = None
        master_quiz_unlocked = False
        unit_completed = False

        if quiz.quiz_type == "TOPIC" and quiz.topic and attempt.passed:
            topic = quiz.topic
            next_topic = db.query(Topic).filter(
                Topic.document_id == topic.document_id,
                Topic.order_index > topic.order_index
            ).order_by(Topic.order_index.asc()).first()
            if next_topic:
                unlocked_next_topic_id = next_topic.id
            else:
                all_topics = db.query(Topic).filter(Topic.document_id == topic.document_id).all()
                all_ids = [t.id for t in all_topics]
                passed_count = db.query(TopicProgress).filter(
                    TopicProgress.user_id == user_id,
                    TopicProgress.topic_id.in_(all_ids),
                    TopicProgress.status == "PASSED"
                ).count()
                if passed_count >= len(all_ids):
                    master_quiz_unlocked = True

        return {
            "attempt_id": attempt.id,
            "quiz_id": quiz.id,
            "score": attempt.score,
            "total_questions": attempt.total_questions,
            "percentage": attempt.percentage,
            "passed": attempt.passed,
            "passing_percentage": quiz.passing_percentage,
            "results": results,
            "unlocked_next_topic_id": unlocked_next_topic_id,
            "master_quiz_unlocked": master_quiz_unlocked,
            "unit_completed": unit_completed,
        }

    def check_and_resolve_topic_unlock(self, db: Session, topic: Topic, user_id: str) -> Tuple[bool, str]:
        """
        Determines if a topic is unlocked for a user.
        - If existing progress is UNLOCKED, IN_PROGRESS, PASSED, or COMPLETED -> returns True.
        - If it's the very first topic in the document -> returns True (auto-creates UNLOCKED).
        - If the immediately preceding topic is PASSED -> auto-unlocks this topic and returns True.
        - Otherwise returns False, LOCKED.
        """
        tp = db.query(TopicProgress).filter(
            TopicProgress.user_id == user_id,
            TopicProgress.topic_id == topic.id
        ).first()

        if tp and tp.status in ["UNLOCKED", "IN_PROGRESS", "PASSED", "COMPLETED"]:
            return True, tp.status

        # Find preceding topics in document
        preceding = db.query(Topic).filter(
            Topic.document_id == topic.document_id,
            Topic.order_index < topic.order_index
        ).order_by(Topic.order_index.asc()).all()

        if not preceding:
            # First topic in document
            if not tp:
                tp = TopicProgress(user_id=user_id, topic_id=topic.id, status="UNLOCKED")
                db.add(tp)
                db.commit()
            return True, "UNLOCKED"

        # Check if the immediately preceding topic is PASSED
        prev_topic = preceding[-1]
        prev_tp = db.query(TopicProgress).filter(
            TopicProgress.user_id == user_id,
            TopicProgress.topic_id == prev_topic.id
        ).first()

        if prev_tp and prev_tp.status in ["PASSED", "COMPLETED"]:
            if not tp:
                tp = TopicProgress(
                    user_id=user_id,
                    topic_id=topic.id,
                    status="UNLOCKED"
                )
                db.add(tp)
                db.commit()
            elif tp.status == "LOCKED":
                tp.status = "UNLOCKED"
                db.commit()
            return True, "UNLOCKED"

        status = tp.status if tp else "LOCKED"
        return False, status

progress_service = ProgressService()

