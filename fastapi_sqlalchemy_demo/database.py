# database.py
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# URL de conexión SQLite usando aiosqlite para operaciones asíncronas
DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Creación del motor asíncrono
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# Fábrica de sesiones asíncronas
AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# Base declarativa moderna para los modelos ORM
class Base(DeclarativeBase):
    pass

# Dependencia de FastAPI para obtener la sesión de base de datos por solicitud
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()