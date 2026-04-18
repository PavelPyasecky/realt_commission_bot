import httpx
import redis

from app.celery_app import celery_app
from app.core.config import config


@celery_app.task(name="app.tasks.currency.update_usd_rate")
def update_usd_rate():
    response = httpx.get(
        "https://api.nbrb.by/exrates/rates/431",
        timeout=10.0,
    )
    response.raise_for_status()
    data = response.json()
    rate = float(data["Cur_OfficialRate"])
    client = redis.from_url(str(config.REDIS_URL))
    client.set("currency:usd", rate)
    return rate
