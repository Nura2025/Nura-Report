from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from os import getenv
from dotenv import load_dotenv
from sqlalchemy.ext.declarative import declarative_base


load_dotenv()


# Create async engine
engine = create_async_engine("postgresql+asyncpg://adhd_user:1234@localhost/adhd_therapy", echo=True)

# Create session factory
async_session = sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)

# Dependency to get DB session
async def get_db():
    async with async_session() as session:
        yield session


Base = declarative_base()
