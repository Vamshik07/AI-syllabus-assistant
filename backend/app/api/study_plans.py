from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.database import get_db
from app.models.models import Subject, StudyRoadmap
from app.services.study_plan_service import study_plan_service

router = APIRouter(prefix="/subjects", tags=["study plans"])


class StudyPlanRequest(BaseModel):
    start_date: date
    end_date: date
    daily_hours: float = Field(default=2.0, gt=0, le=24)
    material_preference: Optional[str] = Field(default="auto")  # "auto", "concise", "detailed"
    selected_topic_ids: Optional[List[str]] = None
    only_important: Optional[bool] = False


@router.get("/{subject_id}/topics-for-plan")
def get_subject_topics_for_plan(
    subject_id: str,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    """Returns all topics for the subject annotated with workload, importance, and student progress."""
    user = get_current_user(db, user_id, authorization)
    subject = db.query(Subject).filter(
        Subject.id == subject_id,
        Subject.user_id == user.id,
    ).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found.")

    return study_plan_service.get_subject_topics_for_plan(subject, db=db, user_id=user.id)


@router.get("/{subject_id}/study-plan")
def get_existing_study_plan(
    subject_id: str,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    """Returns the existing active study roadmap for this subject, if one exists."""
    user = get_current_user(db, user_id, authorization)
    saved = db.query(StudyRoadmap).filter(
        StudyRoadmap.user_id == user.id,
        StudyRoadmap.subject_id == subject_id,
    ).first()

    if not saved or not saved.plan_data:
        raise HTTPException(status_code=404, detail="No active study roadmap found for this subject.")

    return saved.plan_data


@router.post("/{subject_id}/study-plan")
def create_study_plan(
    subject_id: str,
    plan_in: StudyPlanRequest,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    user = get_current_user(db, user_id, authorization)
    subject = db.query(Subject).filter(
        Subject.id == subject_id,
        Subject.user_id == user.id,
    ).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found.")
    if plan_in.end_date < plan_in.start_date:
        raise HTTPException(status_code=422, detail="End date must be on or after start date.")

    try:
        return study_plan_service.create_plan(
            db,
            subject,
            plan_in.start_date,
            plan_in.end_date,
            plan_in.daily_hours,
            user_id=user.id,
            material_preference=plan_in.material_preference,
            selected_topic_ids=plan_in.selected_topic_ids,
            only_important=plan_in.only_important,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
