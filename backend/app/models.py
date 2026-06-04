"""SQLAlchemy models — 5 tables for API Sentinel."""
from datetime import datetime

from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow():
    return datetime.utcnow()


class ApiCredential(Base):
    __tablename__ = "api_credentials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(20), nullable=False, index=True)
    api_key = Column(Text, nullable=False)          # Fernet-encrypted
    alias = Column(String(100), nullable=False, default="")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    snapshots = relationship("UsageSnapshot", back_populates="credential",
                             cascade="all, delete-orphan")


class UsageSnapshot(Base):
    __tablename__ = "usage_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    credential_id = Column(Integer, ForeignKey("api_credentials.id",
                            ondelete="CASCADE"), nullable=False, index=True)
    total_credits = Column(Float, default=0.0, nullable=False)
    used_credits = Column(Float, default=0.0, nullable=False)
    remaining_credits = Column(Float, default=0.0, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    fetched_at = Column(DateTime, default=utcnow, nullable=False, index=True)

    credential = relationship("ApiCredential", back_populates="snapshots")


class NotificationChannel(Base):
    __tablename__ = "notification_channels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_type = Column(String(20), nullable=False)  # email / telegram / feishu / wecom
    config_json = Column(Text, nullable=False, default="{}")
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(Integer, ForeignKey("notification_channels.id",
                         ondelete="CASCADE"), nullable=False, index=True)
    credential_id = Column(Integer, ForeignKey("api_credentials.id",
                           ondelete="CASCADE"), nullable=False, index=True)
    alert_level = Column(Integer, nullable=False)   # 1, 2, 3
    message = Column(Text, nullable=False, default="")
    sent_at = Column(DateTime, default=utcnow, nullable=False)


class Setting(Base):
    __tablename__ = "settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False, default="")
