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
