import asyncio
import os

from fastapi import Depends, FastAPI, HTTPException, Query, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import psycopg

from app.db import get_connection, get_db, init_db
from app.deps import get_current_user
from app.realtime import activity_log_poller, manager
from app.schemas import (
    ActivityLogResponse,
    AIModelListRequest,
    AIModelListResponse,
    BotCreateRequest,
    BotJobResponse,
    BotResponse,
    BotUpdateRequest,
    CommentDepthSettingResponse,
    CommentDepthSettingUpdateRequest,
    LoginRequest,
    LoginResponse,
    MeResponse,
    SnsCommentCreateRequest,
    SnsCommentResponse,
    SnsCommentUpdateRequest,
    SnsPostCreateRequest,
    SnsPostResponse,
    SnsPostUpdateRequest,
)
from app.security import decode_access_token
from app.services import ai_model_service, auth_service, bot_service, settings_service, sns_service

app = FastAPI(title="hams-api", version="0.7.0")


def _parse_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return origins or ["http://localhost:3000"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    init_db()
    with get_connection() as conn:
        auth_service.ensure_default_user(conn)

    app.state.stop_event = asyncio.Event()
    app.state.poller_task = asyncio.create_task(activity_log_poller(app.state.stop_event))


@app.on_event("shutdown")
async def on_shutdown() -> None:
    app.state.stop_event.set()
    app.state.poller_task.cancel()
    try:
        await app.state.poller_task
    except asyncio.CancelledError:
        pass


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




@app.get("/settings/comment-depth", response_model=CommentDepthSettingResponse)
def get_comment_depth_setting(
    current_user: dict = Depends(get_current_user),
    conn: psycopg.Connection = Depends(get_db),
) -> CommentDepthSettingResponse:
    _ = current_user
    value = settings_service.get_max_comment_depth(conn)
    return CommentDepthSettingResponse(max_comment_depth=value)


@app.patch("/settings/comment-depth", response_model=CommentDepthSettingResponse)
def patch_comment_depth_setting(
    payload: CommentDepthSettingUpdateRequest,
    current_user: dict = Depends(get_current_user),
    conn: psycopg.Connection = Depends(get_db),
) -> CommentDepthSettingResponse:
    _ = current_user
    value = settings_service.set_max_comment_depth(conn, payload.max_comment_depth)
    return CommentDepthSettingResponse(max_comment_depth=value)


@app.get("/bots", response_model=list[BotResponse])
def get_bots(
    current_user: dict = Depends(get_current_user),
    conn: psycopg.Connection = Depends(get_db),
) -> list[BotResponse]:
    rows = bot_service.list_bots(conn, current_user["id"])
    return [BotResponse(**row) for row in rows]


@app.post("/ai/models", response_model=AIModelListResponse)
def get_ai_models(payload: AIModelListRequest) -> AIModelListResponse:
    try:
        models = ai_model_service.list_models(payload.ai_provider, payload.api_key)
    except ai_model_service.AIModelServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not models:
        raise HTTPException(status_code=400, detail="조회 가능한 모델이 없습니다.")
    return AIModelListResponse(models=models)


@app.post("/bots", response_model=BotResponse, status_code=201)
def create_bot(
    payload: BotCreateRequest,
    current_user: dict = Depends(get_current_user),
    conn: psycopg.Connection = Depends(get_db),
) -> BotResponse:
    try:
        row = bot_service.create_bot(
            conn,
            current_user["id"],
            payload.name,
            payload.persona,
            payload.topic,
            payload.ai_provider,
            payload.api_key,
            payload.ai_model,
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = 400 if detail in {"유효하지 않은 봇입니다.", "글 작성은 하루에 한 번만 가능합니다."} else 404
        raise HTTPException(status_code=status_code, detail=detail) from exc
    return BotResponse(**row)


@app.patch("/bots/{bot_id}", response_model=BotResponse)
def patch_bot(
    bot_id: int,
    payload: BotUpdateRequest,
    current_user: dict = Depends(get_current_user),
    conn: psycopg.Connection = Depends(get_db),
) -> BotResponse:
    try:
        row = bot_service.update_bot(conn, bot_id, current_user["id"], payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
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


@app.get("/sns/posts", response_model=list[SnsPostResponse])
def get_sns_posts(
    current_user: dict = Depends(get_current_user),
    conn: psycopg.Connection = Depends(get_db),
) -> list[SnsPostResponse]:
    rows = sns_service.list_public_posts(conn)
    for row in rows:
        row["can_edit"] = row["user_id"] == current_user["id"]
    return [SnsPostResponse(**row) for row in rows]


@app.get("/sns/posts/{post_id}", response_model=SnsPostResponse)
def get_sns_post(
    post_id: int,
    current_user: dict = Depends(get_current_user),
    conn: psycopg.Connection = Depends(get_db),
) -> SnsPostResponse:
    row = sns_service.get_post_by_id(conn, post_id)
    if not row:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    row["can_edit"] = row["user_id"] == current_user["id"]
    return SnsPostResponse(**row)


@app.post("/sns/posts", response_model=SnsPostResponse, status_code=201)
def create_sns_post(
    payload: SnsPostCreateRequest,
    current_user: dict = Depends(get_current_user),
    conn: psycopg.Connection = Depends(get_db),
) -> SnsPostResponse:
    try:
        row = sns_service.create_post(
            conn,
            current_user["id"],
            payload.category,
            payload.title,
            payload.content,
            payload.is_anonymous,
            payload.bot_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    row["bot_name"] = None
    row["comment_count"] = 0
    row["can_edit"] = True
    if row["bot_id"]:
        bot = bot_service.get_bot(conn, row["bot_id"], current_user["id"])
        row["bot_name"] = bot["name"] if bot else None
    return SnsPostResponse(**row)


@app.patch("/sns/posts/{post_id}", response_model=SnsPostResponse)
def patch_sns_post(
    post_id: int,
    payload: SnsPostUpdateRequest,
    current_user: dict = Depends(get_current_user),
    conn: psycopg.Connection = Depends(get_db),
) -> SnsPostResponse:
    try:
        row = sns_service.update_post(conn, post_id, current_user["id"], payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not row:
        raise HTTPException(status_code=403, detail="본인이 작성한 게시글만 수정할 수 있습니다.")

    row["bot_name"] = None
    row["comment_count"] = len(sns_service.list_comments(conn, post_id))
    row["can_edit"] = True
    if row["bot_id"]:
        bot = bot_service.get_bot(conn, row["bot_id"], current_user["id"])
        row["bot_name"] = bot["name"] if bot else None
    return SnsPostResponse(**row)


@app.delete("/sns/posts/{post_id}", status_code=204)
def remove_sns_post(
    post_id: int,
    current_user: dict = Depends(get_current_user),
    conn: psycopg.Connection = Depends(get_db),
) -> Response:
    deleted = sns_service.delete_post(conn, post_id, current_user["id"])
    if not deleted:
        raise HTTPException(status_code=403, detail="본인이 작성한 게시글만 삭제할 수 있습니다.")
    return Response(status_code=204)


@app.get("/sns/posts/{post_id}/comments", response_model=list[SnsCommentResponse])
def get_sns_comments(
    post_id: int,
    current_user: dict = Depends(get_current_user),
    conn: psycopg.Connection = Depends(get_db),
) -> list[SnsCommentResponse]:
    if not sns_service.get_post_by_id(conn, post_id):
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    rows = sns_service.list_comments(conn, post_id)
    for row in rows:
        row["can_edit"] = row["user_id"] == current_user["id"]
        row["bot_name"] = row.get("bot_name")
    return [SnsCommentResponse(**row) for row in rows]


@app.post("/sns/posts/{post_id}/comments", response_model=SnsCommentResponse, status_code=201)
def create_sns_comment(
    post_id: int,
    payload: SnsCommentCreateRequest,
    current_user: dict = Depends(get_current_user),
    conn: psycopg.Connection = Depends(get_db),
) -> SnsCommentResponse:
    try:
        row = sns_service.create_comment(
            conn,
            post_id,
            current_user["id"],
            payload.content,
            payload.bot_id,
            payload.parent_comment_id,
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = 400 if detail in {"유효하지 않은 봇입니다.", "대댓글 대상 댓글을 찾을 수 없습니다."} or detail.startswith("댓글 최대 depth는") else 404
        raise HTTPException(status_code=status_code, detail=detail) from exc
    row["can_edit"] = True
    row["bot_name"] = None
    if row["bot_id"]:
        bot = bot_service.get_bot(conn, row["bot_id"], current_user["id"])
        row["bot_name"] = bot["name"] if bot else None
    return SnsCommentResponse(**row)


@app.patch("/sns/comments/{comment_id}", response_model=SnsCommentResponse)
def patch_sns_comment(
    comment_id: int,
    payload: SnsCommentUpdateRequest,
    current_user: dict = Depends(get_current_user),
    conn: psycopg.Connection = Depends(get_db),
) -> SnsCommentResponse:
    row = sns_service.update_comment(conn, comment_id, current_user["id"], payload.content)
    if not row:
        raise HTTPException(status_code=403, detail="본인이 작성한 댓글만 수정할 수 있습니다.")
    row["can_edit"] = True
    row["bot_name"] = None
    if row["bot_id"]:
        bot = bot_service.get_bot(conn, row["bot_id"], current_user["id"])
        row["bot_name"] = bot["name"] if bot else None
    return SnsCommentResponse(**row)


@app.delete("/sns/comments/{comment_id}", status_code=204)
def remove_sns_comment(
    comment_id: int,
    current_user: dict = Depends(get_current_user),
    conn: psycopg.Connection = Depends(get_db),
) -> Response:
    deleted = sns_service.delete_comment(conn, comment_id, current_user["id"])
    if not deleted:
        raise HTTPException(status_code=403, detail="본인이 작성한 댓글만 삭제할 수 있습니다.")
    return Response(status_code=204)


@app.websocket("/ws/activity")
async def ws_activity(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="token is required")
        return

    try:
        payload = decode_access_token(token)
    except ValueError:
        await websocket.close(code=1008, reason="invalid token")
        return

    user_id = int(payload["sub"])
    with get_connection() as conn:
        user = auth_service.get_user_by_id(conn, user_id)
    if not user:
        await websocket.close(code=1008, reason="user not found")
        return

    await manager.connect(user_id, websocket)
    await websocket.send_json({"type": "connected", "data": {"user_id": user_id}})

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(user_id, websocket)
