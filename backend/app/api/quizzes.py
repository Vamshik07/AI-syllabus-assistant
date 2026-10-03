from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.models import Quiz
from app.schemas.schemas import QuizResponse, QuizAttemptRequest, QuizAttemptResponse
from app.api.deps import get_current_user
from app.services.progress_service import progress_service

router = APIRouter(prefix="/quizzes", tags=["quizzes"])

@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(
    quiz_id: str,
    db: Session = Depends(get_db),
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found.")
    return quiz

@router.post("/{quiz_id}/attempt", response_model=QuizAttemptResponse)
def submit_quiz_attempt(
    quiz_id: str,
    attempt_in: QuizAttemptRequest,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    user = get_current_user(db, attempt_in.user_id, authorization)
    result = progress_service.submit_quiz_attempt(
        db=db,
        quiz_id=quiz_id,
        user_id=user.id,
        submitted_answers=attempt_in.answers,
    )
    return result

@router.get("/{quiz_id}/latest-attempt", response_model=Optional[QuizAttemptResponse])
def get_latest_attempt(
    quiz_id: str,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    user = get_current_user(db, None, authorization)
    result = progress_service.get_latest_quiz_attempt(
        db=db,
        quiz_id=quiz_id,
        user_id=user.id,
    )
    return result

