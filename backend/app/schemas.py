"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Health ──

class HealthResponse(BaseModel):
    status: str
    version: str


# ── Credentials ──

class CredentialCreate(BaseModel):
    provider: str = Field(..., pattern="^(openai|claude|deepseek|glm)$")
    api_key: str = Field(..., min_length=1)
    alias: str = Field(default="", max_length=100)


class CredentialUpdate(BaseModel):
    api_key: Optional[str] = None
    alias: Optional[str] = None
    is_active: Optional[bool] = None


class CredentialResponse(BaseModel):
    id: int
    provider: str
    alias: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CredentialWithLatest(CredentialResponse):
    """Credential + latest snapshot (used by Dashboard)."""
    total_credits: Optional[float] = None
    used_credits: Optional[float] = None
    remaining_credits: Optional[float] = None
    currency: Optional[str] = None
    last_fetched_at: Optional[datetime] = None


# ── Usage ──

class UsageSnapshotResponse(BaseModel):
    id: int
    credential_id: int
    total_credits: float
    used_credits: float
    remaining_credits: float
    currency: str
    fetched_at: datetime

    class Config:
        from_attributes = True


class MetricsResponse(BaseModel):
    credential_id: int
    remaining_credits: float
    currency: str
    avg_24h: Optional[float] = None
    avg_7d: Optional[float] = None
    predicted_exhaustion_days: Optional[float] = None
    predicted_exhaustion_date: Optional[str] = None
    status: str  # "insufficient_data" | "ok"


# ── Notification Channels ──

class ChannelCreate(BaseModel):
    channel_type: str = Field(..., pattern="^(email|telegram|feishu|wecom)$")
    config_json: str = Field(default="{}")
    enabled: bool = True


class ChannelUpdate(BaseModel):
    config_json: Optional[str] = None
    enabled: Optional[bool] = None


class ChannelResponse(BaseModel):
    id: int
    channel_type: str
    config_json: str
    enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Manual Balance ──

class ManualBalanceRequest(BaseModel):
    balance: float


class ManualBalanceResponse(BaseModel):
    status: str
    snapshot_id: int
    remaining_credits: float
    currency: str
    fetched_at: str


# ── Settings ──

class SettingUpdate(BaseModel):
    value: str


class SettingsResponse(BaseModel):
    sync_interval_minutes: str
    data_retention_days: str
