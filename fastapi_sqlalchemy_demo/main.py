# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import engine, Base, get_db, AsyncSessionLocal
from models import TaskModel, UserModel
from schemas import TaskCreate, TaskResponse

SINGLE_USER_ID = 1

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Sembrar el usuario único si todavía no existe
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(UserModel).where(UserModel.id == SINGLE_USER_ID))
        if not result.scalars().first():
            session.add(UserModel(id=SINGLE_USER_ID, username="usuario"))
            await session.commit()
    yield

app = FastAPI(
    title="FastAPI con SQLAlchemy 2.0",
    description="Gestor de tareas de usuario único",
    version="1.1.0",
    lifespan=lifespan
)

async def get_task_or_404(task_id: int, db: AsyncSession) -> TaskModel:
    result = await db.execute(select(TaskModel).where(TaskModel.id == task_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")
    return task

# 2. Alta de tarea
@app.post("/tasks/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate, db: AsyncSession = Depends(get_db)):
    db_task = TaskModel(
        title=task.title,
        description=task.description,
        user_id=SINGLE_USER_ID,
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task

# Listar tareas (por defecto oculta las archivadas)
@app.get("/tasks/", response_model=list[TaskResponse])
async def read_tasks(
    skip: int = 0,
    limit: int = 10,
    include_archived: bool = False,
    db: AsyncSession = Depends(get_db),
):
    query = select(TaskModel)
    if not include_archived:
        query = query.where(TaskModel.archived == False)  # noqa: E712
    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())

@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def read_task(task_id: int, db: AsyncSession = Depends(get_db)):
    return await get_task_or_404(task_id, db)

@app.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, task_data: TaskCreate, db: AsyncSession = Depends(get_db)):
    task = await get_task_or_404(task_id, db)
    task.title = task_data.title
    task.description = task_data.description
    await db.commit()
    await db.refresh(task)
    return task

# 3. Marcar como terminada
@app.patch("/tasks/{task_id}/complete", response_model=TaskResponse)
async def complete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await get_task_or_404(task_id, db)
    task.completed = True
    await db.commit()
    await db.refresh(task)
    return task

# 4. Archivar (solo si está terminada)
@app.patch("/tasks/{task_id}/archive", response_model=TaskResponse)
async def archive_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await get_task_or_404(task_id, db)
    if not task.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden archivar tareas terminadas",
        )
    task.archived = True
    await db.commit()
    await db.refresh(task)
    return task

# Desarchivar
@app.patch("/tasks/{task_id}/unarchive", response_model=TaskResponse)
async def unarchive_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await get_task_or_404(task_id, db)
    task.archived = False
    await db.commit()
    await db.refresh(task)
    return task

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await get_task_or_404(task_id, db)
    await db.delete(task)
    await db.commit()
    return None