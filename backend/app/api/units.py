from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Header
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.models import Unit, Subject, Document, Topic, TopicProgress, UnitProgress
from app.schemas.schemas import (
    UnitCreate,
    UnitUpdate,
    UnitResponse,
    UnitDetailResponse,
    TopicResponse,
    DocumentResponse,
    QuizResponse,
    QuizAttemptRequest,
    QuizAttemptResponse,
)
from app.api.deps import get_current_user
from app.services.document_service import document_service
from app.services.quiz_service import quiz_service
from app.services.progress_service import progress_service

router = APIRouter(tags=["units"])

@router.post("/subjects/{subject_id}/units", response_model=UnitResponse)
def create_unit_for_subject(
    subject_id: str,
    unit_in: UnitCreate,
    db: Session = Depends(get_db),
):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found.")

    unit = Unit(
        subject_id=subject.id,
        title=unit_in.title,
        order_index=unit_in.order_index,
        description=unit_in.description,
    )
    db.add(unit)
    db.commit()
    db.refresh(unit)

    # Initialize UnitProgress
    user = subject.user
    if user:
        up = UnitProgress(
            user_id=user.id,
            unit_id=unit.id,
            total_topics=0,
            topics_completed=0,
            status="NOT_STARTED"
        )
        db.add(up)
        db.commit()
        progress_service._refresh_subject_progress(db, user.id, subject.id)

    return unit

@router.get("/units/{unit_id}", response_model=UnitDetailResponse)
def get_unit(
    unit_id: str,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    user = get_current_user(db, user_id, authorization)
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found.")

    # Fetch topics
    topics_list = []
    if unit.document:
        for t in unit.document.topics:
            is_unlocked, status = progress_service.check_and_resolve_topic_unlock(db, t, user.id)

            topics_list.append({
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
    up = db.query(UnitProgress).filter(
        UnitProgress.user_id == user.id,
        UnitProgress.unit_id == unit.id
    ).first()

    unit_prog_res = None
    if up:
        unit_prog_res = {
            "unit_id": unit.id,
            "unit_title": unit.title,
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
    if unit.document:
        doc_res = {
            "id": unit.document.id,
            "unit_id": unit.document.unit_id,
            "file_name": unit.document.file_name,
            "file_type": unit.document.file_type,
            "file_size": unit.document.file_size,
            "page_count": unit.document.page_count,
            "slide_count": unit.document.slide_count,
            "processing_status": unit.document.processing_status,
            "processing_error": unit.document.processing_error,
            "created_at": unit.document.created_at,
            "updated_at": unit.document.updated_at,
        }

    return {
        "id": unit.id,
        "subject_id": unit.subject_id,
        "title": unit.title,
        "order_index": unit.order_index,
        "description": unit.description,
        "created_at": unit.created_at,
        "updated_at": unit.updated_at,
        "document": doc_res,
        "topics": topics_list,
        "progress": unit_prog_res,
    }

@router.put("/units/{unit_id}", response_model=UnitResponse)
def update_unit(
    unit_id: str,
    unit_in: UnitUpdate,
    db: Session = Depends(get_db),
):
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found.")
    if unit_in.title is not None:
        unit.title = unit_in.title
    if unit_in.order_index is not None:
        unit.order_index = unit_in.order_index
    if unit_in.description is not None:
        unit.description = unit_in.description
    db.commit()
    db.refresh(unit)
    return unit

@router.delete("/units/{unit_id}")
def delete_unit(
    unit_id: str,
    db: Session = Depends(get_db),
):
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found.")
    subject_id = unit.subject_id
    user_id = unit.subject.user_id
    db.delete(unit)
    db.commit()
    progress_service._refresh_subject_progress(db, user_id, subject_id)
    return {"message": "Unit deleted successfully."}

@router.get("/units/{unit_id}/topics", response_model=List[TopicResponse])
def get_unit_topics(
    unit_id: str,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    user = get_current_user(db, user_id, authorization)
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found.")
    if not unit.document:
        return []

    topics_res = []
    for t in unit.document.topics:
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
    return topics_res

@router.post("/units/{unit_id}/document", response_model=DocumentResponse)
async def upload_unit_document(
    unit_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found.")

    content = await file.read()
    doc = document_service.save_and_create_document(db, unit_id, file, content)
    # Process document synchronously for instant readiness
    processed_doc = document_service.process_document(db, doc.id)
    return processed_doc

@router.post("/units/{unit_id}/master-quiz/generate", response_model=QuizResponse)
def generate_master_quiz(
    unit_id: str,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    user = get_current_user(db, user_id, authorization)
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found.")

    # Verify that master quiz is unlocked (all topics completed)
    up = db.query(UnitProgress).filter(
        UnitProgress.user_id == user.id,
        UnitProgress.unit_id == unit.id
    ).first()

    if not up or not up.master_quiz_unlocked:
        # Check if actually all topics completed
        all_passed = progress_service._refresh_unit_progress(db, user.id, unit.id)
        if not all_passed:
            raise HTTPException(
                status_code=400,
                detail="Master Quiz is locked. All topics in this unit must be passed first."
            )

    quiz = quiz_service.get_or_generate_master_quiz(db, unit_id)
    return quiz

@router.post("/units/{unit_id}/master-quiz/attempt", response_model=QuizAttemptResponse)
def attempt_master_quiz(
    unit_id: str,
    attempt_in: QuizAttemptRequest,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    user = get_current_user(db, attempt_in.user_id, authorization)
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found.")

    quiz = quiz_service.get_or_generate_master_quiz(db, unit_id)
    result = progress_service.submit_quiz_attempt(
        db=db,
        quiz_id=quiz.id,
        user_id=user.id,
        submitted_answers=attempt_in.answers,
    )
    return result
