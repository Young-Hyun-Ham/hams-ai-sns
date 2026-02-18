from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(..., examples=["owner@hams.local"])
    password: str = Field(..., examples=["hams1234"])


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: int
    email: str
    nickname: str


class BotCreateRequest(BaseModel):
    name: str
    persona: str
    topic: str


class BotUpdateRequest(BaseModel):
    name: str | None = None
    persona: str | None = None
    topic: str | None = None
    is_active: bool | None = None


class BotResponse(BaseModel):
    id: int
    user_id: int
    name: str
    persona: str
    topic: str
    is_active: bool


class BotJobResponse(BaseModel):
    id: int
    bot_id: int
    job_type: str
    payload: dict
    interval_seconds: int
    next_run_at: datetime
    status: str
    retry_count: int
    max_retries: int
    last_error: str | None


class ActivityLogResponse(BaseModel):
    id: int
    bot_id: int
    job_id: int
    job_type: str
    result_status: str
    message: str
    executed_at: datetime


class SnsPostCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    is_anonymous: bool = True
    bot_id: int | None = None


class SnsPostUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1)
    is_anonymous: bool | None = None
    bot_id: int | None = None


class SnsPostResponse(BaseModel):
    id: int
    user_id: int
    bot_id: int | None
    bot_name: str | None = None
    title: str
    content: str
    is_anonymous: bool
    created_at: datetime
    updated_at: datetime
