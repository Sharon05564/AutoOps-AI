import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import IncidentStatus, Severity
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.investigation import Investigation
    from app.models.postmortem import Postmortem
    from app.models.remediation_action import RemediationAction
    from app.models.service import Service
    from app.models.verification import Verification


class Incident(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "incidents"

    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    severity: Mapped[Severity] = mapped_column(
        Enum(Severity, native_enum=False, length=20), nullable=False
    )
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus, native_enum=False, length=30),
        default=IncidentStatus.DETECTED,
        nullable=False,
        index=True,
    )
    triggering_deployment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deployments.id"), nullable=True
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    service: Mapped["Service"] = relationship(back_populates="incidents")
    alerts: Mapped[list["Alert"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )
    investigations: Mapped[list["Investigation"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )
    remediation_actions: Mapped[list["RemediationAction"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )
    verifications: Mapped[list["Verification"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )
    postmortem: Mapped["Postmortem | None"] = relationship(
        back_populates="incident", cascade="all, delete-orphan", uselist=False
    )
