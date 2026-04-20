import redis.asyncio as redis

from app.core.config import config
from app.infrastructure.redis_values import redis_float


class UserPreferencesService:
    def _last_key(self, user_id):
        return f"user:{user_id}:last_amount"

    def _favorites_key(self, user_id):
        return f"user:{user_id}:favorites"

    async def save_last_amount(self, user_id, amount):
        client = redis.from_url(str(config.REDIS_URL))
        try:
            await client.set(self._last_key(user_id), amount)
        finally:
            await client.aclose()

    async def get_last_amount(self, user_id):
        client = redis.from_url(str(config.REDIS_URL))
        try:
            value = await client.get(self._last_key(user_id))
            if value is None:
                return None
            return redis_float(value)
        finally:
            await client.aclose()

    async def add_favorite_amount(self, user_id, amount):
        client = redis.from_url(str(config.REDIS_URL))
        try:
            await client.sadd(self._favorites_key(user_id), amount)
        finally:
            await client.aclose()

    async def get_favorite_amounts(self, user_id):
        client = redis.from_url(str(config.REDIS_URL))
        try:
            values = await client.smembers(self._favorites_key(user_id))
            parsed = [redis_float(value) for value in values]
            return sorted(parsed)
        finally:
            await client.aclose()

