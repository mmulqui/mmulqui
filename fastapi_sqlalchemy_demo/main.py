import time# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import engine, Base, get_db
from models import TaskModel
from schemas import TaskCreate, TaskResponse

# Evento de inicio para crear las tablas automáticamente
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title="FastAPI con SQLAlchemy 2.0",
    description="Ejemplo práctico de integración asíncrona",
    version="1.0.0",
    lifespan=lifespan
)

# 1. Crear una Tarea (CREATE)
@app.post("/tasks/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate, db: AsyncSession = Depends(get_db)):
    db_task = TaskModel(
        title=task.title,
        description=task.description,
        completed=task.completed
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task

# 2. Listar Tareas (READ - List)
@app.get("/tasks/", response_model=list[TaskResponse])
async def read_tasks(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskModel).offset(skip).limit(limit))
    tasks = result.scalars().all()
    return list(tasks)

# 3. Obtener una Tarea por ID (READ - Detail)
@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def read_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskModel).where(TaskModel.id == task_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")
    return task

# 4. Actualizar una Tarea (UPDATE)
@app.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, task_data: TaskCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskModel).where(TaskModel.id == task_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")
    
    task.title = task_data.title
    task.description = task_data.description
    task.completed = task_data.completed
    
    await db.commit()
    await db.refresh(task)
    return task

# 5. Eliminar una Tarea (DELETE)
@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskModel).where(TaskModel.id == task_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")
    
    await db.delete(task)
    await db.commit()
    return None