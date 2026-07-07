from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from gbot.config import DATABASE_URL
from gbot.database.models import Base

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
