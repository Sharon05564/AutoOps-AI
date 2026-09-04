import uuid
from datetime import datetime

from app.models.enums import LogLevel
from app.schemas.common import ORMModel


class LogEntryRead(ORMModel):
    id: uuid.UUID
    service_id: uuid.UUID
    timestamp: datetime
    level: LogLevel
    message: str
    source: str
