from datetime import timedelta

from app.infrastructure.repositories.user_repository import UserRepository

PERIODS = {
    "day": timedelta(days=1),
    "week": timedelta(days=7),
    "month": timedelta(days=30),
}


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

    async def get_users_page(self, session, period, page=1, page_size=10):
        since = PERIODS.get(period)
        if since is None:
            raise ValueError(f"Unknown period: {period}")

        safe_page = max(1, int(page))
        safe_page_size = max(1, int(page_size))
        total = await self.user_repository.count_active_since(session, since)
        total_pages = max(1, (total + safe_page_size - 1) // safe_page_size)
        safe_page = min(safe_page, total_pages)
        offset = (safe_page - 1) * safe_page_size
        users = await self.user_repository.list_active_since(
            session,
            since=since,
            limit=safe_page_size,
            offset=offset,
        )
        return {
            "users": users,
            "total": total,
            "page": safe_page,
            "total_pages": total_pages,
            "period": period,
        }
