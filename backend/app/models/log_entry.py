import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import LogLevel
from app.models.mixins import UUIDPrimaryKeyMixin


class LogEntry(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "log_entries"

    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id"), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    level: Mapped[LogLevel] = mapped_column(
        Enum(LogLevel, native_enum=False, length=20), nullable=False, index=True
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(100), default="app", nullable=False)

    service: Mapped["Service"] = relationship(back_populates="log_entries")
