from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.infrastructure.database.models import User


class UserRepository:
    async def touch_user(self, session, tg_id):
        now = datetime.utcnow()
        stmt = (
            insert(User)
            .values(tg_id=tg_id, created_at=now, last_seen=now)
            .on_conflict_do_update(
                index_elements=[User.tg_id],
                set_={"last_seen": now},
            )
        )
        await session.execute(stmt)
        await session.commit()

    async def count_total(self, session):
        result = await session.execute(select(func.count(User.tg_id)))
        return int(result.scalar_one())

    async def count_active_since(self, session, since):
        since_dt = datetime.utcnow() - since
        stmt = select(func.count(User.tg_id)).where(User.last_seen >= since_dt)
        result = await session.execute(stmt)
        return int(result.scalar_one())
