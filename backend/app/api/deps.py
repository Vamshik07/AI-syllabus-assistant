from typing import Optional
from sqlalchemy.orm import Session
from app.models.models import User
from app.services.auth_service import auth_service

DEFAULT_USER_EMAIL = "student@sourcelearn.ai"
DEFAULT_USER_NAME = "SourceLearn Student"

def get_current_user(
    db: Session,
    user_id: Optional[str] = None,
    authorization: Optional[str] = None,
) -> User:
    """
    Returns authenticated user based on:
    1. Bearer JWT token in Authorization header
    2. user_id query/parameter (for test backward compatibility)
    3. Fallback student user
    """
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        payload = auth_service.decode_access_token(token)
        if payload and "sub" in payload:
            user = db.query(User).filter(User.id == payload["sub"]).first()
            if user:
                return user

    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            return user

    user = db.query(User).filter(User.email == DEFAULT_USER_EMAIL).first()
    if not user:
        user = User(email=DEFAULT_USER_EMAIL, name=DEFAULT_USER_NAME)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
