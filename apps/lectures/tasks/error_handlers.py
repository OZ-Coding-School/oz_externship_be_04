from celery import shared_task
from celery.result import AsyncResult  # type: ignore[import-untyped]

from apps.core.logger.logging import get_logger

logger = get_logger(__name__)


@shared_task(name="lectures.handle_crawl_failure")  # type: ignore[misc]
def handle_crawl_failure(task_id: str) -> None:
    logger.error(f"크롤링 태스크 실패, task_id={task_id}")
    if not (traceback := AsyncResult(task_id).traceback):
        logger.error("traceback 정보를 가져올 수 없습니다.")
        return
    logger.error(f"실패한 태스크의 traceback:\n{traceback}")
