from celery import Celery

from app.core.config import config


celery_app = Celery(
    "realt_commission_bot",
    broker=str(config.REDIS_URL),
    backend=str(config.REDIS_URL),
    include=["app.tasks.currency"],
)

celery_app.conf.imports = ("app.tasks.currency",)

celery_app.conf.beat_schedule = {
    "update_usd_rate_every_4_hours": {
        "task": "app.tasks.currency.update_usd_rate",
        "schedule": 60 * 60 * 4,
    }
}

# Force task module import so worker/beat always register task strategies.
from app.tasks import currency as _currency_tasks  # noqa: F401,E402
