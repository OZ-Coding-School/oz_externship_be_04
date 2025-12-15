import asyncio
from typing import Any
from celery import shared_task

from apps.lectures.services.inflearn_sync_service import run_inflearn_sync


@shared_task(  # type: ignore[misc]
    bind=True,
    name="lectures.sync_inflearn_task",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 30},
    retry_backoff=True,
    retry_jitter=True,
)
def sync_inflearn_task(self: Any) -> int:
    return asyncio.run(run_inflearn_sync())
