from pydantic import BaseModel

from app.models.enums import ActionType


class Diagnosis(BaseModel):
    root_cause: str
    confidence: float
    summary: str
    recommended_action: ActionType | None
    evidence: list[str]


class PostmortemNarrative(BaseModel):
    summary: str
    prevention_recommendations: list[str]
