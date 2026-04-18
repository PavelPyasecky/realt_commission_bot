from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import config


def create_engine():
    return create_async_engine(
        str(config.DB_DSN),
        echo=False,
        pool_pre_ping=True,
        pool_recycle=1800,
    )


def create_sessionmaker(engine):
    return async_sessionmaker(engine, expire_on_commit=False)
