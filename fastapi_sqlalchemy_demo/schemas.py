# schemas.py
from pydantic import BaseModel, ConfigDict

class TaskCreate(BaseModel):
    title: str
    description: str | None = None

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None
    completed: bool
    archived: bool

    model_config = ConfigDict(from_attributes=True)