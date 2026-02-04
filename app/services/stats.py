from datetime import timedelta

from app.infrastructure.repositories.user_repository import UserRepository


class StatsService:
    def __init__(self, user_repository=None):
        self.user_repository = user_repository or UserRepository()

    async def get_stats(self, session):
        return {
            "dau": await self.user_repository.count_active_since(
                session, timedelta(days=1)
            ),
            "wau": await self.user_repository.count_active_since(
                session, timedelta(days=7)
            ),
            "mau": await self.user_repository.count_active_since(
                session, timedelta(days=30)
            ),
            "total": await self.user_repository.count_total(session),
        }
