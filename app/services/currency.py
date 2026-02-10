import httpx
import redis.asyncio as redis

from app.core.config import config
from app.services.exceptions import CurrencyUnavailableError


class CurrencyService:
    async def get_dollar_rate_for_today(self):
        client = redis.from_url(str(config.REDIS_URL))
        try:
            try:
                value = await client.get("currency:usd")
                if value is not None:
                    return float(value)
            except Exception:
                # Redis is an optimization layer, fallback to API if unavailable.
                pass

            rate = await self._fetch_usd_rate()
            try:
                await client.set("currency:usd", rate)
            except Exception:
                # Best effort caching.
                pass
            return rate
        except Exception as exc:
            raise CurrencyUnavailableError(
                "USD rate is not available from cache or API."
            ) from exc
        finally:
            await client.aclose()
            await client.connection_pool.disconnect()

    async def _fetch_usd_rate(self):
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            response = await http_client.get("https://api.nbrb.by/exrates/rates/431")
            response.raise_for_status()
            data = response.json()
            return float(data["Cur_OfficialRate"])
