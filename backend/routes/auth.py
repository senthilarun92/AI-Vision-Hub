from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.dependencies import get_db
from backend.models.user import User

from backend.schemas.user import UserRegister, UserLogin, Token

from backend.utils.security import (
    hash_password,
    verify_password,
    create_access_token
)

from backend.config import ACCESS_TOKEN_EXPIRE
from backend.utils.responses import success_response


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.get("/")
def auth_home():
    return success_response(message="Authentication API Working")


@router.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(User.email == user.email).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(user.password)

    new_user = User(
        full_name=user.full_name,
        email=user.email,
        password_hash=hashed_password,
        phone=user.phone
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return success_response(
        message="User registered successfully.",
        data={"user_id": new_user.id}
    )


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):

    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid Email or Password")

    access_token = create_access_token(
        data={"sub": db_user.email, "user_id": db_user.id},
        expires_delta=ACCESS_TOKEN_EXPIRE
    )

    return success_response(
        message="Login successful.",
        data={"access_token": access_token, "token_type": "bearer"}
    )
