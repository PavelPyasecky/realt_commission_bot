import httpx
import redis.asyncio as redis

from app.core.config import config


class CurrencyService:
    async def _fetch_usd_rate_from_api(self):
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("https://api.nbrb.by/exrates/rates/431")
            response.raise_for_status()
            data = response.json()
            return float(data["Cur_OfficialRate"])

    async def get_dollar_rate_for_today(self):
        client = redis.from_url(str(config.REDIS_URL))
        try:
            value = await client.get("currency:usd")
            if value is not None:
                return float(value)
        finally:
            await client.aclose()

        # Fallback: allow calculations even when Celery/Redis cache is unavailable.
        rate = await self._fetch_usd_rate_from_api()
        client = redis.from_url(str(config.REDIS_URL))
        try:
            await client.set("currency:usd", rate, ex=60 * 60 * 12)
        finally:
            await client.aclose()
        return rate
