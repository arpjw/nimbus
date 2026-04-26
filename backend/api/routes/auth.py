from fastapi import APIRouter, Depends, HTTPException, Header
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional
import jwt
import os
from datetime import datetime, timedelta
from database import get_session
from models.user import User
from services.auth import ApiKey
import secrets

router = APIRouter(prefix="/auth", tags=["auth"])

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-in-prod")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 30


def create_nimbus_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(days=JWT_EXPIRY_DAYS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_nimbus_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(
    authorization: Optional[str] = Header(None),
    session: Session = Depends(get_session)
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    user_id = decode_nimbus_token(token)
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


class GitHubAuthRequest(BaseModel):
    github_id: str
    github_username: str
    github_email: Optional[str] = None
    github_avatar_url: Optional[str] = None


class AuthResponse(BaseModel):
    token: str
    user_id: str
    username: str
    avatar_url: Optional[str]
    plan: str
    tasks_this_month: int
    api_key: Optional[str] = None


@router.post("/github", response_model=AuthResponse)
async def github_auth(body: GitHubAuthRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.github_id == body.github_id)).first()
    is_new = user is None
    if not user:
        user = User(
            github_id=body.github_id,
            github_username=body.github_username,
            github_email=body.github_email,
            github_avatar_url=body.github_avatar_url,
        )
        session.add(user)
    else:
        user.github_username = body.github_username
        user.github_email = body.github_email or user.github_email
        user.github_avatar_url = body.github_avatar_url or user.github_avatar_url
        user.updated_at = datetime.utcnow()

    session.commit()
    session.refresh(user)

    new_api_key = None
    if is_new:
        raw_key = f"nk_{secrets.token_urlsafe(32)}"
        api_key = ApiKey(
            key=raw_key,
            name="Default key",
            user_id=user.id,
        )
        session.add(api_key)
        session.commit()
        new_api_key = raw_key

    token = create_nimbus_token(user.id)
    return AuthResponse(
        token=token,
        user_id=user.id,
        username=user.github_username,
        avatar_url=user.github_avatar_url,
        plan=user.plan,
        tasks_this_month=user.tasks_this_month,
        api_key=new_api_key,
    )


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.github_username,
        "email": current_user.github_email,
        "avatar_url": current_user.github_avatar_url,
        "plan": current_user.plan,
        "tasks_this_month": current_user.tasks_this_month,
    }


@router.post("/logout")
async def logout():
    return {"status": "logged out"}
