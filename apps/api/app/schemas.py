from typing import Literal
from datetime import datetime

from pydantic import BaseModel, Field

AIProviderType = Literal["mock", "gpt", "gemini", "claude"]


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
    ai_provider: AIProviderType = "mock"
    api_key: str = ""
    ai_model: str = "mock-v1"


class BotUpdateRequest(BaseModel):
    name: str | None = None
    persona: str | None = None
    topic: str | None = None
    is_active: bool | None = None
    ai_provider: AIProviderType | None = None
    api_key: str | None = None
    ai_model: str | None = None


class BotResponse(BaseModel):
    id: int
    user_id: int
    name: str
    persona: str
    topic: str
    ai_provider: AIProviderType
    ai_model: str
    has_api_key: bool
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
    category: Literal["경제", "문화", "연예", "유머"] = "경제"
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    is_anonymous: bool = True
    bot_id: int | None = None


class SnsPostUpdateRequest(BaseModel):
    category: Literal["경제", "문화", "연예", "유머"] | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1)
    is_anonymous: bool | None = None
    bot_id: int | None = None


class SnsPostResponse(BaseModel):
    id: int
    user_id: int
    bot_id: int | None
    bot_name: str | None = None
    category: Literal["경제", "문화", "연예", "유머"] = "경제"
    title: str
    content: str
    is_anonymous: bool
    created_at: datetime
    updated_at: datetime
    comment_count: int
    can_edit: bool = False


class SnsCommentCreateRequest(BaseModel):
    content: str = Field(..., min_length=1)
    bot_id: int | None = None


class SnsCommentUpdateRequest(BaseModel):
    content: str = Field(..., min_length=1)


class SnsCommentResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    bot_id: int | None = None
    bot_name: str | None = None
    content: str
    created_at: datetime
    updated_at: datetime
    can_edit: bool = False


class AIModelListRequest(BaseModel):
    ai_provider: AIProviderType
    api_key: str = Field(..., min_length=1)


class AIModelListResponse(BaseModel):
    models: list[str]
