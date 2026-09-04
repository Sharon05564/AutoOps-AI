import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class ApprovalRead(ORMModel):
    id: uuid.UUID
    remediation_action_id: uuid.UUID
    approved: bool
    approved_by: str
    reason: str
    decided_at: datetime


class ApprovalCreate(BaseModel):
    approved: bool
    approved_by: str
    reason: str = ""
