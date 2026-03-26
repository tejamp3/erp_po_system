# auth.py router - Handles /register and /login endpoints

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter()


# ─────────────────────────────────────────────
# POST /api/auth/register
# Creates a new user account
# ─────────────────────────────────────────────
@router.post("/register", response_model=schemas.UserResponse,
             status_code=status.HTTP_201_CREATED)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        # Check if username already taken
        if db.query(models.User).filter(
            models.User.username == user_data.username
        ).first():
            raise HTTPException(
                status_code=400,
                detail="Username already taken"
            )

        # Check if email already registered
        if db.query(models.User).filter(
            models.User.email == user_data.email
        ).first():
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        # Hash password before saving — NEVER store plain text!
        new_user = models.User(
            username        = user_data.username,
            email           = user_data.email,
            hashed_password = hash_password(user_data.password)
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# POST /api/auth/login
# Returns a JWT token on successful login
# ─────────────────────────────────────────────
@router.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Find user by username
    user = db.query(models.User).filter(
        models.User.username == form_data.username
    ).first()

    # Verify user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT token with username as subject
    access_token = create_access_token(data={"sub": user.username})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# ─────────────────────────────────────────────
# GET /api/auth/me
# Returns currently logged-in user info
# ─────────────────────────────────────────────
@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user