import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import UUIDPrimaryKeyMixin


class Approval(Base, UUIDPrimaryKeyMixin):
    """Records who (or what) approved or rejected a remediation action, and why."""

    __tablename__ = "approvals"

    remediation_action_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("remediation_actions.id"),
        nullable=False,
        unique=True,
    )
    approved: Mapped[bool] = mapped_column(Boolean, nullable=False)
    approved_by: Mapped[str] = mapped_column(String(200), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    remediation_action: Mapped["RemediationAction"] = relationship(back_populates="approval")
