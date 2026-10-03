import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.models import User
from app.schemas.schemas import (
    UserRegister,
    UserLogin,
    UserResponse,
    AuthTokenResponse,
)
from app.services.auth_service import auth_service
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=AuthTokenResponse)
def register(
    user_in: UserRegister,
    db: Session = Depends(get_db),
):
    clean_email = user_in.email.strip().lower()
    if not clean_email or "@" not in clean_email:
        raise HTTPException(status_code=400, detail="A valid email address is required.")
    if len(user_in.password.strip()) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long.")

    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="An account with this email already exists. Please login instead."
        )

    hashed_pw = auth_service.hash_password(user_in.password.strip())
    new_user = User(
        email=clean_email,
        name=user_in.name.strip() or clean_email.split("@")[0].capitalize(),
        hashed_password=hashed_pw,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = auth_service.create_access_token(user_id=new_user.id, email=new_user.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": new_user,
    }

@router.post("/login", response_model=AuthTokenResponse)
def login(
    user_in: UserLogin,
    db: Session = Depends(get_db),
):
    clean_email = user_in.email.strip().lower()
    user = db.query(User).filter(User.email == clean_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not user.hashed_password:
        # Default seed user without password; allow password setup or login
        user.hashed_password = auth_service.hash_password(user_in.password.strip())
        db.commit()
        db.refresh(user)
    else:
        is_valid = auth_service.verify_password(user_in.password.strip(), user.hashed_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password."
            )

    token = auth_service.create_access_token(user_id=user.id, email=user.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }

@router.get("/me", response_model=UserResponse)
def get_me(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please provide a valid Bearer token."
        )

    user = get_current_user(db, authorization=authorization)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or session expired."
        )
    return user
