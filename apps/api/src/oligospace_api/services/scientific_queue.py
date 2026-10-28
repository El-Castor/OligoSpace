from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from celery import Celery

from oligospace_api.core.config import get_settings


class ScientificQueue(Protocol):
    def dispatch(self, job_id: str, claim_token: str) -> str: ...


@dataclass
class CeleryScientificQueue:
    app: Celery

    def dispatch(self, job_id: str, claim_token: str) -> str:
        result = self.app.send_task("oligospace.scientific_job", args=[job_id, claim_token])
        return str(result.id)


def get_scientific_queue() -> ScientificQueue:
    settings = get_settings()
    app = Celery("oligospace_api", broker=settings.redis_url, backend=settings.redis_url)
    return CeleryScientificQueue(app)
