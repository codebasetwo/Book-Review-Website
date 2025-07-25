from sqlmodel import create_engine, text, SQLModel
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession 
from src.config import Config

async_engine = AsyncEngine(
    create_engine(
    url=Config.DATABASE_URL,
    echo=True,
))


async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        # statement = text("SELECT 'Hello';")

        # result = await conn.execute(statement)
        # print(result.all())


async def get_session() -> AsyncSession:
    Session = sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with Session() as session:
        yield session