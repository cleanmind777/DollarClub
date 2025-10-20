from celery import Celery
from ..core.config import settings

celery_app = Celery(
    "dollarclub",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.script_execution"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.MAX_EXECUTION_TIME,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)
