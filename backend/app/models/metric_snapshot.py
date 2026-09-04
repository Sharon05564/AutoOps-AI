import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import UUIDPrimaryKeyMixin


class MetricSnapshot(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "metric_snapshots"

    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id"), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    request_count: Mapped[int] = mapped_column(Integer, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False)
    error_rate: Mapped[float] = mapped_column(Float, nullable=False)
    latency_p50_ms: Mapped[float] = mapped_column(Float, nullable=False)
    latency_p95_ms: Mapped[float] = mapped_column(Float, nullable=False)
    latency_p99_ms: Mapped[float] = mapped_column(Float, nullable=False)

    service: Mapped["Service"] = relationship(back_populates="metric_snapshots")
