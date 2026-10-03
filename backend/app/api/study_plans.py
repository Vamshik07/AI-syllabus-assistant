from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.database import get_db
from app.models.models import Subject
from app.services.study_plan_service import study_plan_service

router = APIRouter(prefix="/subjects", tags=["study plans"])


class StudyPlanRequest(BaseModel):
    start_date: date
    end_date: date
    daily_hours: float = Field(default=2.0, gt=0, le=24)


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
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
