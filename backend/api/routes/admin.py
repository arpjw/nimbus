from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from services.auth import ApiKey
from models.user import User
import os

router = APIRouter(prefix="/admin", tags=["admin"])

ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "")


@router.post("/link-keys")
async def link_orphan_keys(
    secret: str,
    github_username: str,
    session: Session = Depends(get_session),
):
    if not ADMIN_SECRET or secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")

    user = session.exec(select(User).where(User.github_username == github_username)).first()
    if not user:
        return {"error": f"User {github_username} not found"}

    keys = session.exec(select(ApiKey).where(ApiKey.user_id == None)).all()
    for key in keys:
        key.user_id = user.id
        session.add(key)
    session.commit()
    return {"linked": len(keys), "user": github_username, "user_id": user.id}
