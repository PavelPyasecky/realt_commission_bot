from contextlib import asynccontextmanager


@asynccontextmanager
async def managed_session(sessionmaker):
    async with sessionmaker() as session:
        try:
            yield session
            await session.commit()
        except BaseException:
            await session.rollback()
            raise
