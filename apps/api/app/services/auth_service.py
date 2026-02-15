import os

import psycopg

from app.security import create_access_token, hash_password, verify_password


DEFAULT_EMAIL = os.getenv("DEFAULT_USER_EMAIL", "owner@hams.local")
DEFAULT_PASSWORD = os.getenv("DEFAULT_USER_PASSWORD", "hams1234")
DEFAULT_NICKNAME = os.getenv("DEFAULT_USER_NICKNAME", "owner")


def ensure_default_user(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE email = %s", (DEFAULT_EMAIL,))
        user = cur.fetchone()
        if user:
            return
        cur.execute(
            "INSERT INTO users (email, password_hash, nickname) VALUES (%s, %s, %s)",
            (DEFAULT_EMAIL, hash_password(DEFAULT_PASSWORD), DEFAULT_NICKNAME),
        )
    conn.commit()


def login(conn: psycopg.Connection, email: str, password: str) -> str:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, email, password_hash FROM users WHERE email = %s",
            (email,),
        )
        user = cur.fetchone()

    if not user or not verify_password(password, user["password_hash"]):
        raise ValueError("이메일 또는 비밀번호가 올바르지 않습니다.")

    return create_access_token(user_id=user["id"], email=user["email"])


def get_user_by_id(conn: psycopg.Connection, user_id: int) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, email, nickname FROM users WHERE id = %s",
            (user_id,),
        )
        user = cur.fetchone()
    return user
