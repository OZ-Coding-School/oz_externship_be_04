from typing import Any

from celery import shared_task

from apps.lectures.tasks.crawl import sync_inflearn_task
from apps.lectures.tasks.embedding import build_all_lecture_embeddings
from apps.lectures.tasks.error_handlers import handle_crawl_failure


@shared_task(name="lectures.crawl_then_embed")  # type: ignore[misc]
def crawl_then_embed() -> Any:
    sync_inflearn_task.apply_async(link=build_all_lecture_embeddings.si(), link_error=handle_crawl_failure.s())
