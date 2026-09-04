import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.investigation import Investigation


class AgentToolCall(Base, UUIDPrimaryKeyMixin):
    """Audit record of a single tool invocation made by the investigation agent."""

    __tablename__ = "agent_tool_calls"

    investigation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("investigations.id"), nullable=False, index=True
    )
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    arguments: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    result: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    called_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    investigation: Mapped["Investigation"] = relationship(back_populates="tool_calls")
