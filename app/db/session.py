from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
)

SessionLocal = async_sessionmaker(bind=engine,
                                  class_=AsyncEngine,
                                  expire_on_commit=False,
                                  autoflush=False,
                                  )


async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
