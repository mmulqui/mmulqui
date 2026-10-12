# schemas.py
from pydantic import BaseModel, ConfigDict

class TaskBase(BaseModel):
    title: str
    description: str | None = None
    completed: bool = False

class TaskCreate(TaskBase):
    pass

class TaskResponse(TaskBase):
    id: int

    # Configuración para permitir la lectura de modelos ORM directamente (equivalente a orm_mode en v1)
    model_config = ConfigDict(from_attributes=True)