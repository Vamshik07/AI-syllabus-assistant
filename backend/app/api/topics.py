from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.models import Topic, TopicProgress, SourceRegion
from app.schemas.schemas import (
    TopicResponse,
    TopicContentView,
    TopicProgressResponse,
    QuizResponse,
    SourceRegionResponse,
    SubtopicResponse,
)
from app.api.deps import get_current_user
from app.services.quiz_service import quiz_service
from app.services.progress_service import progress_service

router = APIRouter(prefix="/topics", tags=["topics"])

@router.get("/{topic_id}", response_model=TopicResponse)
def get_topic(
    topic_id: str,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    user = get_current_user(db, user_id, authorization)
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found.")

    is_unlocked, status = progress_service.check_and_resolve_topic_unlock(db, topic, user.id)

    return {
        "id": topic.id,
        "document_id": topic.document_id,
        "name": topic.name,
        "order_index": topic.order_index,
        "source_start": topic.source_start,
        "source_end": topic.source_end,
        "confidence": topic.confidence,
        "status": topic.status,
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
            } for s in topic.subtopics
        ],
        "is_unlocked": is_unlocked,
        "progress_status": status,
    }

@router.get("/{topic_id}/content", response_model=TopicContentView)
def get_topic_content(
    topic_id: str,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    """
    Returns authentic original source content for the topic.
    Strictly preserves original page rendering, layout, tables, images, and text.
    """
    user = get_current_user(db, user_id, authorization)
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found.")

    # Ensure user progress record exists
    is_unlocked, status = progress_service.check_and_resolve_topic_unlock(db, topic, user.id)

    # Update status to IN_PROGRESS if UNLOCKED
    tp = db.query(TopicProgress).filter(
        TopicProgress.user_id == user.id,
        TopicProgress.topic_id == topic.id
    ).first()
    if tp and tp.status == "UNLOCKED":
        tp.status = "IN_PROGRESS"
        db.commit()

    regions = db.query(SourceRegion).filter(
        SourceRegion.topic_id == topic.id
    ).order_by(SourceRegion.element_order).all()

    subtopics_res = [
        SubtopicResponse(
            id=s.id,
            topic_id=s.topic_id,
            name=s.name,
            order_index=s.order_index,
            source_start=s.source_start,
            source_end=s.source_end,
            confidence=s.confidence,
            status=s.status,
        ) for s in topic.subtopics
    ]

    regions_res = [
        SourceRegionResponse(
            id=r.id,
            document_id=r.document_id,
            topic_id=r.topic_id,
            subtopic_id=r.subtopic_id,
            page_number=r.page_number,
            slide_number=r.slide_number,
            region_type=r.region_type,
            x1=r.x1,
            y1=r.y1,
            x2=r.x2,
            y2=r.y2,
            element_order=r.element_order,
            source_reference=r.source_reference,
            content_text=r.content_text,
            content_html=r.content_html,
            media_path=r.media_path,
        ) for r in regions
    ]

    unit_id = topic.document.unit.id if (topic.document and topic.document.unit) else None
    unit_title = topic.document.unit.title if (topic.document and topic.document.unit) else None
    subject_id = topic.document.unit.subject.id if (topic.document and topic.document.unit and topic.document.unit.subject) else None
    subject_name = topic.document.unit.subject.name if (topic.document and topic.document.unit and topic.document.unit.subject) else None

    return TopicContentView(
        topic_id=topic.id,
        topic_name=topic.name,
        order_index=topic.order_index,
        document_id=topic.document_id,
        file_type=topic.document.file_type,
        file_name=topic.document.file_name,
        source_start=topic.source_start,
        source_end=topic.source_end,
        subtopics=subtopics_res,
        regions=regions_res,
        unit_id=unit_id,
        unit_title=unit_title,
        subject_id=subject_id,
        subject_name=subject_name,
    )

@router.post("/{topic_id}/quiz/generate", response_model=QuizResponse)
def generate_topic_quiz(
    topic_id: str,
    regenerate: bool = Query(False),
    db: Session = Depends(get_db),
):
    quiz = quiz_service.get_or_generate_topic_quiz(db, topic_id, regenerate=regenerate)
    return quiz


@router.get("/{topic_id}/quiz", response_model=QuizResponse)
def get_topic_quiz(
    topic_id: str,
    db: Session = Depends(get_db),
):
    quiz = quiz_service.get_or_generate_topic_quiz(db, topic_id)
    return quiz

@router.get("/{topic_id}/progress", response_model=TopicProgressResponse)
def get_topic_progress(
    topic_id: str,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    user = get_current_user(db, user_id, authorization)
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found.")

    tp = db.query(TopicProgress).filter(
        TopicProgress.user_id == user.id,
        TopicProgress.topic_id == topic.id
    ).first()

    status = tp.status if (tp and tp.status != "LOCKED") else "UNLOCKED"
    best_score = tp.best_score if tp else None
    attempt_count = tp.attempt_count if tp else 0
    completed_at = tp.completed_at if tp else None

    return {
        "topic_id": topic.id,
        "topic_name": topic.name,
        "order_index": topic.order_index,
        "status": status,
        "best_score": best_score,
        "attempt_count": attempt_count,
        "completed_at": completed_at,
    }
