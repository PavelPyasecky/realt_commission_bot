from aiogram import BaseMiddleware

from app.infrastructure.repositories.user_repository import UserRepository


class UserActivityMiddleware(BaseMiddleware):
    def __init__(self):
        self.user_repository = UserRepository()

    async def __call__(self, handler, event, data):
        sessionmaker = data.get("sessionmaker")
        user = data.get("event_from_user")
        if sessionmaker and user:
            async with sessionmaker() as session:
                await self.user_repository.touch_user(session, user.id)
        return await handler(event, data)
