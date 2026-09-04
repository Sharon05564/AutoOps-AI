import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Service(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "services"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    replicas: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    active_deployment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deployments.id", use_alter=True, name="fk_services_active_deployment"),
        nullable=True,
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    incidents: Mapped[list["Incident"]] = relationship(
        back_populates="service", cascade="all, delete-orphan"
    )
    deployments: Mapped[list["Deployment"]] = relationship(
        back_populates="service",
        cascade="all, delete-orphan",
        foreign_keys="Deployment.service_id",
    )
    metric_snapshots: Mapped[list["MetricSnapshot"]] = relationship(
        back_populates="service", cascade="all, delete-orphan"
    )
    log_entries: Mapped[list["LogEntry"]] = relationship(
        back_populates="service", cascade="all, delete-orphan"
    )
