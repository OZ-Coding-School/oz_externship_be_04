from typing import Any

from celery import chain, shared_task

from apps.lectures.tasks.crawl import sync_inflearn_task
from apps.lectures.tasks.embedding import build_all_lecture_embeddings


@shared_task(name="lectures.crawl_then_embed")  # type: ignore[misc]
def crawl_then_embed() -> Any:
    return chain(
        sync_inflearn_task.s(),
        build_all_lecture_embeddings.s(),
    )()
