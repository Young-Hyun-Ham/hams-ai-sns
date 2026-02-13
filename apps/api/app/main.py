from fastapi import Depends, FastAPI, HTTPException, Query, Response
import psycopg

from app.db import get_connection, get_db, init_db
from app.deps import get_current_user
from app.schemas import (
    ActivityLogResponse,
    BotCreateRequest,
    BotJobResponse,
    BotResponse,
    BotUpdateRequest,
    LoginRequest,
    LoginResponse,
    MeResponse,
)
from app.services import auth_service, bot_service

app = FastAPI(title="hams-api", version="0.3.0")


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    with get_connection() as conn:
        auth_service.ensure_default_user(conn)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "api"}


@app.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, conn: psycopg.Connection = Depends(get_db)) -> LoginResponse:
    try:
        access_token = auth_service.login(conn, payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return LoginResponse(access_token=access_token)


@app.get("/auth/me", response_model=MeResponse)
def me(current_user: dict = Depends(get_current_user)) -> MeResponse:
    return MeResponse(**current_user)


@app.get("/bots", response_model=list[BotResponse])
def get_bots(
    current_user: dict = Depends(get_current_user),
    conn: psycopg.Connection = Depends(get_db),
) -> list[BotResponse]:
    rows = bot_service.list_bots(conn, current_user["id"])
    return [BotResponse(**row) for row in rows]


@app.post("/bots", response_model=BotResponse, status_code=201)
def create_bot(
    payload: BotCreateRequest,
    current_user: dict = Depends(get_current_user),
    conn: psycopg.Connection = Depends(get_db),
) -> BotResponse:
    row = bot_service.create_bot(conn, current_user["id"], payload.name, payload.persona, payload.topic)
    return BotResponse(**row)


@app.patch("/bots/{bot_id}", response_model=BotResponse)
def patch_bot(
    bot_id: int,
    payload: BotUpdateRequest,
    current_user: dict = Depends(get_current_user),
    conn: psycopg.Connection = Depends(get_db),
) -> BotResponse:
    row = bot_service.update_bot(conn, bot_id, current_user["id"], payload.model_dump())
    if not row:
        raise HTTPException(status_code=404, detail="봇을 찾을 수 없습니다.")
    return BotResponse(**row)


@app.delete("/bots/{bot_id}", status_code=204)
def remove_bot(
    bot_id: int,
    current_user: dict = Depends(get_current_user),
    conn: psycopg.Connection = Depends(get_db),
) -> Response:
    deleted = bot_service.delete_bot(conn, bot_id, current_user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="봇을 찾을 수 없습니다.")
    return Response(status_code=204)


@app.get("/bots/{bot_id}/jobs", response_model=list[BotJobResponse])
def get_bot_jobs(
    bot_id: int,
    current_user: dict = Depends(get_current_user),
    conn: psycopg.Connection = Depends(get_db),
) -> list[BotJobResponse]:
    rows = bot_service.list_bot_jobs(conn, bot_id, current_user["id"])
    return [BotJobResponse(**row) for row in rows]


@app.get("/activity-logs", response_model=list[ActivityLogResponse])
def get_activity_logs(
    limit: int = Query(default=30, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    conn: psycopg.Connection = Depends(get_db),
) -> list[ActivityLogResponse]:
    rows = bot_service.list_activity_logs(conn, current_user["id"], limit=limit)
    return [ActivityLogResponse(**row) for row in rows]
