from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.models import Unit, Subject, UnitProgress, SubjectProgress, TopicProgress
from app.schemas.schemas import UnitProgressResponse, SubjectProgressResponse, TopicProgressResponse
from app.api.deps import get_current_user
from app.services.progress_service import progress_service

router = APIRouter(tags=["progress"])

@router.get("/units/{unit_id}/progress", response_model=UnitProgressResponse)
def get_unit_progress(
    unit_id: str,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    user = get_current_user(db, user_id, authorization)
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found.")

    progress_service._refresh_unit_progress(db, user.id, unit.id)

    up = db.query(UnitProgress).filter(
        UnitProgress.user_id == user.id,
        UnitProgress.unit_id == unit.id
    ).first()

    topics = unit.document.topics if unit.document else []
    topic_progs = []
    for t in topics:
        tp = db.query(TopicProgress).filter(
            TopicProgress.user_id == user.id,
            TopicProgress.topic_id == t.id
        ).first()
        status = tp.status if tp else ("UNLOCKED" if t.order_index == 1 else "LOCKED")
        topic_progs.append(TopicProgressResponse(
            topic_id=t.id,
            topic_name=t.name,
            order_index=t.order_index,
            status=status,
            best_score=tp.best_score if tp else None,
            attempt_count=tp.attempt_count if tp else 0,
            completed_at=tp.completed_at if tp else None,
        ))

    completed_count = up.topics_completed if up else 0
    total_count = up.total_topics if up else len(topics)
    pct = round((completed_count / max(1, total_count)) * 100.0, 1) if total_count > 0 else 0.0

    return UnitProgressResponse(
        unit_id=unit.id,
        unit_title=unit.title,
        topics_completed=completed_count,
        total_topics=total_count,
        completion_percentage=pct,
        master_quiz_unlocked=up.master_quiz_unlocked if up else False,
        master_quiz_score=up.master_quiz_score if up else None,
        status=up.status if up else "NOT_STARTED",
        completed_at=up.completed_at if up else None,
        topic_progress=topic_progs,
    )

@router.get("/subjects/{subject_id}/progress", response_model=SubjectProgressResponse)
def get_subject_progress(
    subject_id: str,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    user = get_current_user(db, user_id, authorization)
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found.")

    progress_service._refresh_subject_progress(db, user.id, subject.id)

    sp = db.query(SubjectProgress).filter(
        SubjectProgress.user_id == user.id,
        SubjectProgress.subject_id == subject.id
    ).first()

    unit_progs = []
    for u in subject.units:
        up = db.query(UnitProgress).filter(
            UnitProgress.user_id == user.id,
            UnitProgress.unit_id == u.id
        ).first()
        completed = up.topics_completed if up else 0
        total = up.total_topics if up else 0
        pct = round((completed / max(1, total)) * 100.0, 1) if total > 0 else 0.0

        unit_progs.append(UnitProgressResponse(
            unit_id=u.id,
            unit_title=u.title,
            topics_completed=completed,
            total_topics=total,
            completion_percentage=pct,
            master_quiz_unlocked=up.master_quiz_unlocked if up else False,
            master_quiz_score=up.master_quiz_score if up else None,
            status=up.status if up else "NOT_STARTED",
            completed_at=up.completed_at if up else None,
            topic_progress=[],
        ))

    completed_units = sp.units_completed if sp else 0
    total_units = sp.total_units if sp else len(subject.units)
    subj_pct = sp.completion_percentage if sp else 0.0

    return SubjectProgressResponse(
        subject_id=subject.id,
        subject_name=subject.name,
        units_completed=completed_units,
        total_units=total_units,
        completion_percentage=subj_pct,
        status=sp.status if sp else "NOT_STARTED",
        unit_progress=unit_progs,
    )
