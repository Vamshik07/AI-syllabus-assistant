from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.models import Subject, User, SubjectProgress
from app.schemas.schemas import (
    SubjectCreate,
    SubjectUpdate,
    SubjectResponse,
    SubjectDetailResponse,
)
from app.api.deps import get_current_user
from app.services.progress_service import progress_service

router = APIRouter(prefix="/subjects", tags=["subjects"])

@router.post("", response_model=SubjectResponse)
def create_subject(
    subject_in: SubjectCreate,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    user = get_current_user(db, user_id or subject_in.user_id, authorization)
    subject = Subject(
        name=subject_in.name,
        description=subject_in.description,
        user_id=user.id,
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)
    
    # Initialize SubjectProgress
    progress_service._refresh_subject_progress(db, user.id, subject.id)
    return subject

@router.get("", response_model=List[SubjectResponse])
def list_subjects(
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    user = get_current_user(db, user_id, authorization)
    subjects = db.query(Subject).filter(Subject.user_id == user.id).order_by(Subject.created_at.desc()).all()
    for s in subjects:
        progress_service._refresh_subject_progress(db, user.id, s.id)
    db.commit()
    return subjects

@router.get("/{subject_id}", response_model=SubjectDetailResponse)
def get_subject(
    subject_id: str,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    user = get_current_user(db, user_id, authorization)
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found.")

    # Refresh subject progress calculation
    progress_service._refresh_subject_progress(db, user.id, subject.id)

    # Build response with units detail
    units_detail = []
    for u in subject.units:
        # Check topics for this unit
        topics_res = []
        if u.document:
            for t in u.document.topics:
                is_unlocked, status = progress_service.check_and_resolve_topic_unlock(db, t, user.id)
                topics_res.append({
                    "id": t.id,
                    "document_id": t.document_id,
                    "name": t.name,
                    "order_index": t.order_index,
                    "source_start": t.source_start,
                    "source_end": t.source_end,
                    "confidence": t.confidence,
                    "status": t.status,
                    "subtopics": [
                        {
                            "id": s.id,
                            "topic_id": s.topic_id,
                            "name": s.name,
                            "order_index": s.order_index,
                            "source_start": s.source_start,
                            "source_end": s.source_end,
                            "confidence": s.confidence,
                            "status": s.status,
                        } for s in t.subtopics
                    ],
                    "is_unlocked": is_unlocked,
                    "progress_status": status,
                })

        # Unit progress
        from app.models.models import UnitProgress
        up = db.query(UnitProgress).filter(
            UnitProgress.user_id == user.id,
            UnitProgress.unit_id == u.id
        ).first()

        unit_prog_res = None
        if up:
            unit_prog_res = {
                "unit_id": u.id,
                "unit_title": u.title,
                "topics_completed": up.topics_completed,
                "total_topics": up.total_topics,
                "completion_percentage": round((up.topics_completed / max(1, up.total_topics)) * 100.0, 1) if up.total_topics > 0 else 0.0,
                "master_quiz_unlocked": up.master_quiz_unlocked,
                "master_quiz_score": up.master_quiz_score,
                "status": up.status,
                "completed_at": up.completed_at,
                "topic_progress": [],
            }

        doc_res = None
        if u.document:
            doc_res = {
                "id": u.document.id,
                "unit_id": u.document.unit_id,
                "file_name": u.document.file_name,
                "file_type": u.document.file_type,
                "file_size": u.document.file_size,
                "page_count": u.document.page_count,
                "slide_count": u.document.slide_count,
                "processing_status": u.document.processing_status,
                "processing_error": u.document.processing_error,
                "created_at": u.document.created_at,
                "updated_at": u.document.updated_at,
            }

        units_detail.append({
            "id": u.id,
            "subject_id": u.subject_id,
            "title": u.title,
            "order_index": u.order_index,
            "description": u.description,
            "created_at": u.created_at,
            "updated_at": u.updated_at,
            "document": doc_res,
            "topics": topics_res,
            "progress": unit_prog_res,
        })

    # Subject progress
    sp = db.query(SubjectProgress).filter(
        SubjectProgress.user_id == user.id,
        SubjectProgress.subject_id == subject.id
    ).first()

    subj_prog_res = None
    if sp:
        subj_prog_res = {
            "subject_id": subject.id,
            "subject_name": subject.name,
            "units_completed": sp.units_completed,
            "total_units": sp.total_units,
            "completion_percentage": sp.completion_percentage,
            "status": sp.status,
            "unit_progress": [],
        }

    return {
        "id": subject.id,
        "user_id": subject.user_id,
        "name": subject.name,
        "description": subject.description,
        "created_at": subject.created_at,
        "updated_at": subject.updated_at,
        "units": units_detail,
        "progress": subj_prog_res,
    }

@router.put("/{subject_id}", response_model=SubjectResponse)
def update_subject(
    subject_id: str,
    subject_in: SubjectUpdate,
    db: Session = Depends(get_db),
):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found.")
    if subject_in.name is not None:
        subject.name = subject_in.name
    if subject_in.description is not None:
        subject.description = subject_in.description
    db.commit()
    db.refresh(subject)
    return subject

@router.delete("/{subject_id}")
def delete_subject(
    subject_id: str,
    db: Session = Depends(get_db),
):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found.")
    db.delete(subject)
    db.commit()
    return {"message": "Subject deleted successfully."}
