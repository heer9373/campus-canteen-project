"""
auth.py
FR-1: JWT-based session management (HMAC-SHA256, 24h expiry)
NFR-2: bcrypt password hashing, salt rounds >= 10
"""

import os
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

JWT_SECRET = os.getenv("JWT_SECRET", "dev_secret_change_me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRES_HOURS = int(os.getenv("JWT_EXPIRES_HOURS", "24"))
SALT_ROUNDS = int(os.getenv("BCRYPT_SALT_ROUNDS", "10"))

security = HTTPBearer()


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=SALT_ROUNDS)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(user_id: int, roll_number: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRES_HOURS)
    payload = {
        "sub": str(user_id),
        "roll_number": roll_number,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """FastAPI dependency: verifies the Bearer token and returns the user claims."""
    payload = decode_token(creds.credentials)
    return {
        "id": int(payload["sub"]),
        "roll_number": payload["roll_number"],
        "role": payload["role"],
    }


def require_roles(*allowed_roles: str):
    """FastAPI dependency factory for role-based access control."""

    def checker(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: insufficient role privileges",
            )
        return user

    return checker
