import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ActionType, RemediationStatus, RiskLevel
from app.models.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.approval import Approval
    from app.models.incident import Incident


class RemediationAction(Base, UUIDPrimaryKeyMixin):
    """A proposed or executed mutating action, gated by the safety/approval policy."""

    __tablename__ = "remediation_actions"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False, index=True
    )
    action_type: Mapped[ActionType] = mapped_column(
        Enum(ActionType, native_enum=False, length=30), nullable=False
    )
    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel, native_enum=False, length=10), nullable=False
    )
    status: Mapped[RemediationStatus] = mapped_column(
        Enum(RemediationStatus, native_enum=False, length=20),
        default=RemediationStatus.PENDING_APPROVAL,
        nullable=False,
        index=True,
    )
    parameters: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    result: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    incident: Mapped["Incident"] = relationship(back_populates="remediation_actions")
    approval: Mapped["Approval | None"] = relationship(
        back_populates="remediation_action", cascade="all, delete-orphan", uselist=False
    )
