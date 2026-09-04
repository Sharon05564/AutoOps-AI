import uuid
from datetime import datetime

from app.models.enums import DeploymentStatus
from app.schemas.common import ORMModel


class DeploymentRead(ORMModel):
    id: uuid.UUID
    service_id: uuid.UUID
    version: str
    status: DeploymentStatus
    is_bad_deployment: bool
    deployed_at: datetime
    rolled_back_at: datetime | None
    rolled_back_from_id: uuid.UUID | None
