import os

from celery import Celery

broker_url = os.environ.get("REDIS_URL", "redis://redis:6379/0")

app = Celery("oligospace_bioinfo", broker=broker_url, backend=broker_url)
app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=86400,
    timezone="UTC",
    enable_utc=True,
)
app.autodiscover_tasks(["oligospace_bioinfo"])
