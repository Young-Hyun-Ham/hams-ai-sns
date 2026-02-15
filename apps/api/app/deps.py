from fastapi import Depends, Header, HTTPException
import psycopg

from app.db import get_db
from app.security import decode_access_token
from app.services.auth_service import get_user_by_id


def get_current_user(
    authorization: str | None = Header(default=None),
    conn: psycopg.Connection = Depends(get_db),
) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="인증 토큰이 필요합니다.")

    token = authorization.replace("Bearer ", "", 1)
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    user = get_user_by_id(conn, int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")

    return user
