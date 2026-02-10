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
            try:
                async with sessionmaker() as session:
                    await self.user_repository.touch_user(session, user.id)
            except SQLAlchemyError:
                # Do not fail the whole update flow if activity ping fails.
                logger.warning("Failed to update user activity", exc_info=True)
        return await handler(event, data)
