import logging

from aiogram import BaseMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.infrastructure.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class UserActivityMiddleware(BaseMiddleware):
    def __init__(self):
        self.user_repository = UserRepository()

    async def __call__(self, handler, event, data):
        sessionmaker = data.get("sessionmaker")
        user = data.get("event_from_user")
        if sessionmaker and user:
            async with sessionmaker() as session:
                try:
                    await self.user_repository.touch_user(
                        session,
                        user.id,
                        username=user.username,
                        first_name=user.first_name,
                    )
                except SQLAlchemyError:
                    # Do not break update handling if activity tracking fails.
                    logger.exception("Failed to touch user activity")
        return await handler(event, data)
