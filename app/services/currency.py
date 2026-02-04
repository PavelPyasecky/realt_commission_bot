import redis.asyncio as redis

from app.core.config import config


class CurrencyService:
    async def get_dollar_rate_for_today(self):
        client = redis.from_url(str(config.REDIS_URL))
        value = await client.get("currency:usd")
        if value is None:
            raise RuntimeError("USD rate is not available in Redis.")
        return float(value)
