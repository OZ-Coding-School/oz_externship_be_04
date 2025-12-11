import asyncio
from typing import Any, Dict, List, cast

from celery import shared_task

from apps.lectures.crawler.inflearn.inflearn_crawler import InflearnCrawler
from apps.lectures.services.db_sync import SyncResult, sync_inflearn_db


def _sync_inflearn_task() -> int:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    crawler = InflearnCrawler()
    data: List[Dict[str, Any]] = loop.run_until_complete(crawler.get_all_courses())
    loop.close()

    result: SyncResult = sync_inflearn_db(data)
    return result["created_lectures"] + result["updated_lectures"]


sync_inflearn_task = cast(Any, shared_task(name="lectures.sync_inflearn_task")(_sync_inflearn_task))
