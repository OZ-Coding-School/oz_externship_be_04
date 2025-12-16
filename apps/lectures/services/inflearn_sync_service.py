from typing import Any, Dict, List

from asgiref.sync import sync_to_async

from apps.lectures.crawler.inflearn.inflearn_crawler import InflearnCrawler
from apps.lectures.services.db_sync import SyncResult, sync_inflearn_db


async def run_inflearn_sync() -> int:
    crawler = InflearnCrawler()

    data: List[Dict[str, Any]] = await crawler.get_all_courses()

    result: SyncResult = await sync_to_async(
        sync_inflearn_db,
        thread_sensitive=True,
    )(data)

    return result["created_lectures"] + result["updated_lectures"]
