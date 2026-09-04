import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import VerificationStatus
from app.models.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.incident import Incident


class Verification(Base, UUIDPrimaryKeyMixin):
    """Post-remediation check confirming whether the service actually recovered."""

    __tablename__ = "verifications"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False, index=True
    )
    remediation_action_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("remediation_actions.id"), nullable=False
    )
    status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, native_enum=False, length=20), nullable=False
    )
    metrics_before: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    metrics_after: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    incident: Mapped["Incident"] = relationship(back_populates="verifications")
