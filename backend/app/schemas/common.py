from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Base for schemas that read directly from SQLAlchemy ORM objects."""

    model_config = ConfigDict(from_attributes=True)
