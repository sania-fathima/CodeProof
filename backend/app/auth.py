import hashlib
import hmac
import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

router = APIRouter(tags=["Authentication"])


class UserRegister(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=150)
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: str = Field(min_length=5, max_length=150)
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    created_at: datetime


def get_db():
    try:
        from app.database import Base, engine, SessionLocal
        from app import models

        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Check DB_PASS and PostgreSQL.",
        ) from exc

    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    iterations = 600_000
    hashed = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt, iterations
    )
    return f"pbkdf2_sha256${iterations}${salt.hex()}${hashed.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt_hex, hash_hex = stored_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations)
        if not 1 <= iterations <= 2_000_000:
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        if len(salt) != 16 or len(expected) != 32:
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt, iterations
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(user: UserRegister, db: Session = Depends(get_db)):
    from app import models

    full_name = user.full_name.strip()
    email = user.email.strip().lower()

    if len(full_name) < 2 or email.count("@") != 1 or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=422, detail="Invalid name or email")

    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    new_user = models.User(
        full_name=full_name,
        email=email,
        password_hash=hash_password(user.password),
    )
    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered") from exc

    return new_user


@router.post("/login")
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    from app import models

    email = user.email.strip().lower()
    existing = db.query(models.User).filter(models.User.email == email).first()

    if not existing or not verify_password(user.password, existing.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {
        "message": "Password verified successfully",
        "user_id": existing.id,
        "email": existing.email,
    }
