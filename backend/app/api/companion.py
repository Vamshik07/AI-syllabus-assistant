import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, Header
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.schemas import CompanionChatRequest, CompanionChatResponse
from app.api.deps import get_current_user
from app.services.companion_service import companion_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/companion", tags=["companion"])

@router.post("/chat", response_model=CompanionChatResponse)
def companion_chat(
    req: CompanionChatRequest,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    """
    Interactive chat with Sir Paws-a-Lot (AI Study Cat Companion).
    Strictly source-grounded in Study Mode, with optional General Knowledge mode.
    """
    user = get_current_user(db, user_id, authorization)
    return companion_service.chat(db, req)

@router.get("/bubble")
def get_companion_bubble(
    page_type: str = Query("dashboard"),
    topic_name: Optional[str] = Query(None),
):
    """
    Fetches contextual speech bubble text and companion state for the current view.
    """
    return companion_service.get_context_bubble(page_type, topic_name)
